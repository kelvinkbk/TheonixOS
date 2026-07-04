pub mod system;
pub mod context;
pub mod memory;
pub mod vision;
pub mod intent;

use serde_json::Value;
use std::sync::Arc;
use tokio::sync::RwLock;
use crate::memory::ConversationStore;

pub fn get_all_tools() -> Vec<Value> {
    let mut tools = Vec::new();
    tools.extend(system::get_system_tools());
    tools.extend(context::get_context_tools());
    tools.extend(memory::get_memory_tools());
    tools.extend(vision::get_vision_tools());
    tools.extend(intent::get_intent_tools());
    tools
}

pub async fn execute_tool(name: &str, args: &Value, mem: &Arc<RwLock<ConversationStore>>) -> Option<String> {
    if let Some(res) = system::execute_system_tool(name, args).await {
        return Some(res);
    }
    if let Some(res) = context::execute_context_tool(name, args).await {
        return Some(res);
    }
    if let Some(res) = memory::execute_memory_tool(name, args, mem).await {
        return Some(res);
    }
    if let Some(res) = vision::execute_vision_tool(name, args).await {
        return Some(res);
    }
    if let Some(res) = intent::execute_intent_tool(name, args).await {
        return Some(res);
    }
    None
}
