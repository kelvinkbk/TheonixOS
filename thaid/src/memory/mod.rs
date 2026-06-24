// =============================================================================
// thaid — Conversation Memory (SQLite)
// =============================================================================

use anyhow::{Context, Result};
use rusqlite::{params, Connection};
use std::path::PathBuf;
use std::sync::Mutex;
use tracing::{debug, info};

/// Stores AI conversation history in a local SQLite database.
/// Thread-safe via Mutex (all methods take &self but acquire the lock internally).
pub struct ConversationStore {
    conn: Mutex<Connection>,
}

impl ConversationStore {
    /// Open (or create) the SQLite database and run schema migrations.
    pub async fn open(path: &PathBuf) -> Result<Self> {
        // Ensure the parent directory exists
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)
                .with_context(|| format!("Cannot create memory dir: {}", parent.display()))?;
        }

        let conn = Connection::open(path)
            .with_context(|| format!("Cannot open memory DB at: {}", path.display()))?;

        // Enable WAL mode for better concurrent performance
        conn.execute_batch("PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;")?;

        // Schema migration (idempotent)
        conn.execute_batch(
            "
            CREATE TABLE IF NOT EXISTS sessions (
                id         TEXT PRIMARY KEY,
                created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
                updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
            );

            CREATE TABLE IF NOT EXISTS turns (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                role       TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content    TEXT NOT NULL,
                created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
            );

            CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id, created_at);
        ",
        )?;

        info!(path = %path.display(), "Conversation memory database opened");
        Ok(Self { conn: Mutex::new(conn) })
    }

    /// Create a new conversation session.
    pub async fn create_session(&mut self, session_id: &str) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT OR IGNORE INTO sessions (id) VALUES (?1)",
            params![session_id],
        ).context("Failed to create session")?;
        debug!(session_id, "Session created");
        Ok(())
    }

    /// Append a user+assistant turn to a session.
    pub async fn append_turn(
        &mut self,
        session_id: &str,
        user_prompt: &str,
        assistant_response: &str,
    ) -> Result<()> {
        let conn = self.conn.lock().unwrap();

        // Ensure session exists (create if it doesn't)
        conn.execute(
            "INSERT OR IGNORE INTO sessions (id) VALUES (?1)",
            params![session_id],
        )?;

        // Insert user message
        conn.execute(
            "INSERT INTO turns (session_id, role, content) VALUES (?1, 'user', ?2)",
            params![session_id, user_prompt],
        )?;

        // Insert assistant message
        conn.execute(
            "INSERT INTO turns (session_id, role, content) VALUES (?1, 'assistant', ?2)",
            params![session_id, assistant_response],
        )?;

        // Update session timestamp
        conn.execute(
            "UPDATE sessions SET updated_at = strftime('%s', 'now') WHERE id = ?1",
            params![session_id],
        )?;

        Ok(())
    }

    /// Build a context-aware prompt by prepending recent conversation history.
    /// Returns a formatted string suitable for sending to Ollama.
    pub async fn build_context_prompt(&self, session_id: &str, new_prompt: &str) -> Result<String> {
        let conn = self.conn.lock().unwrap();

        // Get the last N turns (most recent first, then reverse)
        let mut stmt = conn.prepare(
            "SELECT role, content FROM turns
             WHERE session_id = ?1
             ORDER BY created_at DESC
             LIMIT 20",
        )?;

        let turns: Vec<(String, String)> = stmt
            .query_map(params![session_id], |row| Ok((row.get(0)?, row.get(1)?)))?
            .filter_map(|r| r.ok())
            .collect();

        if turns.is_empty() {
            return Ok(new_prompt.to_string());
        }

        // Build context string (oldest first)
        let mut context = String::new();
        for (role, content) in turns.iter().rev() {
            match role.as_str() {
                "user" => context.push_str(&format!("User: {content}\n")),
                "assistant" => context.push_str(&format!("Assistant: {content}\n")),
                _ => {}
            }
        }
        context.push_str(&format!("User: {new_prompt}\nAssistant:"));

        Ok(context)
    }

    /// Delete a session and all its turns.
    pub async fn delete_session(&mut self, session_id: &str) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute("DELETE FROM sessions WHERE id = ?1", params![session_id])
            .context("Failed to delete session")?;
        debug!(session_id, "Session deleted");
        Ok(())
    }

    /// Enforce memory limits: delete oldest turns beyond max_turns per session.
    pub async fn enforce_limits(&mut self, session_id: &str, max_turns: usize) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "DELETE FROM turns WHERE session_id = ?1 AND id NOT IN (
                SELECT id FROM turns WHERE session_id = ?1
                ORDER BY created_at DESC LIMIT ?2
            )",
            params![session_id, max_turns as i64 * 2], // *2 because each turn = 2 rows
        )?;
        Ok(())
    }
}
