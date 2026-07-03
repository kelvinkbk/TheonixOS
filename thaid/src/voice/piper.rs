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
            tracing::warn!(
                "Piper voice model not found at {}. Falling back to mock TTS.",
                self.voice_model_path.display()
            );
            // Wait 2 seconds to simulate processing time
            tokio::time::sleep(std::time::Duration::from_secs(2)).await;
            // Write a tiny valid 44-byte WAV header so `aplay` in Python doesn't crash
            let dummy_wav: [u8; 44] = [
                0x52, 0x49, 0x46, 0x46, 0x24, 0x00, 0x00, 0x00, 0x57, 0x41, 0x56, 0x45, 0x66, 0x6d, 0x74, 0x20,
                0x10, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x80, 0x3e, 0x00, 0x00, 0x00, 0x7d, 0x00, 0x00,
                0x02, 0x00, 0x10, 0x00, 0x64, 0x61, 0x74, 0x61, 0x00, 0x00, 0x00, 0x00,
            ];
            tokio::fs::write(output_path, &dummy_wav).await?;
            return Ok(());
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
