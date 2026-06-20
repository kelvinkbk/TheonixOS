// thaid — error types
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ThaidError {
    #[error("Model not available: {0}")]
    ModelNotAvailable(String),

    #[error("Ollama communication error: {0}")]
    OllamaError(String),

    #[error("Database error: {0}")]
    DatabaseError(#[from] rusqlite::Error),

    #[error("Configuration error: {0}")]
    ConfigError(String),

    #[error("Permission denied: {0}")]
    PermissionDenied(String),

    #[error("Voice processing error: {0}")]
    VoiceError(String),

    #[error("I/O error: {0}")]
    IoError(#[from] std::io::Error),
}
