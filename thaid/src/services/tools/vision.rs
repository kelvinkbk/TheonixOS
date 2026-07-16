use serde_json::{json, Value};
use std::fs;
use tokio::process::Command;

pub fn get_vision_tools() -> Vec<Value> {
    vec![json!({
        "type": "function",
        "function": {
            "name": "read_screen_text",
            "description": "Capture a screenshot of the user's desktop and extract the text from it using OCR. Use this to 'see' what errors or applications the user is looking at.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    })]
}

pub async fn execute_vision_tool(name: &str, _args: &Value) -> Option<String> {
    match name {
        "read_screen_text" => {
            let img_path = "/tmp/thaid_vision.png";
            let txt_base = "/tmp/thaid_vision_text";
            let txt_full = "/tmp/thaid_vision_text.txt";

            // 1. Capture the screen (using spectacle on KDE)
            let _ = Command::new("spectacle")
                .arg("-b") // background mode
                .arg("-n") // non-notifying
                .arg("-o")
                .arg(img_path)
                .output()
                .await;

            // Allow spectacle to finish writing
            tokio::time::sleep(std::time::Duration::from_millis(500)).await;

            // 2. Run OCR (Tesseract)
            let ocr = Command::new("tesseract")
                .arg(img_path)
                .arg(txt_base)
                .output()
                .await;

            match ocr {
                Ok(out) if out.status.success() => {
                    // 3. Read the extracted text
                    match fs::read_to_string(txt_full) {
                        Ok(text) => {
                            if text.trim().is_empty() {
                                Some("No readable text found on the screen.".to_string())
                            } else {
                                Some(format!(
                                    "I have extracted the following text from the screen:\n{}",
                                    text.trim()
                                ))
                            }
                        }
                        Err(_) => Some("Failed to read the extracted text file.".to_string()),
                    }
                }
                _ => Some("OCR engine (tesseract) failed or is not installed.".to_string()),
            }
        }
        _ => None,
    }
}
