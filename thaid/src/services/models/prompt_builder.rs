pub struct PromptContext {
    pub history: Vec<(String, String)>,
    pub facts: Vec<(String, String)>,
    pub environment: Option<String>,
}

pub struct PromptBuilder;

impl PromptBuilder {
    pub fn build(context: PromptContext) -> Vec<(String, String)> {
        let mut final_prompt = Vec::new();

        if !context.facts.is_empty() {
            let mut facts_str = String::from("Here are some persistent facts you have learned about the user and MUST remember:\n");
            for (k, v) in context.facts {
                facts_str.push_str(&format!("- {}: {}\n", k, v));
            }
            final_prompt.push(("system".to_string(), facts_str));
        }

        if let Some(env) = context.environment {
            final_prompt.push(("system".to_string(), env));
        }

        final_prompt.extend(context.history);
        final_prompt
    }
}
