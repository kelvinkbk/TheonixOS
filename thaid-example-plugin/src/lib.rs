use std::future::Future;
use std::pin::Pin;
use std::sync::Arc;
use serde_json::{json, Value};
use thaid::services::tools::{Plugin, Tool};

pub struct WeatherTool;

impl Tool for WeatherTool {
    fn name(&self) -> &str {
        "get_weather"
    }

    fn description(&self) -> &str {
        "Get the current weather for a city."
    }

    fn schema(&self) -> Value {
        json!({
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": { "type": "string", "description": "The city to get weather for" }
                    },
                    "required": ["city"]
                }
            }
        })
    }

    fn execute<'a>(&'a self, args: &'a Value) -> Pin<Box<dyn Future<Output = Option<String>> + Send + 'a>> {
        Box::pin(async move {
            let city = args.get("city").and_then(|v| v.as_str()).unwrap_or("Unknown");
            Some(format!("The weather in {} is currently sunny and 75°F (Stubbed via dynamic plugin!).", city))
        })
    }
}

pub struct ExamplePlugin;

impl Plugin for ExamplePlugin {
    fn name(&self) -> &str { "ExampleWeatherPlugin" }
    fn version(&self) -> &str { "1.0.0" }
    
    fn initialize(&self) -> Result<(), String> {
        Ok(())
    }
    
    fn tools(&self) -> Vec<Arc<dyn Tool>> {
        vec![Arc::new(WeatherTool)]
    }
    
    fn unload(&self) -> Result<(), String> {
        Ok(())
    }
}

#[no_mangle]
pub unsafe extern "C" fn _plugin_create() -> *mut () {
    let plugin: Box<dyn Plugin> = Box::new(ExamplePlugin);
    Box::into_raw(plugin) as *mut ()
}
