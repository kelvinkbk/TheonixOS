pub mod automation;
pub mod context;
pub mod intent;
pub mod memory;
pub mod network;
pub mod settings;
pub mod system;
pub mod vision;
pub mod plugin_manager;
pub mod desktop;

use crate::services::memory::ConversationStore;
use crate::services::permissions::PermissionManager;
use serde_json::Value;
use std::sync::Arc;
use tokio::sync::RwLock;
use std::time::Instant;

use std::collections::HashMap;

pub trait Tool: Send + Sync {
    fn name(&self) -> &str;
    fn description(&self) -> &str;
    fn schema(&self) -> Value;
    fn execute<'a>(&'a self, args: &'a Value) -> std::pin::Pin<Box<dyn std::future::Future<Output = Option<String>> + Send + 'a>>;
}

pub trait Plugin: Send + Sync {
    fn name(&self) -> &str;
    fn version(&self) -> &str;
    fn initialize(&self) -> Result<(), String>;
    fn tools(&self) -> Vec<Arc<dyn Tool>>;
    fn unload(&self) -> Result<(), String>;
}

pub struct ToolExecutor {
    permission_manager: Arc<RwLock<PermissionManager>>,
    registry: HashMap<String, Arc<dyn Tool>>,
}

impl ToolExecutor {
    pub fn new(permission_manager: Arc<RwLock<PermissionManager>>) -> Self {
        Self { 
            permission_manager,
            registry: HashMap::new(),
        }
    }

    pub fn register_tool(&mut self, tool: Arc<dyn Tool>) {
        self.registry.insert(tool.name().to_string(), tool);
    }

    pub fn get_all_tools(&self) -> Vec<Value> {
        let mut tools = Vec::new();
        // Return trait-based tools
        for tool in self.registry.values() {
            tools.push(tool.schema());
        }
        
        // Legacy fallback (Will be removed once all migrated to traits)
        tools.extend(system::get_system_tools());
        tools.extend(context::get_context_tools());
        tools.extend(memory::get_memory_tools());
        tools.extend(vision::get_vision_tools());
        tools.extend(intent::get_intent_tools());
        tools.extend(settings::get_settings_tools());
        tools.extend(network::get_network_tools());
        tools.extend(automation::get_automation_tools());
        tools
    }

    pub async fn execute_tool(
        &self,
        name: &str,
        args: &Value,
        mem: &Arc<RwLock<ConversationStore>>,
    ) -> Option<String> {
        let start_time = Instant::now();
        let mut status = "allowed";

        // Intercept via PermissionManager
        {
            let pm = self.permission_manager.read().await;
            if !pm.is_allowed(name) {
                // Check if a valid token was provided
                let token_valid = if let Some(token) = args.get("approval_token").and_then(|v| v.as_str()) {
                    pm.consume_token(token, name).await
                } else {
                    false
                };

                if !token_valid {
                    let new_token = pm.request_token(name).await;
                    let entry = crate::services::permissions::AuditEntry {
                        timestamp: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default().as_secs(),
                        request_id: uuid::Uuid::new_v4().to_string(),
                        session_id: None,
                        user: std::env::var("USER").unwrap_or_else(|_| "unknown".to_string()),
                        plugin: "core".to_string(),
                        model: "unknown".to_string(),
                        tool: name.to_string(),
                        tool_version: "1.0.0".to_string(),
                        args: args.clone(),
                        status: "denied".to_string(),
                        success: false,
                        error: Some("Valid approval_token required".to_string()),
                        duration_ms: start_time.elapsed().as_millis() as u64,
                    };
                    pm.audit_log(entry);
                    return Some(format!("Permission Denied: This action requires user confirmation. Ask the user for permission. If they approve, call this tool again with the argument 'approval_token' set to '{}'", new_token));
                }
            }
        }

        // Execute tool via registry first
        let result = if let Some(tool) = self.registry.get(name) {
            tool.execute(args).await
        } else {
            // Legacy fallback
            if let Some(res) = system::execute_system_tool(name, args).await {
                Some(res)
            } else if let Some(res) = context::execute_context_tool(name, args).await {
                Some(res)
            } else if let Some(res) = memory::execute_memory_tool(name, args, mem).await {
                Some(res)
            } else if let Some(res) = vision::execute_vision_tool(name, args).await {
                Some(res)
            } else if let Some(res) = intent::execute_intent_tool(name, args).await {
                Some(res)
            } else if let Some(res) = settings::execute_settings_tool(name, args).await {
                Some(res)
            } else if let Some(res) = network::execute_network_tool(name, args).await {
                Some(res)
            } else if let Some(res) = automation::execute_automation_tool(name, args).await {
                Some(res)
            } else {
                status = "failed";
                None
            }
        };

        let pm = self.permission_manager.read().await;
        let entry = crate::services::permissions::AuditEntry {
            timestamp: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default().as_secs(),
            request_id: uuid::Uuid::new_v4().to_string(),
            session_id: None,
            user: std::env::var("USER").unwrap_or_else(|_| "unknown".to_string()),
            plugin: "core".to_string(),
            model: "unknown".to_string(),
            tool: name.to_string(),
            tool_version: "1.0.0".to_string(),
            args: args.clone(),
            status: status.to_string(),
            success: status == "allowed",
            error: if status == "failed" { Some("Execution failed".to_string()) } else { None },
            duration_ms: start_time.elapsed().as_millis() as u64,
        };
        pm.audit_log(entry);

        result
    }
}
