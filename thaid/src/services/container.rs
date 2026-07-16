use std::sync::Arc;
use tokio::sync::RwLock;
use crate::services::memory::ConversationStore;
use crate::services::permissions::PermissionManager;
use crate::services::tools::ToolExecutor;
use crate::services::models::ModelManager;
use crate::services::metrics::MetricsService;

use std::collections::HashMap;
use tokio_util::sync::CancellationToken;
use crate::services::event_bus::EventBus;

/// The ServiceContainer holds all core services and dependencies.
/// This pattern enables true Dependency Injection, avoiding a tangled web
/// of Arc<RwLock<T>> passed individually to every struct.
#[derive(Clone)]
pub struct ServiceContainer {
    pub permission_manager: Arc<RwLock<PermissionManager>>,
    pub tool_executor: Arc<ToolExecutor>,
    pub memory: Arc<RwLock<ConversationStore>>,
    pub model_manager: Arc<ModelManager>,
    pub event_bus: Arc<EventBus>,
    pub metrics: Arc<MetricsService>,
    pub active_queries: Arc<RwLock<HashMap<String, CancellationToken>>>,
}

impl ServiceContainer {
    pub fn new(
        permission_manager: Arc<RwLock<PermissionManager>>,
        tool_executor: Arc<ToolExecutor>,
        memory: Arc<RwLock<ConversationStore>>,
        model_manager: Arc<ModelManager>,
        event_bus: Arc<EventBus>,
        metrics: Arc<MetricsService>,
    ) -> Self {
        Self {
            permission_manager,
            tool_executor,
            memory,
            model_manager,
            event_bus,
            metrics,
            active_queries: Arc::new(RwLock::new(HashMap::new())),
        }
    }
    
    pub async fn cancel_query(&self, session_id: &str) {
        let queries = self.active_queries.read().await;
        if let Some(token) = queries.get(session_id) {
            token.cancel();
        }
    }
}
