use std::sync::Arc;
use std::collections::HashMap;
use crate::services::tools::Plugin;

/// PluginManager handles the dynamic loading of .so libraries.
pub struct PluginManager {
    loaded_plugins: HashMap<String, Arc<dyn Plugin>>,
    libraries: Vec<libloading::Library>,
    plugin_dir: String,
}

impl PluginManager {
    pub fn new() -> Self {
        let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
        let plugin_dir = format!("{}/.local/share/thaid/plugins", home);
        let _ = std::fs::create_dir_all(&plugin_dir);

        Self {
            loaded_plugins: HashMap::new(),
            libraries: Vec::new(),
            plugin_dir,
        }
    }

    /// Dynamically loads all plugins in the plugin directory.
    pub fn load_all_plugins(&mut self) -> Result<usize, String> {
        let mut count = 0;
        if let Ok(entries) = std::fs::read_dir(&self.plugin_dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.extension().and_then(|e| e.to_str()) == Some("so") {
                    if let Ok((plugin, lib)) = self.load_plugin(path.to_str().unwrap_or_default()) {
                        self.loaded_plugins.insert(plugin.name().to_string(), plugin);
                        self.libraries.push(lib);
                        count += 1;
                    } else {
                        tracing::error!("Failed to load plugin: {:?}", path);
                    }
                }
            }
        }
        Ok(count)
    }

    /// Load a single plugin dynamically via dlopen
    fn load_plugin(&self, path: &str) -> Result<(Arc<dyn Plugin>, libloading::Library), String> {
        unsafe {
            let lib = libloading::Library::new(path)
                .map_err(|e| format!("Library load error: {}", e))?;
            
            // The plugin MUST export a C-compatible function named `_plugin_create`
            // that returns a raw pointer to a Boxed trait object.
            let constructor: libloading::Symbol<unsafe extern "C" fn() -> *mut ()> = lib
                .get(b"_plugin_create\0")
                .map_err(|e| format!("Symbol _plugin_create not found: {}", e))?;
            
            let raw_ptr = constructor();
            if raw_ptr.is_null() {
                return Err("Plugin returned null pointer".to_string());
            }

            // Convert the raw pointer back to Box<dyn Plugin>
            let boxed_plugin = Box::from_raw(raw_ptr as *mut Box<dyn Plugin>);
            
            // Convert Box to Arc so we can share it
            let plugin: Arc<dyn Plugin> = Arc::from(*boxed_plugin);
            
            if let Err(e) = plugin.initialize() {
                return Err(format!("Plugin {} initialization failed: {}", plugin.name(), e));
            }
            
            tracing::info!("Successfully loaded dynamic plugin: {} (v{})", plugin.name(), plugin.version());
            
            Ok((plugin, lib))
        }
    }

    pub fn get_plugins(&self) -> Vec<Arc<dyn Plugin>> {
        self.loaded_plugins.values().cloned().collect()
    }
}
