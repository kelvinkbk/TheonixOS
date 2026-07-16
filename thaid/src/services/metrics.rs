use std::sync::atomic::{AtomicU64, Ordering};

/// MetricsService tracks operational telemetry for THAID.
/// In Phase 4, this scaffolds the foundation for a /metrics Prometheus endpoint.
pub struct MetricsService {
    pub total_queries_handled: AtomicU64,
    pub total_tools_executed: AtomicU64,
    pub active_pipelines: AtomicU64,
}

impl MetricsService {
    pub fn new() -> Self {
        Self {
            total_queries_handled: AtomicU64::new(0),
            total_tools_executed: AtomicU64::new(0),
            active_pipelines: AtomicU64::new(0),
        }
    }

    pub fn record_query(&self) {
        self.total_queries_handled.fetch_add(1, Ordering::Relaxed);
    }

    pub fn record_tool_execution(&self) {
        self.total_tools_executed.fetch_add(1, Ordering::Relaxed);
    }
}
