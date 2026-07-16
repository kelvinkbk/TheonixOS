use std::pin::Pin;
use std::future::Future;
use crate::services::container::ServiceContainer;
use crate::services::pipeline::PipelineContext;

/// The Agent trait defines a specialist that can process a PipelineContext.
pub trait Agent: Send + Sync {
    fn name(&self) -> &str;
    fn description(&self) -> &str;
    
    /// Execute the agent's specific reasoning loop.
    fn execute<'a>(
        &'a self,
        ctx: &'a mut PipelineContext,
        container: &'a ServiceContainer,
    ) -> Pin<Box<dyn Future<Output = Result<(), String>> + Send + 'a>>;
}

/// The SystemAgent specializes in system administration and OS tools.
pub struct SystemAgent;
impl Agent for SystemAgent {
    fn name(&self) -> &str { "SystemAgent" }
    fn description(&self) -> &str { "Handles OS configuration, package management, and system administration." }
    
    fn execute<'a>(
        &'a self,
        ctx: &'a mut PipelineContext,
        container: &'a ServiceContainer,
    ) -> Pin<Box<dyn Future<Output = Result<(), String>> + Send + 'a>> {
        Box::pin(async move {
            tracing::info!("SystemAgent: Taking control of context");
            // [PENDING Phase 4 Compilation]
            // This is where the Agent-specific prompting and Tool selection loop will live.
            let response = container.model_manager
                .chat(&ctx.history, &ctx.prompt, ctx.routed_model.as_deref(), &container.memory, &container.tool_executor)
                .await
                .map_err(|e| format!("SystemAgent failed: {e}"))?;
            ctx.response = Some(response);
            Ok(())
        })
    }
}

/// The CoderAgent specializes in software development, reading files, and writing code.
pub struct CoderAgent;
impl Agent for CoderAgent {
    fn name(&self) -> &str { "CoderAgent" }
    fn description(&self) -> &str { "Handles coding tasks, git operations, and file editing." }
    
    fn execute<'a>(
        &'a self,
        ctx: &'a mut PipelineContext,
        container: &'a ServiceContainer,
    ) -> Pin<Box<dyn Future<Output = Result<(), String>> + Send + 'a>> {
        Box::pin(async move {
            tracing::info!("CoderAgent: Analyzing codebase");
            // [PENDING Phase 4 Compilation]
            let response = container.model_manager
                .chat(&ctx.history, &ctx.prompt, ctx.routed_model.as_deref(), &container.memory, &container.tool_executor)
                .await
                .map_err(|e| format!("CoderAgent failed: {e}"))?;
            ctx.response = Some(response);
            Ok(())
        })
    }
}

/// The VerifierAgent double checks the output of other agents against the original constraints.
pub struct VerifierAgent;
impl Agent for VerifierAgent {
    fn name(&self) -> &str { "VerifierAgent" }
    fn description(&self) -> &str { "Critiques and verifies the response against the user prompt." }
    
    fn execute<'a>(
        &'a self,
        _ctx: &'a mut PipelineContext,
        _container: &'a ServiceContainer,
    ) -> Pin<Box<dyn Future<Output = Result<(), String>> + Send + 'a>> {
        Box::pin(async move {
            tracing::info!("VerifierAgent: Critiquing output...");
            // [PENDING Phase 4 Compilation]
            Ok(())
        })
    }
}
