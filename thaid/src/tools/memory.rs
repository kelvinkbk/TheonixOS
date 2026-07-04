use serde_json::{json, Value};
use crate::memory::ConversationStore;
use std::sync::Arc;
use tokio::sync::RwLock;

pub fn get_memory_tools() -> Vec<Value> {
    vec![
        json!({
            "type": "function",
            "function": {
                "name": "remember_fact",
                "description": "Save an important fact to your long-term memory (e.g. the user's name, favorite browser, preferred theme). You can use this to learn over time.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "A short, unique identifier for this fact (e.g. 'favorite_browser', 'user_name')."
                        },
                        "value": {
                            "type": "string",
                            "description": "The information to remember."
                        }
                    },
                    "required": ["key", "value"]
                }
            }
        })
    ]
}

pub async fn execute_memory_tool(name: &str, args: &Value, memory: &Arc<RwLock<ConversationStore>>) -> Option<String> {
    match name {
        "remember_fact" => {
            let key = args.get("key").and_then(|v| v.as_str());
            let value = args.get("value").and_then(|v| v.as_str());
            
            if let (Some(k), Some(v)) = (key, value) {
                let store = memory.read().await;
                match store.save_fact(k, v).await {
                    Ok(_) => Some(format!("Successfully remembered: {} = {}", k, v)),
                    Err(e) => Some(format!("Failed to save fact: {}", e)),
                }
            } else {
                Some("Error: Missing key or value".to_string())
            }
        },
        _ => None,
    }
}
