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
pub mod services;
pub use services::*;

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

    // ---- Initialize core systems --------------------------------------------
    let model_manager = std::sync::Arc::new(models::ModelManager::new(config.clone()));

    // Start the idle watcher — unloads model after inactivity
    let mgr_clone = model_manager.clone();
    tokio::spawn(async move {
        mgr_clone.run_idle_watcher().await;
    });

    let permission_manager = std::sync::Arc::new(tokio::sync::RwLock::new(
        crate::services::permissions::PermissionManager::new(),
    ));

    // Instantiate PluginManager early so it outlives ToolExecutor
    let mut plugin_manager = crate::services::tools::plugin_manager::PluginManager::new();

    let mut executor = crate::services::tools::ToolExecutor::new(permission_manager.clone());
    
    // Register migrated trait-based tools
    executor.register_tool(std::sync::Arc::new(crate::services::tools::system::GetSystemInfoTool));
    executor.register_tool(std::sync::Arc::new(crate::services::tools::system::SetVolumeTool));
    executor.register_tool(std::sync::Arc::new(crate::services::tools::system::LaunchAppTool));
    executor.register_tool(std::sync::Arc::new(crate::services::tools::system::RunOsCommandTool));
    
    // Register Phase 4 Desktop tools
    executor.register_tool(std::sync::Arc::new(crate::services::tools::desktop::ReadClipboardTool));
    executor.register_tool(std::sync::Arc::new(crate::services::tools::desktop::SendNotificationTool));
    executor.register_tool(std::sync::Arc::new(crate::services::tools::desktop::KRunnerSearchTool));

    // ---- Phase 5: Dynamic Plugin Loading ----
    match plugin_manager.load_all_plugins() {
        Ok(count) => {
            info!("Loaded {} dynamic plugins", count);
            for plugin in plugin_manager.get_plugins() {
                for tool in plugin.tools() {
                    info!("Registering dynamic tool: {}", tool.name());
                    executor.register_tool(tool);
                }
            }
        }
        Err(e) => tracing::error!("Failed to load dynamic plugins: {}", e),
    }

    let tool_executor = std::sync::Arc::new(executor);

    let memory_arc = std::sync::Arc::new(tokio::sync::RwLock::new(memory));
    
    let event_bus = std::sync::Arc::new(crate::services::event_bus::EventBus::new());
    
    let metrics = std::sync::Arc::new(crate::services::metrics::MetricsService::new());

    let container = crate::services::container::ServiceContainer::new(
        permission_manager,
        tool_executor,
        memory_arc.clone(),
        model_manager.clone(),
        event_bus,
        metrics,
    );

    let planner = crate::services::planner::Planner::new(container);

    // ---- D-Bus service registration ----------------------------------------
    let connection = zbus::connection::Builder::session()
        .context("Cannot connect to D-Bus session bus")?
        .name("org.theonix.AI")
        .context("Cannot acquire D-Bus name org.theonix.AI — another instance may be running")?
        .serve_at(
            "/org/theonix/AI",
            dbus::AIInterface::new(config.clone(), model_manager.clone(), memory_arc.clone(), planner),
        )
        .context("Failed to register D-Bus object")?
        .build()
        .await
        .context("Failed to build D-Bus connection")?;

    info!("thaid registered on D-Bus as org.theonix.AI at /org/theonix/AI");

    // ---- Ambient Intelligence Watcher (Phase 14) ----------------------------
    let iface_ref = connection
        .object_server()
        .interface::<_, dbus::AIInterface>("/org/theonix/AI")
        .await?;
    let signal_ctxt = iface_ref.signal_context().clone();

    tokio::spawn(async move {
        let mut interval = tokio::time::interval(std::time::Duration::from_secs(30));
        loop {
            interval.tick().await;
            // Watch for failed system services
            if let Ok(out) = tokio::process::Command::new("systemctl")
                .arg("--failed")
                .output()
                .await
            {
                let stdout = String::from_utf8_lossy(&out.stdout);
                if !stdout.contains("0 loaded units listed") {
                    if let Some(line) = stdout.lines().find(|l| l.contains("failed")) {
                        let parts: Vec<&str> = line.split_whitespace().collect();
                        if let Some(unit) = parts.first() {
                            let msg = format!("Ambient Alert: '{}' has crashed. Would you like me to investigate?", unit);
                            let _ =
                                dbus::AIInterface::ambient_notification(&signal_ctxt, &msg).await;
                        }
                    }
                }
            }
        }
    });

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
