// =============================================================================
// thaid — Model Manager (lazy loading + idle unload)
// =============================================================================

use anyhow::{Context, Result};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::RwLock;
use tracing::{debug, info, warn};
use crate::memory::ConversationStore;
use crate::tools;

/// Tracks the current state of a loaded model.
#[derive(Debug, Clone, PartialEq)]
pub enum ModelState {
    /// No model is loaded. Memory footprint: ~0 MB.
    Unloaded,
    /// Model is being pulled/loaded into Ollama.
    Loading,
    /// Model is loaded and ready to serve queries.
    Ready { name: String },
}

/// Manages the Ollama model lifecycle: lazy loading and idle unloading.
/// All public methods are async and safe to call from concurrent tasks.
pub struct ModelManager {
    ollama_url: String,
    default_model: String,
    idle_timeout: Duration,
    state: Arc<RwLock<ModelState>>,
    last_used: Arc<RwLock<Option<Instant>>>,
    http: Client,
}

impl ModelManager {
    pub fn new(ollama_url: String, default_model: String, idle_timeout: Duration) -> Self {
        Self {
            ollama_url,
            default_model,
            idle_timeout,
            state: Arc::new(RwLock::new(ModelState::Unloaded)),
            last_used: Arc::new(RwLock::new(None)),
            http: Client::builder()
                .timeout(Duration::from_secs(300)) // long timeout for model pulls
                .build()
                .expect("Failed to build HTTP client"),
        }
    }

    /// Ensure a model is loaded, loading it lazily if needed.
    /// Returns the model name that is ready.
    pub async fn ensure_loaded(&self, requested_model: Option<&str>) -> Result<String> {
        let model_name = requested_model.unwrap_or(&self.default_model).to_string();

        // Fast path: already loaded
        {
            let state = self.state.read().await;
            if let ModelState::Ready { name } = &*state {
                if name == &model_name {
                    debug!(model = %model_name, "Model already loaded (fast path)");
                    self.update_last_used().await;
                    return Ok(name.clone());
                }
            }
        }

        // Need to load or switch model
        {
            let mut state = self.state.write().await;
            // Double-check under write lock
            if let ModelState::Ready { name } = &*state {
                if name == &model_name {
                    self.update_last_used().await;
                    return Ok(name.clone());
                }
            }

            info!(model = %model_name, "Loading AI model (lazy)...");
            *state = ModelState::Loading;
        }

        // Pull/load the model (this may take a while for large models)
        match self.ollama_pull(&model_name).await {
            Ok(()) => {
                info!(model = %model_name, "Model loaded successfully");
                let mut state = self.state.write().await;
                *state = ModelState::Ready {
                    name: model_name.clone(),
                };
                self.update_last_used().await;
                Ok(model_name)
            }
            Err(e) => {
                warn!(model = %model_name, error = %e, "Failed to load model");
                let mut state = self.state.write().await;
                *state = ModelState::Unloaded;
                Err(e)
            }
        }
    }

