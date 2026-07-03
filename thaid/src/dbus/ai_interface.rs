// =============================================================================
// thaid — D-Bus Interface: org.theonix.AI
// =============================================================================

use crate::{config::ThaidConfig, memory::ConversationStore, models::ModelManager};
use crate::voice::{whisper::WhisperTranscriber, piper::PiperTts};
use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{error, info, warn};
use uuid::Uuid;
use zbus::interface;

/// Implements the org.theonix.AI D-Bus interface.
/// This is the primary interface for all AI operations.
pub struct AIInterface {
    config: ThaidConfig,
    model_manager: Arc<ModelManager>,
    memory: Arc<RwLock<ConversationStore>>,
    whisper: WhisperTranscriber,
    piper: PiperTts,
}

impl AIInterface {
    pub fn new(
        config: ThaidConfig,
        model_manager: Arc<ModelManager>,
        memory: ConversationStore,
    ) -> Self {
        let whisper = WhisperTranscriber::new(config.whisper_model.clone());
        let piper = PiperTts::new(config.piper_voice_path.clone());
        
        Self {
            config,
            model_manager,
            memory: Arc::new(RwLock::new(memory)),
            whisper,
            piper,
        }
    }
}

#[interface(name = "org.theonix.AI")]
impl AIInterface {
    /// Send a text prompt and receive the full response synchronously.
    ///
    /// Parameters:
    ///   prompt:  The user's text input
    ///   options: Optional map of key-value options:
    ///              "model"   — override the default model
    ///              "session" — session ID for memory continuity
    ///
    /// Returns: The AI's response text
    async fn query(
        &self,
        prompt: String,
        options: HashMap<String, zbus::zvariant::OwnedValue>,
    ) -> zbus::fdo::Result<String> {
        if prompt.trim().is_empty() {
            return Err(zbus::fdo::Error::InvalidArgs(
                "Prompt cannot be empty".into(),
            ));
        }

        info!(prompt_len = prompt.len(), "Query received");

        // Extract optional model override
        let model_override: Option<String> = options
            .get("model")
            .and_then(|v| <&str>::try_from(v).ok())
            .map(|s| s.to_string());

        // Retrieve session context for memory continuity
        let session_id: Option<String> = options
            .get("session")
            .and_then(|v| <&str>::try_from(v).ok())
            .map(|s| s.to_string());

        // Build prompt with conversation history if session provided
        let full_prompt = if let Some(ref sid) = session_id {
            let memory = self.memory.read().await;
            match memory.build_context_prompt(sid, &prompt).await {
                Ok(ctx_prompt) => ctx_prompt,
                Err(e) => {
                    warn!(error = %e, "Failed to load conversation history — using bare prompt");
                    prompt.clone()
                }
            }
        } else {
            prompt.clone()
        };

        // Send to model manager (loads model lazily)
        let response = self
            .model_manager
            .query(&full_prompt, model_override.as_deref())
            .await
            .map_err(|e| {
                error!(error = %e, "Model query failed");
                zbus::fdo::Error::Failed(format!("AI query failed: {e}"))
            })?;

        // Persist to conversation memory if session provided
        if let Some(sid) = session_id {
            let mut memory = self.memory.write().await;
            if let Err(e) = memory.append_turn(&sid, &prompt, &response).await {
                warn!(error = %e, "Failed to save conversation turn to memory");
            } else if let Err(e) = memory
                .enforce_limits(&sid, self.config.memory_max_turns)
                .await
            {
                warn!(error = %e, "Failed to enforce conversation memory limits");
            }
        }

        info!(response_len = response.len(), "Query completed");
        Ok(response)
    }

    /// Get the current daemon status.
    ///
    /// Returns a dict with:
    ///   "model_state"  — "unloaded" | "loading" | "ready"
    ///   "model_name"   — current model name (or empty string)
    ///   "version"      — thaid version string
    async fn get_status(&self) -> zbus::fdo::Result<HashMap<String, String>> {
        let state = self.model_manager.get_state().await;

        let (state_str, model_name) = match &state {
            crate::models::ModelState::Unloaded => ("unloaded".to_string(), String::new()),
            crate::models::ModelState::Loading => ("loading".to_string(), String::new()),
            crate::models::ModelState::Ready { name } => ("ready".to_string(), name.clone()),
        };

        let mut status = HashMap::new();
        status.insert("model_state".to_string(), state_str);
        status.insert("model_name".to_string(), model_name);
        status.insert("version".to_string(), env!("CARGO_PKG_VERSION").to_string());
        status.insert(
            "default_model".to_string(),
            self.config.default_model.clone(),
        );

        Ok(status)
    }

    /// Create a new conversation session. Returns a session ID.
    async fn new_session(&self) -> zbus::fdo::Result<String> {
        let session_id = Uuid::new_v4().to_string();
        let mut memory = self.memory.write().await;
        memory
            .create_session(&session_id)
            .await
            .map_err(|e| zbus::fdo::Error::Failed(format!("Failed to create session: {e}")))?;
        info!(session_id = %session_id, "New AI session created");
        Ok(session_id)
    }

    /// Delete a conversation session and all its history.
    async fn delete_session(&self, session_id: String) -> zbus::fdo::Result<()> {
        let mut memory = self.memory.write().await;
        memory
            .delete_session(&session_id)
            .await
            .map_err(|e| zbus::fdo::Error::Failed(format!("Failed to delete session: {e}")))?;
        info!(session_id = %session_id, "Session deleted");
        Ok(())
    }

    /// List available Ollama models.
    async fn list_models(&self) -> zbus::fdo::Result<Vec<String>> {
        // Query Ollama for available models
        let client = reqwest::Client::new();
        let response = client
            .get(format!("{}/api/tags", self.config.ollama_url))
            .send()
            .await
            .map_err(|e| zbus::fdo::Error::Failed(format!("Cannot reach Ollama: {e}")))?
            .json::<serde_json::Value>()
            .await
            .map_err(|e| zbus::fdo::Error::Failed(format!("Cannot parse Ollama response: {e}")))?;

        let models = response["models"]
            .as_array()
            .unwrap_or(&vec![])
            .iter()
            .filter_map(|m| m["name"].as_str().map(str::to_string))
            .collect();

        Ok(models)
    }

    /// Unload the current model immediately (frees RAM without waiting for idle timeout).
    async fn unload_model(&self) -> zbus::fdo::Result<()> {
        self.model_manager.unload().await;
        Ok(())
    }

    /// Transcribe a WAV audio file to text.
    ///
    /// Parameters:
    ///   audio_path: Absolute path to the WAV file to transcribe.
    ///
    /// Returns: The transcribed text.
    async fn transcribe(&self, audio_path: String) -> zbus::fdo::Result<String> {
        let path = PathBuf::from(&audio_path);
        if !path.exists() {
            return Err(zbus::fdo::Error::InvalidArgs(format!("Audio file not found: {}", audio_path)));
        }
        
        self.whisper.transcribe(&path).await.map_err(|e| {
            zbus::fdo::Error::Failed(format!("Transcription failed: {e}"))
        })
    }

    /// Synthesize speech from text and save to a WAV file.
    ///
    /// Parameters:
    ///   text: The text to speak.
    ///   output_path: Absolute path to save the generated WAV file.
    ///
    /// Returns: Result<()>
    async fn synthesize(&self, text: String, output_path: String) -> zbus::fdo::Result<()> {
        let path = PathBuf::from(&output_path);
        self.piper.synthesize(&text, &path).await.map_err(|e| {
            zbus::fdo::Error::Failed(format!("TTS failed: {e}"))
        })
    }
}
