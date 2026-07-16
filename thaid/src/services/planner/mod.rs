use crate::services::container::ServiceContainer;
use crate::services::pipeline::{Pipeline, PipelineContext, PipelineStep};
use std::collections::HashMap;
use zbus::zvariant::OwnedValue;

pub struct Planner {
    container: ServiceContainer,
}

impl Planner {
    pub fn new(container: ServiceContainer) -> Self {
        Self { container }
    }

    pub async fn handle_query(
        &self,
        prompt: String,
        options: HashMap<String, OwnedValue>,
    ) -> Result<String, String> {
        let session_id: Option<String> = options
            .get("session")
            .and_then(|v| <&str>::try_from(v).ok())
            .map(|s| s.to_string());

        let token = tokio_util::sync::CancellationToken::new();
        
        if let Some(ref sid) = session_id {
            let mut queries = self.container.active_queries.write().await;
            queries.insert(sid.clone(), token.clone());
        }

        let mut pipeline = Pipeline::new();
        
        // Add all steps
        pipeline.add_step(std::sync::Arc::new(MemoryStep));
        pipeline.add_step(std::sync::Arc::new(ContextStep));
        pipeline.add_step(std::sync::Arc::new(PromptStep));
        pipeline.add_step(std::sync::Arc::new(DispatcherStep));
        pipeline.add_step(std::sync::Arc::new(ResponseStep));

        let result = pipeline.execute(prompt, options, &self.container, token).await;

        result
    }

    pub async fn cancel_query(&self, session_id: &str) {
        self.container.cancel_query(session_id).await;
    }
}

// ---- Pipeline Steps ----

struct MemoryStep;
impl PipelineStep for MemoryStep {
    fn name(&self) -> &str { "MemoryStep" }
    fn execute<'a>(&'a self, ctx: &'a mut PipelineContext, container: &'a ServiceContainer) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<(), String>> + Send + 'a>> {
        Box::pin(async move {
            let memory = container.memory.read().await;
            if let Some(ref sid) = ctx.session_id {
                ctx.history = memory.get_history(sid).await.unwrap_or_default();
            }
            
            // 1. Load explicit facts
            ctx.facts = memory.get_all_facts().await.unwrap_or_default();
            
            // 2. Load semantic facts (Phase 4 Vector Search)
            let vector_store = crate::services::memory::vector::StubVectorStore;
            use crate::services::memory::vector::VectorStore;
            if let Ok(semantic_results) = vector_store.search_similar(&[], 3) {
                for result in semantic_results {
                    ctx.facts.push(("semantic_context".to_string(), result));
                }
            }

            Ok(())
        })
    }
}

struct ContextStep;
impl PipelineStep for ContextStep {
    fn name(&self) -> &str { "ContextStep" }
    fn execute<'a>(&'a self, ctx: &'a mut PipelineContext, _container: &'a ServiceContainer) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<(), String>> + Send + 'a>> {
        Box::pin(async move {
            ctx.environment = crate::services::context::ContextManager::get_environmental_context().await;
            Ok(())
        })
    }
}

struct PromptStep;
impl PipelineStep for PromptStep {
    fn name(&self) -> &str { "PromptStep" }
    fn execute<'a>(&'a self, ctx: &'a mut PipelineContext, _container: &'a ServiceContainer) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<(), String>> + Send + 'a>> {
        Box::pin(async move {
            let pctx = crate::services::models::prompt_builder::PromptContext {
                history: ctx.history.clone(),
                facts: ctx.facts.clone(),
                environment: ctx.environment.clone(),
            };
            ctx.history = crate::services::models::PromptBuilder::build(pctx);
            Ok(())
        })
    }
}

struct DispatcherStep;
impl PipelineStep for DispatcherStep {
    fn name(&self) -> &str { "DispatcherStep" }
    fn execute<'a>(&'a self, ctx: &'a mut PipelineContext, container: &'a ServiceContainer) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<(), String>> + Send + 'a>> {
        Box::pin(async move {
            use crate::services::agents::{Agent, SystemAgent, CoderAgent, VerifierAgent};

            // 1. Route the model using ModelRouter (for backend LLM selection)
            let model_override: Option<String> = ctx.options
                .get("model")
                .and_then(|v| <&str>::try_from(v).ok())
                .map(|s| s.to_string());
            
            let router = crate::services::models::router::ModelRouter::new();
            ctx.routed_model = router.route_query(&ctx.prompt, model_override);

            // 2. Dispatch to the appropriate Agent (Multi-Agent Swarm logic)
            // For now, simple keyword matching. In Phase 4, an LLM determines the agent.
            let agent: Box<dyn Agent> = if ctx.prompt.to_lowercase().contains("code") || ctx.prompt.to_lowercase().contains("python") {
                Box::new(CoderAgent)
            } else {
                Box::new(SystemAgent)
            };

            tracing::info!("Dispatcher assigning task to {}", agent.name());
            agent.execute(ctx, container).await?;
            
            // 3. Verifier checks the response
            let verifier = VerifierAgent;
            verifier.execute(ctx, container).await?;

            Ok(())
        })
    }
}

struct ResponseStep;
impl PipelineStep for ResponseStep {
    fn name(&self) -> &str { "ResponseStep" }
    fn execute<'a>(&'a self, ctx: &'a mut PipelineContext, container: &'a ServiceContainer) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<(), String>> + Send + 'a>> {
        Box::pin(async move {
            if let Some(sid) = &ctx.session_id {
                if let Some(resp) = &ctx.response {
                    let mut memory = container.memory.write().await;
                    let _ = memory.append_turn(sid, &ctx.prompt, resp).await;
                    let _ = memory.enforce_limits(sid, 100).await;
                }
            }
            Ok(())
        })
    }
}
