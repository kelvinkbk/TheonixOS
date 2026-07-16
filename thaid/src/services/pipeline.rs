use std::collections::HashMap;
use crate::services::container::ServiceContainer;
use zbus::zvariant::OwnedValue;
use std::sync::Arc;

pub struct PipelineContext {
    pub prompt: String,
    pub options: HashMap<String, OwnedValue>,
    pub history: Vec<(String, String)>,
    pub facts: Vec<(String, String)>,
    pub environment: Option<String>,
    pub routed_model: Option<String>,
    pub response: Option<String>,
    pub session_id: Option<String>,
    pub token: tokio_util::sync::CancellationToken,
}

pub trait PipelineStep: Send + Sync {
    fn name(&self) -> &str;
    fn execute<'a>(&'a self, ctx: &'a mut PipelineContext, container: &'a ServiceContainer) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<(), String>> + Send + 'a>>;
}

pub struct Pipeline {
    steps: Vec<Arc<dyn PipelineStep>>,
}

impl Pipeline {
    pub fn new() -> Self {
        Self { steps: Vec::new() }
    }

    pub fn add_step(&mut self, step: Arc<dyn PipelineStep>) {
        self.steps.push(step);
    }

    pub async fn execute(&self, prompt: String, options: HashMap<String, OwnedValue>, container: &ServiceContainer, token: tokio_util::sync::CancellationToken) -> Result<String, String> {
        let session_id: Option<String> = options
            .get("session")
            .and_then(|v| <&str>::try_from(v).ok())
            .map(|s| s.to_string());

        let mut ctx = PipelineContext {
            prompt,
            options,
            history: Vec::new(),
            facts: Vec::new(),
            environment: None,
            routed_model: None,
            response: None,
            session_id,
            token,
        };

        for step in &self.steps {
            if ctx.token.is_cancelled() {
                return Err("Query was cancelled".to_string());
            }
            tracing::debug!("Executing Pipeline Step: {}", step.name());
            step.execute(&mut ctx, container).await?;
        }

        ctx.response.ok_or_else(|| "Pipeline completed without generating a response".to_string())
    }
}
