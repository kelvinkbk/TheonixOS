// =============================================================================
// thaid — Theonix AI Daemon
// Entry point
// =============================================================================
//
// thaid is a D-Bus session service that provides AI capabilities to the
// Theonix OS desktop. It manages Ollama model lifecycle (lazy loading),
// voice transcription (Whisper), text-to-speech (Piper), and stores
// conversation memory in SQLite.
//
// Architecture:
//   - Registered as a D-Bus session service (org.theonix.AI)
//   - Started on-demand via D-Bus activation (NOT at boot)
//   - Models loaded lazily on first query, unloaded after idle timeout
//   - All AI processing is local — no data leaves the device

#![allow(dead_code)]

use anyhow::{Context, Result};
use tracing::info;
use tracing_subscriber::{fmt, layer::SubscriberExt, util::SubscriberInitExt, EnvFilter};

mod config;
mod dbus;
mod error;
mod hardware;
mod memory;
mod models;
mod permissions;
mod voice;

#[tokio::main]
async fn main() -> Result<()> {
    // ---- Logging setup -----------------------------------------------------
    // Use journald when running under systemd, otherwise pretty-print to stderr
    let use_journald =
        std::env::var("JOURNAL_STREAM").is_ok() || std::env::var("INVOCATION_ID").is_ok();

    if use_journald {
        // Log to systemd journal with structured fields
        let journald_layer = tracing_journald::layer().context("Failed to connect to journald")?;
        tracing_subscriber::registry()
            .with(
                EnvFilter::from_default_env()
                    .add_directive("thaid=info".parse().expect("valid directive")),
            )
            .with(journald_layer)
            .init();
    } else {
        // Pretty-print for development / interactive use
        tracing_subscriber::registry()
            .with(
                EnvFilter::from_default_env()
                    .add_directive("thaid=debug".parse().expect("valid directive")),
            )
            .with(fmt::layer().with_target(false))
            .init();
    }

    info!(
        version = env!("CARGO_PKG_VERSION"),
        "Starting thaid — Theonix AI Daemon"
    );

    // ---- Configuration -----------------------------------------------------
    let config = config::ThaidConfig::load().context("Failed to load thaid configuration")?;

    info!(
        ollama_url = %config.ollama_url,
        default_model = %config.default_model,
        idle_timeout_secs = config.idle_timeout_secs,
        "Configuration loaded"
    );

    // ---- Hardware detection (determines GPU backend for Ollama) -----------
    let hw_info = hardware::HardwareInfo::detect();
    info!(
        gpu_backend = %hw_info.gpu_backend,
        total_ram_mb = hw_info.total_ram_mb,
        "Hardware detected"
    );

    // ---- Conversation memory (SQLite) -------------------------------------
    let memory = memory::ConversationStore::open(&config.memory_db_path)
        .await
        .context("Failed to open conversation memory database")?;

    // ---- Model manager (lazy loading) -------------------------------------
    let model_manager = std::sync::Arc::new(models::ModelManager::new(
        config.ollama_url.clone(),
        config.default_model.clone(),
        std::time::Duration::from_secs(config.idle_timeout_secs),
    ));

    // Start the idle watcher — unloads model after inactivity
    let mgr_clone = model_manager.clone();
    tokio::spawn(async move {
        mgr_clone.run_idle_watcher().await;
    });

    // ---- D-Bus service registration ----------------------------------------
    let connection = zbus::connection::Builder::session()
        .context("Cannot connect to D-Bus session bus")?
        .name("org.theonix.AI")
        .context("Cannot acquire D-Bus name org.theonix.AI — another instance may be running")?
        .serve_at(
            "/org/theonix/AI",
            dbus::AIInterface::new(config.clone(), model_manager.clone(), memory),
        )
        .context("Failed to register D-Bus object")?
        .build()
        .await
        .context("Failed to build D-Bus connection")?;

    info!("thaid registered on D-Bus as org.theonix.AI at /org/theonix/AI");

    // ---- Signal handling (graceful shutdown) --------------------------------
    tokio::select! {
        _ = tokio::signal::ctrl_c() => {
            info!("Received SIGINT — shutting down");
        }
        _ = async {
            // Also handle SIGTERM from systemd
            let mut sigterm = tokio::signal::unix::signal(
                tokio::signal::unix::SignalKind::terminate()
            ).expect("SIGTERM handler");
            sigterm.recv().await
        } => {
            info!("Received SIGTERM — shutting down");
        }
    }

    // Explicit drop to clean up D-Bus connection before exit
    drop(connection);
    info!("thaid stopped");
    Ok(())
}
