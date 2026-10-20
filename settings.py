"""
SleepSync - Settings Management
Provides application configuration state, theme definitions, and persistence.
"""

from typing import Dict, Any, Callable, List
from database import Database

# Theme color palettes
THEMES = {
    "dark": {
        "name": "Dark Navy",
        "bg_root": "#0B0F19",          # Deep midnight navy
        "bg_sidebar": "#0E1526",       # Sidebar darker tone
        "bg_card": "#162032",          # Charcoal card surface
        "bg_card_secondary": "#1E2B42",# Slightly lighter card accent
        "bg_input": "#111827",         # Input background
        "border": "#24324D",           # Card borders
        "border_focus": "#8B5CF6",     # Accent border
        "text_primary": "#F8FAFC",     # Crisp white
        "text_secondary": "#94A3B8",   # Soft slate
        "text_muted": "#64748B",       # Muted slate
        "accent": "#8B5CF6",           # Vibrant violet/purple
        "accent_hover": "#7C3AED",     # Darker violet
        "accent_light": "#C4B5FD",     # Lavender
        "accent_dim": "#312E81",       # Dimmed purple for subtle badges
        "success": "#10B981",          # Emerald green
        "warning": "#F59E0B",          # Amber
        "danger": "#EF4444",           # Rose red
        "danger_hover": "#DC2626",
        "chart_bg": "#162032",
        "chart_bar": "#8B5CF6",
        "chart_bar_highlight": "#C4B5FD",
        "chart_line": "#10B981",
        "chart_grid": "#24324D",
        "chart_text": "#94A3B8",
    },
    "light": {
        "name": "Clean Lavender",
        "bg_root": "#F1F5F9",          # Soft light slate
        "bg_sidebar": "#FFFFFF",       # Pure white sidebar
        "bg_card": "#FFFFFF",          # Pure white card surface
        "bg_card_secondary": "#F8FAFC",# Very light slate accent
        "bg_input": "#F8FAFC",         # Light input background
        "border": "#E2E8F0",           # Subtle light border
        "border_focus": "#7C3AED",     # Purple focus
        "text_primary": "#0F172A",     # Deep charcoal text
        "text_secondary": "#475569",   # Medium slate
        "text_muted": "#94A3B8",       # Muted slate
        "accent": "#7C3AED",           # Soft deep purple
        "accent_hover": "#6D28D9",     # Darker purple
        "accent_light": "#DDD6FE",     # Soft lavender
        "accent_dim": "#EDE9FE",       # Very light purple tint
        "success": "#059669",          # Green
        "warning": "#D97706",          # Amber
        "danger": "#DC2626",           # Red
        "danger_hover": "#B91C1C",
        "chart_bg": "#FFFFFF",
        "chart_bar": "#7C3AED",
        "chart_bar_highlight": "#A78BFA",
        "chart_line": "#059669",
        "chart_grid": "#E2E8F0",
        "chart_text": "#475569",
    }
}


class SettingsManager:
    def __init__(self, db: Database):
        self.db = db
        self._listeners: List[Callable[[str, Any], None]] = []

    def get(self, key: str, default: Any = "") -> str:
        """Get a setting by key."""
        return self.db.get_setting(key, default)

    def set(self, key: str, value: Any):
        """Set a setting and notify registered listeners."""
        self.db.set_setting(key, str(value))
        for listener in self._listeners:
            try:
                listener(key, value)
            except Exception as e:
                print(f"Error in settings listener: {e}")

    def add_listener(self, callback: Callable[[str, Any], None]):
        """Register a callback for setting changes."""
        self._listeners.append(callback)

    @property
    def theme_name(self) -> str:
        return self.get("theme", "dark")

    @property
    def theme(self) -> Dict[str, str]:
        t_name = self.theme_name
        return THEMES.get(t_name, THEMES["dark"])

    @property
    def is_24h_format(self) -> bool:
        return self.get("time_format", "12") == "24"

    @property
    def sleep_goal_hours(self) -> float:
        try:
            return float(self.get("sleep_goal_hours", "8.0"))
        except ValueError:
            return 8.0

    @property
    def default_snooze_mins(self) -> int:
        try:
            return int(self.get("default_snooze_mins", "10"))
        except ValueError:
            return 10

    @property
    def default_alarm_volume(self) -> int:
        try:
            return int(self.get("default_alarm_volume", "80"))
        except ValueError:
            return 80

    @property
    def math_challenge_enabled(self) -> bool:
        return self.get("math_challenge_enabled", "1") == "1"

    @property
    def math_difficulty(self) -> str:
        return self.get("math_difficulty", "medium")

    @property
    def bedtime_hour(self) -> int:
        try:
            return int(self.get("bedtime_hour", "22"))
        except ValueError:
            return 22

    @property
    def bedtime_minute(self) -> int:
        try:
            return int(self.get("bedtime_minute", "30"))
        except ValueError:
            return 30

    @property
    def bedtime_reminder_enabled(self) -> bool:
        return self.get("bedtime_reminder_enabled", "1") == "1"

    @property
    def bedtime_reminder_lead_mins(self) -> int:
        try:
            return int(self.get("bedtime_reminder_lead_mins", "30"))
        except ValueError:
            return 30

    @property
    def user_name(self) -> str:
        return self.get("user_name", "Dileep")
