// =============================================================================
// thaid — Piper Text-to-Speech
// =============================================================================

use anyhow::{Context, Result};
use std::path::PathBuf;
use tokio::process::Command;
use tracing::info;

pub struct PiperTts {
    voice_model_path: PathBuf,
}

impl PiperTts {
    pub fn new(voice_model_path: PathBuf) -> Self {
        Self { voice_model_path }
    }

    /// Convert text to speech and save to output_path (WAV).
    pub async fn synthesize(&self, text: &str, output_path: &PathBuf) -> Result<()> {
        if !self.voice_model_path.exists() {
            anyhow::bail!(
                "Piper voice model not found: {}",
                self.voice_model_path.display()
            );
        }

        info!(chars = text.len(), "Synthesizing speech");

        let output = Command::new("piper")
            .arg("--model")
            .arg(&self.voice_model_path)
            .arg("--output_file")
            .arg(output_path)
            .stdin(std::process::Stdio::piped())
            .output()
            .await
            .context("Failed to run piper — is piper-tts installed?")?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("piper failed: {stderr}");
        }

        Ok(())
    }
}
