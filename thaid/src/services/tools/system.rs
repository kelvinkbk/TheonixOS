use serde_json::{json, Value};
use tokio::process::Command;
use std::sync::Arc;
use crate::services::tools::Tool;
use std::future::Future;
use std::pin::Pin;

pub struct GetSystemInfoTool;
impl Tool for GetSystemInfoTool {
    fn name(&self) -> &str { "get_system_info" }
    fn description(&self) -> &str { "Get the current system health including CPU usage, RAM, and temperatures." }
    fn schema(&self) -> Value {
        json!({
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": { "type": "object", "properties": {}, "required": [] }
            }
        })
    }
    fn execute<'a>(&'a self, _args: &'a Value) -> Pin<Box<dyn Future<Output = Option<String>> + Send + 'a>> {
        Box::pin(async move {
            let output = Command::new("bash")
                .arg("-c")
                .arg("echo 'CPU & Memory Info:'; top -b -n 1 | head -n 5; echo ''; free -m")
                .output()
                .await;
            match output {
                Ok(out) => Some(String::from_utf8_lossy(&out.stdout).to_string()),
                Err(e) => Some(format!("Failed to get system info: {}", e)),
            }
        })
    }
}

pub struct SetVolumeTool;
impl Tool for SetVolumeTool {
    fn name(&self) -> &str { "set_volume" }
    fn description(&self) -> &str { "Set the system audio volume (0-100)." }
    fn schema(&self) -> Value {
        json!({
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": { "level": { "type": "integer", "description": "Volume level from 0 to 100" } },
                    "required": ["level"]
                }
            }
        })
    }
    fn execute<'a>(&'a self, args: &'a Value) -> Pin<Box<dyn Future<Output = Option<String>> + Send + 'a>> {
        Box::pin(async move {
            if let Some(level) = args.get("level").and_then(|v| v.as_i64()) {
                let cmd = format!("amixer -D pulse sset Master {}%", level);
                let _ = Command::new("bash").arg("-c").arg(&cmd).output().await;
                Some(format!("Volume set to {}%", level))
            } else {
                Some("Error: Missing level argument".to_string())
            }
        })
    }
}

pub struct LaunchAppTool;
impl Tool for LaunchAppTool {
    fn name(&self) -> &str { "launch_app" }
    fn description(&self) -> &str { "Open or launch a graphical desktop application (e.g. Chrome, Firefox) by name." }
    fn schema(&self) -> Value {
        json!({
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": { "app_name": { "type": "string", "description": "The name of the application to launch (e.g., 'chrome', 'firefox')" } },
                    "required": ["app_name"]
                }
            }
        })
    }
    fn execute<'a>(&'a self, args: &'a Value) -> Pin<Box<dyn Future<Output = Option<String>> + Send + 'a>> {
        Box::pin(async move {
            if let Some(app) = args.get("app_name").and_then(|v| v.as_str()) {
                let app_lower = app.to_lowercase();
                let binary = match app_lower.as_str() {
                    "chrome" | "google chrome" => "(google-chrome-stable || google-chrome || chromium || chromium-browser)",
                    "firefox" | "mozilla" => "(firefox || firefox-developer-edition || librewolf)",
                    "discord" => "(discord || discord-canary || webcord)",
                    "terminal" | "console" => "(konsole || alacritty || kitty || gnome-terminal || xterm)",
                    "files" | "file manager" => "(dolphin || nautilus || thunar || pcmanfm)",
                    "settings" => "(systemsettings || gnome-control-center || xfce4-settings-manager)",
                    _ => app,
                };
                
                let _ = Command::new("bash")
                    .arg("-c")
                    .arg(format!("{} &", binary))
                    .spawn();
                    
                Some(format!("Launched application: {}", app))
            } else {
                Some("Error: Missing app_name argument".to_string())
            }
        })
    }
}

pub struct RunOsCommandTool;
impl Tool for RunOsCommandTool {
    fn name(&self) -> &str { "run_os_command" }
    fn description(&self) -> &str { "Execute a system command securely using program name and arguments array." }
    fn schema(&self) -> Value {
        json!({
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": { 
                        "program": { "type": "string", "description": "The executable program to run (e.g., 'systemctl', 'echo', 'mkdir')." },
                        "args": { "type": "array", "items": { "type": "string" }, "description": "Array of arguments to pass to the program." }
                    },
                    "required": ["program", "args"]
                }
            }
        })
    }
    fn execute<'a>(&'a self, args: &'a Value) -> Pin<Box<dyn Future<Output = Option<String>> + Send + 'a>> {
        Box::pin(async move {
            let program = args.get("program").and_then(|v| v.as_str());
            let cmd_args = args.get("args").and_then(|v| v.as_array());

            if let (Some(prog), Some(arr)) = (program, cmd_args) {
                let mut string_args = Vec::new();
                for arg in arr {
                    if let Some(s) = arg.as_str() {
                        string_args.push(s.to_string());
                    }
                }

                // Still wrap in timeout to prevent hanging
                const TOOL_TIMEOUT: &str = "5";
                let mut cmd = Command::new("timeout");
                cmd.arg(TOOL_TIMEOUT).arg(prog).args(&string_args);

                match cmd.output().await {
                    Ok(out) => {
                        let stdout = String::from_utf8_lossy(&out.stdout);
                        let stderr = String::from_utf8_lossy(&out.stderr);

                        if out.status.success() {
                            Some(format!("Success.\n{stdout}"))
                        } else if out.status.code() == Some(124) {
                            Some(format!("Command timed out after {} seconds.\n{}\n{}", TOOL_TIMEOUT, stdout, stderr))
                        } else {
                            Some(format!("Failed (code {}).\n{}\n{}", out.status.code().unwrap_or(1), stderr, stdout))
                        }
                    }
                    Err(e) => Some(format!("Execution failed: {e}")),
                }
            } else {
                Some(format!("Error: Missing program or args. Received: {}", args))
            }
        })
    }
}

pub fn get_system_tools() -> Vec<Value> {
    vec![] // Return empty, we register directly in ToolExecutor now
}

pub async fn execute_system_tool(_name: &str, _args: &Value) -> Option<String> {
    None // Fallback removed, handled by ToolExecutor registry
}
