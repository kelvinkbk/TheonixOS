use serde_json::{json, Value};
use tokio::process::Command;

pub fn get_network_tools() -> Vec<Value> {
    vec![
        json!({
            "type": "function",
            "function": {
                "name": "scan_wifi",
                "description": "Scan for available WiFi networks nearby.",
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
                "name": "connect_wifi",
                "description": "Connect to a WiFi network.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ssid": {
                            "type": "string",
                            "description": "The SSID of the WiFi network."
                        },
                        "password": {
                            "type": "string",
                            "description": "The password for the network. Leave empty if it's an open network."
                        }
                    },
                    "required": ["ssid"]
                }
            }
        }),
    ]
}

pub async fn execute_network_tool(name: &str, args: &Value) -> Option<String> {
    match name {
        "scan_wifi" => {
            let output = Command::new("nmcli")
                .args(["-t", "-f", "SSID,SECURITY,SIGNAL", "dev", "wifi"])
                .output()
                .await;

            match output {
                Ok(out) if out.status.success() => {
                    let text = String::from_utf8_lossy(&out.stdout);
                    Some(format!(
                        "Available WiFi networks (SSID:SECURITY:SIGNAL):\n{}",
                        text.trim()
                    ))
                }
                _ => Some(
                    "Failed to scan WiFi networks. Make sure NetworkManager is running."
                        .to_string(),
                ),
            }
        }
        "connect_wifi" => {
            let ssid = args.get("ssid").and_then(|v| v.as_str())?;
            let password = args.get("password").and_then(|v| v.as_str()).unwrap_or("");
            let mut cmd = Command::new("nmcli");
            cmd.args(["dev", "wifi", "connect", ssid]);
            if !password.is_empty() {
                cmd.args(["password", password]);
            }

            let output = cmd.output().await;
            match output {
                Ok(out) if out.status.success() => Some(format!(
                    "Successfully connected to WiFi network '{}'.",
                    ssid
                )),
                Ok(out) => Some(format!(
                    "Failed to connect to '{}'. Output: {}",
                    ssid,
                    String::from_utf8_lossy(&out.stderr)
                )),
                Err(e) => Some(format!("Error running nmcli: {}", e)),
            }
        }
        _ => None,
    }
}
