// =============================================================================
// thaid — Configuration
// =============================================================================

use anyhow::{Context, Result};
use serde::Deserialize;
use std::path::PathBuf;

/// Main configuration structure for thaid.
/// Loaded from `$XDG_CONFIG_HOME/theonix/thaid.toml` or `/etc/theonix/thaid.toml`.
#[derive(Debug, Clone, Deserialize)]
#[serde(default)]
pub struct ThaidConfig {
    /// Base URL of the local Ollama instance
    pub ollama_url: String,

    /// Default model to load when a query arrives
    pub default_model: String,

    /// Seconds of inactivity before unloading the model (saves RAM)
    pub idle_timeout_secs: u64,

    /// Path to the SQLite database for conversation memory
    pub memory_db_path: PathBuf,

    /// Maximum number of conversation turns to retain in memory
    pub memory_max_turns: usize,

    /// Whisper model size: tiny | base | small | medium | large
    pub whisper_model: String,

    /// Piper voice model path
    pub piper_voice_path: PathBuf,

    /// Permission tier granted to the AI by default
    /// 0 = read-only, 1 = suggest, 2 = execute-approved, 3 = admin
    pub default_permission_tier: u8,

    /// Enable telemetry (always opt-in, default off)
    pub telemetry_enabled: bool,
}

impl Default for ThaidConfig {
    fn default() -> Self {
        let data_dir = dirs_next::data_local_dir()
            .unwrap_or_else(|| PathBuf::from("/tmp"))
            .join("theonix")
            .join("ai");

        Self {
            ollama_url: "http://127.0.0.1:11434".to_string(),
            default_model: "llama3:8b".to_string(),
            idle_timeout_secs: 600, // 10 minutes
            memory_db_path: data_dir.join("memory.db"),
            memory_max_turns: 100,
            whisper_model: "base".to_string(),
            piper_voice_path: PathBuf::from(
                "/usr/share/theonix/models/piper/en_US-lessac-medium.onnx",
            ),
            default_permission_tier: 1, // suggest-only by default
            telemetry_enabled: false,
        }
    }
}

impl ThaidConfig {
    /// Load configuration from the first available file:
    ///   1. $XDG_CONFIG_HOME/theonix/thaid.toml  (user override)
    ///   2. /etc/theonix/thaid.toml              (system-wide default)
    ///   3. Built-in defaults                     (no file found)
    pub fn load() -> Result<Self> {
        // 1. User config
        if let Some(config_dir) = dirs_next::config_dir() {
            let user_config = config_dir.join("theonix").join("thaid.toml");
            if user_config.exists() {
                tracing::debug!("Loading user config: {}", user_config.display());
                return Self::from_file(&user_config);
            }
        }

        // 2. System config
        let system_config = PathBuf::from("/etc/theonix/thaid.toml");
        if system_config.exists() {
            tracing::debug!("Loading system config: {}", system_config.display());
            return Self::from_file(&system_config);
        }

        // 3. Defaults
        tracing::debug!("No config file found — using built-in defaults");
        Ok(Self::default())
    }

    fn from_file(path: &PathBuf) -> Result<Self> {
        let content = std::fs::read_to_string(path)
            .with_context(|| format!("Cannot read config file: {}", path.display()))?;
        toml::from_str(&content)
            .with_context(|| format!("Invalid TOML in config file: {}", path.display()))
    }
}
