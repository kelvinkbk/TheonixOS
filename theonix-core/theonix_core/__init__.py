"""
Theonix Core — Unified Platform Services, IPC & UI Engine for Theonix OS.
"""

__version__ = "2.0.0"
__author__ = "The Theonix Team"

from .ui import (
    THEONIX_THEME_QSS,
    GlassCard,
    NavButton,
    Badge,
    TelemetryBar,
    SearchBar,
    QuickLookDialog,
    apply_theonix_style
)

from .services import (
    ThemeService,
    PackageService,
    SearchService,
    SystemService,
    AIService,
    ActionService,
    UACLService,
    CompatibilityRating,
    UpdateClient,
    AuthClient,
    NotificationClient,
    SearchClient
)

# 7-Pillar THAID Architecture
from .events import EventBus, bus, Event
from .permissions import PermissionManager, permission_mgr, PermissionLevel
from .tools import ToolRegistry, tools, Tool
from .context import ContextManager, BrowserContext
from .sessions import SessionManager, session_mgr
from .router import ModelRouter
from .browser import BrowserService
from .voice import VoiceEngine
