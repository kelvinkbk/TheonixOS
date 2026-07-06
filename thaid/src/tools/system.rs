use serde_json::{json, Value};
use tokio::process::Command;

pub fn get_system_tools() -> Vec<Value> {
    vec![
        json!({
            "type": "function",
            "function": {
                "name": "get_system_info",
                "description": "Get the current system health including CPU usage, RAM, and temperatures.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }),
        json!({
            "type": "function",
            "function": {
                "name": "run_os_command",
                "description": "Execute a bash shell command on the user's OS to control the system (e.g. adjust volume, open applications, lock screen, shutdown).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash shell command to execute."
                        }
                    },
                    "required": ["command"]
                }
            }
        }),
    ]
}

pub async fn execute_system_tool(name: &str, args: &Value) -> Option<String> {
    match name {
        "get_system_info" => {
            // A simple implementation for getting system info via top and free
            let output = Command::new("bash")
                .arg("-c")
                .arg("echo 'CPU & Memory Info:'; top -b -n 1 | head -n 5; echo ''; free -m")
                .output()
                .await;

            match output {
                Ok(out) => Some(String::from_utf8_lossy(&out.stdout).to_string()),
                Err(e) => Some(format!("Failed to get system info: {}", e)),
            }
        }
        "run_os_command" => {
            if let Some(command) = args.get("command").and_then(|v| v.as_str()) {
                let output = Command::new("bash").arg("-c").arg(command).output().await;

                match output {
                    Ok(out) => {
                        let stdout = String::from_utf8_lossy(&out.stdout);
                        let stderr = String::from_utf8_lossy(&out.stderr);
                        
                        if out.status.success() {
                            Some(format!("Success.\n{stdout}"))
                        } else {
                            Some(format!(
                                "Failed (code {}).\n{stderr}",
                                out.status.code().unwrap_or(1)
                            ))
                        }
                    }
                    Err(e) => Some(format!("Execution failed: {e}")),
                }
            } else {
                Some("Error: Missing command argument".to_string())
            }
        }
        _ => None,
    }
}
