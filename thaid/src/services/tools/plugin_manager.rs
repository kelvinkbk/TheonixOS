use std::sync::Arc;
use std::collections::HashMap;
use crate::services::tools::Plugin;

/// PluginManager handles the dynamic loading of .so or .wasm libraries.
/// In Phase 3, this reads from ~/.local/share/thaid/plugins/
pub struct PluginManager {
    loaded_plugins: HashMap<String, Arc<dyn Plugin>>,
    plugin_dir: String,
}

impl PluginManager {
    pub fn new() -> Self {
        let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
        let plugin_dir = format!("{}/.local/share/thaid/plugins", home);
        let _ = std::fs::create_dir_all(&plugin_dir);

        Self {
            loaded_plugins: HashMap::new(),
            plugin_dir,
        }
    }

    /// Dynamically loads all plugins in the plugin directory.
    /// In a fully compiled environment, this will use the `libloading` crate
    /// to safely execute dlopen() on .so files and extract the Plugin trait objects.
    pub fn load_all_plugins(&mut self) -> Result<usize, String> {
        let mut count = 0;
        if let Ok(entries) = std::fs::read_dir(&self.plugin_dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.extension().and_then(|e| e.to_str()) == Some("so") {
                    if let Ok(plugin) = self.load_plugin(path.to_str().unwrap_or_default()) {
                        self.loaded_plugins.insert(plugin.name().to_string(), plugin);
                        count += 1;
                    }
                }
            }
        }
        Ok(count)
    }

    /// Load a single plugin dynamically via dlopen
    fn load_plugin(&self, _path: &str) -> Result<Arc<dyn Plugin>, String> {
        // [PENDING Phase 3 Compilation]
        // This is where `libloading::Library::new(path)` will be invoked.
        // For now, it returns a stub error until `libloading` is added to Cargo.toml
        Err("Dynamic loading requires libloading crate".to_string())
    }

    pub fn get_plugins(&self) -> Vec<Arc<dyn Plugin>> {
        self.loaded_plugins.values().cloned().collect()
    }
}
