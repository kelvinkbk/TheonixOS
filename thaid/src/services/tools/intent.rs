use serde_json::{json, Value};
use tokio::process::Command;

pub fn get_intent_tools() -> Vec<Value> {
    vec![json!({
        "type": "function",
        "function": {
            "name": "install_application",
            "description": "The Intent Engine: Installs an application on the user's system by downloading it from the official repositories. It automatically handles elevated privileges graphically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "package_name": {
                        "type": "string",
                        "description": "The exact name of the package to install (e.g. 'discord', 'htop', 'gimp')."
                    }
                },
                "required": ["package_name"]
            }
        }
    })]
}

pub async fn execute_intent_tool(name: &str, args: &Value) -> Option<String> {
    match name {
        "install_application" => {
            if let Some(pkg) = args.get("package_name").and_then(|v| v.as_str()) {
                // We use pkexec to trigger a graphical password prompt for the user,
                // and pacman -S --noconfirm to install it silently once authorized.
                let output = Command::new("pkexec")
                    .arg("pacman")
                    .arg("-S")
                    .arg("--noconfirm")
                    .arg(pkg)
                    .output()
                    .await;

                match output {
                    Ok(out) => {
                        let stdout = String::from_utf8_lossy(&out.stdout);
                        let stderr = String::from_utf8_lossy(&out.stderr);
                        if out.status.success() {
                            Some(format!("Successfully installed '{}'.", pkg))
                        } else {
                            Some(format!(
                                "Failed to install '{}' (Code {}).\nError:\n{}\nOutput:\n{}",
                                pkg,
                                out.status.code().unwrap_or(1),
                                stderr,
                                stdout
                            ))
                        }
                    }
                    Err(e) => Some(format!(
                        "Execution failed (Make sure polkit and pkexec are running): {}",
                        e
                    )),
                }
            } else {
                Some("Error: Missing package_name argument".to_string())
            }
        }
        _ => None,
    }
}
