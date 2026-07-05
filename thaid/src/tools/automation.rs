use serde_json::{json, Value};
use tokio::process::Command;
use std::fs;
use std::path::PathBuf;

pub fn get_automation_tools() -> Vec<Value> {
    vec![
        json!({
            "type": "function",
            "function": {
                "name": "schedule_task",
                "description": "Schedule a background task to run periodically or at a specific time using systemd timers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_name": {
                            "type": "string",
                            "description": "A short, no-spaces name for the task (e.g. 'backup_script', 'remind_water')."
                        },
                        "schedule": {
                            "type": "string",
                            "description": "The systemd OnCalendar expression (e.g. '*-*-* *:00:00' for hourly, 'Mon *-*-* 09:00:00' for Mondays at 9am, or 'minutely')."
                        },
                        "command": {
                            "type": "string",
                            "description": "The bash command to execute."
                        }
                    },
                    "required": ["task_name", "schedule", "command"]
                }
            }
        })
    ]
}

pub async fn execute_automation_tool(name: &str, args: &Value) -> Option<String> {
    match name {
        "schedule_task" => {
            let task_name = args.get("task_name").and_then(|v| v.as_str())?;
            let schedule = args.get("schedule").and_then(|v| v.as_str())?;
            let command = args.get("command").and_then(|v| v.as_str())?;
            
            // Expand home directory
            let home = match std::env::var("HOME") {
                Ok(h) => h,
                Err(_) => return Some("Error: HOME environment variable not set.".to_string()),
            };
            
            let systemd_dir = PathBuf::from(home).join(".config/systemd/user");
            if !systemd_dir.exists() {
                if let Err(e) = fs::create_dir_all(&systemd_dir) {
                    return Some(format!("Failed to create systemd user directory: {}", e));
                }
            }
            
            let service_content = format!(
r#"[Unit]
Description=THAID Automation: {}

[Service]
Type=oneshot
ExecStart=/bin/bash -c "{}"
"#, task_name, command);

            let timer_content = format!(
r#"[Unit]
Description=Timer for THAID Automation: {}

[Timer]
OnCalendar={}
Persistent=true

[Install]
WantedBy=timers.target
"#, task_name, schedule);

            let service_path = systemd_dir.join(format!("{}.service", task_name));
            let timer_path = systemd_dir.join(format!("{}.timer", task_name));
            
            if fs::write(&service_path, service_content).is_err() || fs::write(&timer_path, timer_content).is_err() {
                return Some("Failed to write systemd unit files.".to_string());
            }
            
            // Reload daemon and enable timer
            let _ = Command::new("systemctl").args(["--user", "daemon-reload"]).output().await;
            let output = Command::new("systemctl")
                .args(["--user", "enable", "--now", &format!("{}.timer", task_name)])
                .output()
                .await;
                
            match output {
                Ok(out) if out.status.success() => Some(format!("Successfully scheduled task '{}' with schedule: {}", task_name, schedule)),
                Ok(out) => Some(format!("Failed to enable timer. Output: {}", String::from_utf8_lossy(&out.stderr))),
                Err(e) => Some(format!("Error running systemctl: {}", e)),
            }
        },
        _ => None,
    }
}
