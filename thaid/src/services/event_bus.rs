use std::sync::Arc;
use tokio::sync::broadcast;
use serde::Serialize;

#[derive(Clone, Serialize, Debug)]
pub enum ThaidEvent {
    MemoryUpdated { session_id: String },
    ToolExecuted { tool_name: String, status: String },
    ModelSwitched { new_model: String },
    Notification { message: String },
    SpeechStarted,
    SpeechEnded,
}

pub struct EventBus {
    sender: broadcast::Sender<ThaidEvent>,
}

impl EventBus {
    pub fn new() -> Self {
        let (sender, _) = broadcast::channel(100);
        Self { sender }
    }

    pub fn subscribe(&self) -> broadcast::Receiver<ThaidEvent> {
        self.sender.subscribe()
    }

    pub fn publish(&self, event: ThaidEvent) {
        // We ignore SendError because it just means there are no subscribers right now.
        let _ = self.sender.send(event);
    }
}