    /// Send a query to the loaded model, optionally executing tools, and return the final response.
    pub async fn chat(
        &self, 
        history: &[(String, String)], 
        prompt: &str, 
        model: Option<&str>, 
        memory: &Arc<RwLock<ConversationStore>>
    ) -> Result<String> {
        let model_name = self.ensure_loaded(model).await?;

        let mut messages = vec![
            serde_json::json!({
                "role": "system",
                "content": "You are THAID, the central AI nervous system for Theonix OS. Your personality is calm, highly intelligent, and extremely minimal. You speak only when useful. If you do not know something, you admit uncertainty immediately. Keep your answers extremely brief and direct. Never use markdown, bullet points, or long paragraphs because your output is spoken aloud via TTS. You have deep control over the operating system through tools. Do not offer platitudes or conversational filler."
            })
        ];

        for (role, content) in history {
            messages.push(serde_json::json!({
                "role": role,
                "content": content
            }));
        }

        messages.push(serde_json::json!({
            "role": "user",
            "content": prompt
        }));

        let tools = serde_json::Value::Array(crate::tools::get_all_tools());

        let payload = serde_json::json!({
            "model": model_name,
            "messages": messages,
            "tools": tools,
            "stream": false
        });

        // 1st request
        let resp = self.http.post(format!("{}/api/chat", self.ollama_url))
            .json(&payload)
            .send().await.context("Failed to send chat to Ollama")?
            .error_for_status().context("Ollama returned an error status")?
            .json::<serde_json::Value>().await.context("Failed to parse Ollama response")?;

        let message = resp["message"].clone();

        if let Some(tool_calls) = message["tool_calls"].as_array() {
            let mut tool_results = Vec::new();
            for tc in tool_calls {
                if let Some(func) = tc["function"].as_object() {
                    let name = func["name"].as_str().unwrap_or("");
                    if let Some(args) = func.get("arguments") {
                        info!(tool = %name, "Executing AI tool call");
                        if let Some(result_text) = crate::tools::execute_tool(name, args, memory).await {
                            tool_results.push(serde_json::json!({
                                "role": "tool",
                                "name": name,
                                "content": result_text
                            }));
                        } else {
                            tool_results.push(serde_json::json!({
                                "role": "tool",
                                "name": name,
                                "content": format!("Tool '{}' not found or failed.", name)
                            }));
                        }
                    }
                }
            }

            messages.push(message);
            for res in tool_results {
                messages.push(res);
            }

            let payload2 = serde_json::json!({
                "model": model_name,
                "messages": messages,
                "stream": false
            });

            let resp2 = self.http.post(format!("{}/api/chat", self.ollama_url))
                .json(&payload2)
                .send().await.context("Failed second chat request")?
                .error_for_status().context("Second request error status")?
                .json::<serde_json::Value>().await.context("Failed to parse second response")?;

            if let Some(final_text) = resp2["message"]["content"].as_str() {
                let trimmed = final_text.trim();
                if trimmed.is_empty() {
                    return Ok("I have executed the command, but I don't have anything else to add.".to_string());
                }
                return Ok(trimmed.to_string());
            }
        } else if let Some(content) = message["content"].as_str() {
            let trimmed = content.trim();
            if trimmed.is_empty() {
                return Ok("I am not sure how to respond to that.".to_string());
            }
            return Ok(trimmed.to_string());
        }

        Err(anyhow::anyhow!("Invalid response format from Ollama"))
    }

    /// Unload the current model, freeing RAM.
    pub async fn unload(&self) {
        let current_model = {
            let state = self.state.read().await;
            match &*state {
                ModelState::Ready { name } => Some(name.clone()),
                _ => None,
            }
        };

        if let Some(model) = current_model {
            info!(model = %model, "Unloading idle AI model");
            // Call Ollama API to evict the model from memory
            let _ = self
                .http
                .post(format!("{}/api/generate", self.ollama_url))
                .json(&serde_json::json!({
                    "model":     model,
                    "prompt":    "",
                    "keep_alive": 0  // 0 = unload immediately
                }))
                .send()
                .await;

            let mut state = self.state.write().await;
            *state = ModelState::Unloaded;
            info!("Model unloaded — RAM freed");
        }
    }

    /// Returns the current model state (for D-Bus status queries).
    pub async fn get_state(&self) -> ModelState {
        self.state.read().await.clone()
    }

    /// Background task: checks periodically for idle timeout and unloads.
    pub async fn run_idle_watcher(self: Arc<Self>) {
        let check_interval = Duration::from_secs(60); // check every minute
        loop {
            tokio::time::sleep(check_interval).await;

            let last = *self.last_used.read().await;
            if let Some(t) = last {
                if t.elapsed() >= self.idle_timeout {
                    self.unload().await;
                    // Reset last_used so we don't trigger again immediately
                    *self.last_used.write().await = None;
                }
            }
        }
    }

    // ---- Private helpers ---------------------------------------------------

    async fn update_last_used(&self) {
        *self.last_used.write().await = Some(Instant::now());
    }

    /// Pull a model from the Ollama model registry (or local cache).
    async fn ollama_pull(&self, model: &str) -> Result<()> {
        #[derive(Serialize)]
        struct PullRequest<'a> {
            model: &'a str,
            stream: bool,
        }

        self.http
            .post(format!("{}/api/pull", self.ollama_url))
            .json(&PullRequest {
                model,
                stream: false,
            })
            .send()
            .await
            .context("Pull request to Ollama failed")?
            .error_for_status()
            .context("Ollama pull returned error status")?;

        Ok(())
    }
}
