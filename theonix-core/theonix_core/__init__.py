"""
Theonix Core — Unified Platform Services, IPC & UI Engine for Theonix OS.
"""

__version__ = "1.0.0"
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
    UACLService,
    CompatibilityRating
)
