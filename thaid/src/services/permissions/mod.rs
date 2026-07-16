use std::fs::OpenOptions;
use std::io::Write;
use std::sync::{Arc, RwLock};
use serde_json::json;

/// Permission tiers for AI operations
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum PermissionTier {
    ReadOnly = 0,
    Suggest = 1,
    Execute = 2,
    Admin = 3,
}

use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize, Clone)]
pub struct PermissionPolicy {
    pub allow: Vec<String>,
    pub confirm: Vec<String>,
    pub deny: Vec<String>,
}

use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

pub struct PermissionConfig {
    pub log_dir: String,
    pub policy: PermissionPolicy,
}

pub struct ApprovalToken {
    pub uuid: String,
    pub tool_name: String,
    pub expires_at: u64,
}

pub struct PermissionCache {
    pub active_tokens: HashMap<String, ApprovalToken>,
}

pub struct PermissionManager {
    pub config: PermissionConfig,
    pub cache: tokio::sync::RwLock<PermissionCache>,
}

#[derive(serde::Serialize)]
pub struct AuditEntry {
    pub timestamp: u64,
    pub request_id: String,
    pub session_id: Option<String>,
    pub user: String,
    pub plugin: String,
    pub model: String,
    pub tool: String,
    pub tool_version: String,
    pub args: serde_json::Value,
    pub status: String,
    pub success: bool,
    pub error: Option<String>,
    pub duration_ms: u64,
}

impl PermissionManager {
    pub fn new() -> Self {
        let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
        let log_dir = format!("{}/.local/share/thaid", home);
        let _ = std::fs::create_dir_all(&log_dir);

        let default_policy = PermissionPolicy {
            allow: vec!["set_volume".into(), "set_brightness".into(), "launch_app".into(), "get_system_info".into()],
            confirm: vec!["run_os_command".into(), "delete".into(), "network".into()],
            deny: vec!["shutdown".into()],
        };

        let policy = if let Ok(data) = std::fs::read_to_string("/etc/theonix/permissions.json") {
            serde_json::from_str(&data).unwrap_or(default_policy)
        } else {
            default_policy
        };

        Self {
            config: PermissionConfig { log_dir, policy },
            cache: tokio::sync::RwLock::new(PermissionCache { active_tokens: HashMap::new() }),
        }
    }

    /// Generate a 5-minute cryptographic token for a specific tool
    pub async fn request_token(&self, tool_name: &str) -> String {
        let uuid = uuid::Uuid::new_v4().to_string();
        let expires_at = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs() + 300; // 5 minutes
        
        let token = ApprovalToken {
            uuid: uuid.clone(),
            tool_name: tool_name.to_string(),
            expires_at,
        };

        let mut cache = self.cache.write().await;
        cache.active_tokens.insert(uuid.clone(), token);
        uuid
    }

    /// Validate and consume a token
    pub async fn consume_token(&self, uuid: &str, tool_name: &str) -> bool {
        let mut cache = self.cache.write().await;
        if let Some(token) = cache.active_tokens.get(uuid) {
            let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs();
            if token.expires_at > now && token.tool_name == tool_name {
                cache.active_tokens.remove(uuid);
                return true;
            }
        }
        false
    }

    /// Logs any executed system action to an audit log file in JSON format
    pub fn audit_log(&self, entry: AuditEntry) {
        let log_path = format!("{}/audit.log", self.config.log_dir);
        
        let log_json = json!(entry);

        if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(log_path) {
            let mut log_line = log_json.to_string();
            log_line.push('\n');
            let _ = file.write_all(log_line.as_bytes());
        }
    }
    
    /// Checks if a tool is allowed to run without explicit user confirmation
    pub fn is_allowed(&self, tool_name: &str) -> bool {
        if self.config.policy.deny.contains(&tool_name.to_string()) {
            return false;
        }
        if self.config.policy.confirm.contains(&tool_name.to_string()) {
            return false; // requires token
        }
        if self.config.policy.allow.contains(&tool_name.to_string()) {
            return true;
        }
        // Default deny for unknown tools
        false
    }
}
