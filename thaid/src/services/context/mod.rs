use tokio::process::Command;

pub struct ContextManager;

impl ContextManager {
    /// Gathers environmental context for the AI (e.g. active window)
    pub async fn get_environmental_context() -> Option<String> {
        let output = Command::new("qdbus")
            .arg("org.kde.KWin")
            .arg("/KWin")
            .arg("supportInformation")
            .output()
            .await;

        if let Ok(out) = output {
            let info = String::from_utf8_lossy(&out.stdout).to_string();
            // Parse KWin output for Active Window manually
            let active_window_info = info.lines()
                .skip_while(|line| !line.contains("Active Window"))
                .take(6) // Take the header + next 5 lines
                .collect::<Vec<&str>>()
                .join("\n");
                
            if !active_window_info.trim().is_empty() && active_window_info.contains("Active Window") {
                return Some(format!(
                    "ENVIRONMENT CONTEXT (For your awareness only, don't mention it unless relevant): The user's currently active window is:\n{}",
                    active_window_info
                ));
            }
        }
        None
    }
}
