use serde_json::{json, Value};
use tokio::process::Command;

pub fn get_settings_tools() -> Vec<Value> {
    vec![json!({
        "type": "function",
        "function": {
            "name": "change_desktop_settings",
            "description": "Change the desktop environment settings like the theme (dark/light) or wallpaper.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "The setting to change: 'theme' or 'wallpaper'"
                    },
                    "argument": {
                        "type": "string",
                        "description": "If theme, 'org.kde.breezedark.desktop' or 'org.kde.breeze.desktop'. If wallpaper, the absolute path to the image."
                    }
                },
                "required": ["action", "argument"]
            }
        }
    })]
}

pub async fn execute_settings_tool(name: &str, args: &Value) -> Option<String> {
    match name {
        "change_desktop_settings" => {
            let action = match args.get("action").and_then(|v| v.as_str()) {
                Some(a) => a,
                None => return Some("Error: Missing required argument 'action' (must be 'theme' or 'wallpaper').".to_string()),
            };
            
            let argument = match args.get("argument").and_then(|v| v.as_str()) {
                Some(a) => a,
                None => return Some("Error: Missing required argument 'argument' (e.g. theme name or wallpaper path).".to_string()),
            };

            match action {
                "theme" => {
                    let output = Command::new("lookandfeeltool")
                        .arg("-a")
                        .arg(argument)
                        .output()
                        .await;
                    match output {
                        Ok(out) if out.status.success() => {
                            Some(format!("Successfully changed theme to {}.", argument))
                        }
                        _ => Some("Failed to change theme.".to_string()),
                    }
                }
                "wallpaper" => {
                    let output = Command::new("plasma-apply-wallpaperimage")
                        .arg(argument)
                        .output()
                        .await;
                    match output {
                        Ok(out) if out.status.success() => {
                            Some(format!("Successfully changed wallpaper to {}.", argument))
                        }
                        _ => Some("Failed to change wallpaper.".to_string()),
                    }
                }
                _ => Some(format!("Unknown action: {}", action)),
            }
        }
        _ => None,
    }
}
