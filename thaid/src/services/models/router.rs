use serde::Deserialize;

#[derive(Deserialize, Clone)]
pub struct RouteRule {
    pub keywords: Vec<String>,
    pub model: String,
    pub priority: i32,
}

#[derive(Deserialize, Clone)]
pub struct RouterConfig {
    pub rules: Vec<RouteRule>,
}

pub struct ModelRouter {
    config: RouterConfig,
}

impl ModelRouter {
    pub fn new() -> Self {
        // Attempt to load from /etc/theonix/router.json
        let config_path = "/etc/theonix/router.json";
        
        let default_rules = vec![
            RouteRule {
                keywords: vec!["code".into(), "rust".into(), "python".into(), "bug".into()],
                model: "qwen2.5-coder:7b".into(),
                priority: 100,
            },
            RouteRule {
                keywords: vec!["wifi".into(), "dns".into()],
                model: "network-agent".into(),
                priority: 90,
            }
        ];

        let config = if let Ok(data) = std::fs::read_to_string(config_path) {
            serde_json::from_str(&data).unwrap_or(RouterConfig { rules: default_rules.clone() })
        } else {
            RouterConfig { rules: default_rules }
        };
        
        Self { config }
    }

    /// Determines which model should handle the given prompt.
    /// Supports routing to specialized agents based on RouteRules.
    pub fn route_query(&self, prompt: &str, override_model: Option<String>) -> Option<String> {
        if override_model.is_some() {
            return override_model;
        }

        let lower_prompt = prompt.to_lowercase();
        
        let mut best_match: Option<&RouteRule> = None;
        
        for rule in &self.config.rules {
            if rule.keywords.iter().any(|k| lower_prompt.contains(k)) {
                if let Some(best) = best_match {
                    if rule.priority > best.priority {
                        best_match = Some(rule);
                    }
                } else {
                    best_match = Some(rule);
                }
            }
        }

        if let Some(matched) = best_match {
            tracing::info!("Routing query to Specialist ({})", matched.model);
            Some(matched.model.clone())
        } else {
            None
        }
    }
}
