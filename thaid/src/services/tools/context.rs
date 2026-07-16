use serde_json::{json, Value};
use tokio::process::Command;

pub fn get_context_tools() -> Vec<Value> {
    vec![json!({
        "type": "function",
        "function": {
            "name": "get_active_window",
            "description": "Get the title and class of the currently active/focused window on the desktop to understand what the user is looking at.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    })]
}

pub async fn execute_context_tool(name: &str, _args: &Value) -> Option<String> {
    match name {
        "get_active_window" => {
            // Using qdbus to query KWin for the active window class and title
            let output = Command::new("bash")
                .arg("-c")
                .arg("qdbus org.kde.KWin /KWin supportInformation | grep -A 5 'Active Window'")
                .output()
                .await;

            match output {
                Ok(out) => {
                    let info = String::from_utf8_lossy(&out.stdout).to_string();
                    if info.trim().is_empty() {
                        Some(
                            "Could not determine the active window (KWin query empty).".to_string(),
                        )
                    } else {
                        Some(format!("Active Window Info:\n{}", info))
                    }
                }
                Err(_) => Some("Failed to query the active window.".to_string()),
            }
        }
        _ => None,
    }
}
