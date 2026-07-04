// =============================================================================
// thaid — Whisper Voice Transcription
// =============================================================================
// Uses whisper.cpp (whisper-cli binary) for fully local transcription.
// No audio data leaves the device.

use anyhow::{Context, Result};
use std::path::PathBuf;
use tokio::process::Command;
use tokio::time::{timeout, Duration};
use tracing::{debug, info};

pub struct WhisperTranscriber {
    model_size: String,
}

impl WhisperTranscriber {
    pub fn new(model_size: String) -> Self {
        Self { model_size }
    }

    /// Transcribe an audio file to text. The audio_path must be a WAV file.
    /// Returns the transcribed text.
    pub async fn transcribe(&self, audio_path: &PathBuf) -> Result<String> {
        let model_path = format!(
            "/usr/share/theonix/models/whisper/ggml-{}.bin",
            self.model_size
        );

        if !std::path::Path::new(&model_path).exists() {
            anyhow::bail!("Whisper model not found at {model_path}");
        }

        info!(model = %self.model_size, path = %audio_path.display(), "Transcribing audio");

        let output = timeout(
            Duration::from_secs(120),
            Command::new("whisper-cli")
                .arg("--model")
                .arg(&model_path)
                .arg("--language")
                .arg("auto")
                .arg("--output-txt")
                .arg("--no-prints")
                .arg("-f")
                .arg(audio_path)
                .output(),
        )
        .await
        .context("whisper-cli timed out after 120s")?
        .context("Failed to run whisper-cli — is whisper-cpp installed?")?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("whisper-cli failed: {stderr}");
        }

        // whisper-cli writes output to <input>.wav.txt
        let txt_path = PathBuf::from(format!("{}.txt", audio_path.display()));
        let text = tokio::fs::read_to_string(&txt_path)
            .await
            .context("Failed to read whisper output")?;

        // Clean up temp text file
        let _ = tokio::fs::remove_file(&txt_path).await;

        let result = text.trim().to_string();
        debug!(chars = result.len(), "Transcription complete");
        Ok(result)
    }
}
