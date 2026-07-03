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
            anyhow::bail!("Piper voice model not found at {}", self.voice_model_path.display());
        }

        info!(chars = text.len(), "Synthesizing speech");

        let mut child = Command::new("piper")
            .arg("--model")
            .arg(&self.voice_model_path)
            .arg("--output_file")
            .arg(output_path)
            .stdin(std::process::Stdio::piped())
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped())
            .spawn()
            .context("Failed to spawn piper — is piper-tts installed?")?;

        // Write the text to Piper's standard input
        if let Some(mut stdin) = child.stdin.take() {
            use tokio::io::AsyncWriteExt;
            stdin.write_all(text.as_bytes()).await?;
        }

        let output = child.wait_with_output().await?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("piper failed: {stderr}");
        }

        Ok(())
    }
}
