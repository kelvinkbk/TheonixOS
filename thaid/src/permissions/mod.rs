// thaid permissions module — polkit integration stubs (Phase 2)
// Full polkit integration implemented in Phase 3

/// Permission tiers for AI operations
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum PermissionTier {
    /// Read-only: AI can only read files and system info
    ReadOnly = 0,
    /// Suggest: AI shows commands but does not execute them
    Suggest = 1,
    /// Execute: AI can run pre-approved commands
    Execute = 2,
    /// Admin: AI can run privileged commands (requires polkit prompt)
    Admin = 3,
}
