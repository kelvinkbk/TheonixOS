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
            let mut command_to_run = None;
            if let Some(cmd) = args.get("command").and_then(|v| v.as_str()) {
                command_to_run = Some(cmd.to_string());
            } else if let Some(cmd) = args.get("cmd").and_then(|v| v.as_str()) {
                command_to_run = Some(cmd.to_string());
            } else if let Some(cmd) = args.get("script").and_then(|v| v.as_str()) {
                command_to_run = Some(cmd.to_string());
            } else if let Some(cmd) = args.as_str() {
                command_to_run = Some(cmd.to_string());
            } else if let Some(obj) = args.as_object() {
                // If the LLM dumped it in some other key
                if let Some((_, val)) = obj.iter().next() {
                    if let Some(s) = val.as_str() {
                        command_to_run = Some(s.to_string());
                    }
                }
            }

            if let Some(command) = command_to_run {
                // Wrap in timeout so launching GUI apps doesn't hang the AI permanently
                let output = Command::new("timeout")
                    .arg("5")
                    .arg("bash")
                    .arg("-c")
                    .arg(&command)
                    .output()
                    .await;

                match output {
                    Ok(out) => {
                        let stdout = String::from_utf8_lossy(&out.stdout);
                        let stderr = String::from_utf8_lossy(&out.stderr);

                        if out.status.success() {
                            Some(format!("Success.\n{stdout}"))
                        } else if out.status.code() == Some(124) {
                            Some(format!("Command timed out after 5 seconds (this is normal if starting a long-running GUI app).\n{stdout}\n{stderr}"))
                        } else {
                            Some(format!(
                                "Failed (code {}).\n{stderr}\n{stdout}",
                                out.status.code().unwrap_or(1)
                            ))
                        }
                    }
                    Err(e) => Some(format!("Execution failed: {e}")),
                }
            } else {
                Some(format!("Error: Missing command argument. Received: {}", args))
            }
        }
        _ => None,
    }
}
