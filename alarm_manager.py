"""
SleepSync - Alarm Manager Module
Handles alarm scheduling, repetition logic, next alarm calculation, snooze management,
and non-blocking minute-precision triggering.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Tuple
import pygame
from database import Database

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class AlarmManager:
    def __init__(self, db: Database, sounds_dir: str):
        self.db = db
        self.sounds_dir = sounds_dir
        
        # Track last triggered minute string per alarm ID to prevent duplicate fires
        # e.g., self._last_triggered[alarm_id] = "2026-10-20 07:00"
        self._last_triggered: Dict[int, str] = {}
        
        # Snooze list: list of dicts: {"alarm_id": int, "trigger_time": datetime, "alarm_data": dict}
        self.snoozed_alarms: List[Dict[str, Any]] = []
        
        # Audio playback for currently firing alarm
        self._alarm_sound_playing: bool = False
        self._alarm_sound_channel: Optional[pygame.mixer.Channel] = None
        self._loaded_sound: Optional[pygame.mixer.Sound] = None
        
        # Callback when alarm triggers: fn(alarm_dict)
        self.on_alarm_trigger: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_alarms_changed: Optional[Callable[[], None]] = None

    # ==========================
    # TIME FORMATTING UTILS
    # ==========================

    @staticmethod
    def format_time(hour: int, minute: int, is_24h: bool = False) -> str:
        """Format hour and minute into 12-hour or 24-hour string."""
        if is_24h:
            return f"{hour:02d}:{minute:02d}"
        else:
            period = "AM" if hour < 12 else "PM"
            disp_hour = hour % 12
            if disp_hour == 0:
                disp_hour = 12
            return f"{disp_hour}:{minute:02d} {period}"

    @staticmethod
    def parse_12h_to_24h(hour_12: int, minute: int, am_pm: str) -> Tuple[int, int]:
        """Convert 12-hour components to 24-hour (hour, minute)."""
        am_pm = am_pm.upper()
        if am_pm == "AM":
            hour_24 = 0 if hour_12 == 12 else hour_12
        else:
            hour_24 = 12 if hour_12 == 12 else hour_12 + 12
        return hour_24, minute

    # ==========================
    # CRUD OPERATIONS
    # ==========================

    def get_alarms(self) -> List[Dict[str, Any]]:
        return self.db.get_all_alarms()

    def add_alarm(self, label: str, hour: int, minute: int, days: str,
                  sound: str, snooze_duration: int = 10, is_active: int = 1) -> int:
        alarm_id = self.db.create_alarm(label, hour, minute, days, sound, snooze_duration, is_active)
        if self.on_alarms_changed:
            self.on_alarms_changed()
        return alarm_id

    def update_alarm(self, alarm_id: int, label: str, hour: int, minute: int,
                     days: str, sound: str, snooze_duration: int, is_active: int):
        self.db.update_alarm(alarm_id, label, hour, minute, days, sound, snooze_duration, is_active)
        if self.on_alarms_changed:
            self.on_alarms_changed()

    def toggle_alarm(self, alarm_id: int, is_active: int):
        self.db.toggle_alarm(alarm_id, is_active)
        if self.on_alarms_changed:
            self.on_alarms_changed()

    def delete_alarm(self, alarm_id: int):
        self.db.delete_alarm(alarm_id)
        # Also clean up any active snoozes for this alarm
        self.snoozed_alarms = [s for s in self.snoozed_alarms if s.get("alarm_id") != alarm_id]
        if self.on_alarms_changed:
            self.on_alarms_changed()

    # ==========================
    # NEXT ALARM CALCULATION
    # ==========================

    def get_next_alarm(self, is_24h: bool = False) -> Optional[Dict[str, Any]]:
        """
        Calculates the earliest next triggering alarm (including snoozes).
        Returns a dictionary with time_str, label, delta_str, or None if no active alarms.
        """
        now = datetime.now()
        candidates: List[Tuple[datetime, Dict[str, Any]]] = []

        # 1. Check snoozed alarms
        for snooze in self.snoozed_alarms:
            t = snooze["trigger_time"]
            if t > now:
                candidates.append((t, snooze["alarm_data"]))

        # 2. Check scheduled database alarms
        active_alarms = [a for a in self.get_alarms() if a["is_active"] == 1]
        for alarm in active_alarms:
            next_dt = self._calculate_next_occurrence(alarm, now)
            if next_dt:
                candidates.append((next_dt, alarm))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0])
        earliest_dt, alarm_data = candidates[0]

        delta = earliest_dt - now
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours > 24:
            days = hours // 24
            rem_hours = hours % 24
            delta_str = f"In {days}d {rem_hours}h"
        elif hours > 0:
            delta_str = f"In {hours}h {minutes}m"
        else:
            delta_str = f"In {max(1, minutes)}m"

        return {
            "datetime": earliest_dt,
            "time_str": self.format_time(earliest_dt.hour, earliest_dt.minute, is_24h),
            "label": alarm_data.get("label", "Alarm"),
            "delta_str": delta_str,
            "alarm_data": alarm_data
        }

    def _calculate_next_occurrence(self, alarm: Dict[str, Any], from_dt: datetime) -> Optional[datetime]:
        """Compute the next datetime this alarm will trigger based on its days pattern."""
        days_str = alarm.get("days", "Daily")
        hour = alarm["hour"]
        minute = alarm["minute"]

        if days_str == "Once":
            # Today at hour:minute if still in future, otherwise tomorrow
            candidate = from_dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if candidate <= from_dt:
                candidate += timedelta(days=1)
            return candidate

        # Parse active weekdays
        if days_str == "Daily":
            active_days = set(range(7))
        else:
            day_tokens = [d.strip() for d in days_str.split(",") if d.strip()]
            active_days = set()
            for token in day_tokens:
                if token in DAY_NAMES:
                    active_days.add(DAY_NAMES.index(token))

        if not active_days:
            active_days = set(range(7))

        # Check up to 8 days in the future
        for offset in range(8):
            test_date = (from_dt + timedelta(days=offset)).date()
            if test_date.weekday() in active_days:
                candidate = datetime(test_date.year, test_date.month, test_date.day, hour, minute)
                if candidate > from_dt:
                    return candidate

        return None

    # ==========================
    # SCHEDULER TICK (NON-BLOCKING)
    # ==========================

    def check_alarms(self):
        """
        Called once every second by Tkinter root.after() loop.
        Non-blocking, checks if any alarm or snooze should trigger right now.
        """
        now = datetime.now()
        current_minute_str = now.strftime("%Y-%m-%d %H:%M")
        current_weekday = now.weekday()  # 0=Mon, 6=Sun
        current_hour = now.hour
        current_minute = now.minute

        # 1. Check Snoozed Alarms
        triggered_snoozes = []
        for snooze in self.snoozed_alarms:
            if now >= snooze["trigger_time"]:
                triggered_snoozes.append(snooze)

        for snooze in triggered_snoozes:
            self.snoozed_alarms.remove(snooze)
            alarm_data = snooze["alarm_data"].copy()
            alarm_data["is_snoozed_fire"] = True
            self._trigger_alarm(alarm_data)

        # 2. Check Database Alarms
        active_alarms = [a for a in self.get_alarms() if a["is_active"] == 1]
        for alarm in active_alarms:
            alarm_id = alarm["id"]

            # If already triggered during this minute, skip to prevent multi-fire
            if self._last_triggered.get(alarm_id) == current_minute_str:
                continue

            # Check hour and minute match
            if alarm["hour"] == current_hour and alarm["minute"] == current_minute:
                days_str = alarm.get("days", "Daily")
                should_trigger = False

                if days_str == "Once":
                    should_trigger = True
                    # Deactivate 'Once' alarm after it fires
                    self.toggle_alarm(alarm_id, 0)
                elif days_str == "Daily":
                    should_trigger = True
                else:
                    active_day_names = [d.strip() for d in days_str.split(",") if d.strip()]
                    if DAY_NAMES[current_weekday] in active_day_names:
                        should_trigger = True

                if should_trigger:
                    self._last_triggered[alarm_id] = current_minute_str
                    self._trigger_alarm(alarm)

    def _trigger_alarm(self, alarm_data: Dict[str, Any]):
        """Trigger an alarm event and start audio loop."""
        self.play_alarm_sound(alarm_data.get("sound", "peaceful_chime.wav"))
        if self.on_alarm_trigger:
            self.on_alarm_trigger(alarm_data)

    # ==========================
    # SNOOZE AND DISMISS
    # ==========================

    def snooze_alarm(self, alarm_data: Dict[str, Any], snooze_minutes: Optional[int] = None):
        """Snooze an alarm for N minutes."""
        self.stop_alarm_sound()
        mins = snooze_minutes if snooze_minutes is not None else alarm_data.get("snooze_duration", 10)
        mins = max(1, mins)
        trigger_time = datetime.now() + timedelta(minutes=mins)

        self.snoozed_alarms.append({
            "alarm_id": alarm_data.get("id"),
            "trigger_time": trigger_time,
            "alarm_data": alarm_data
        })

        if self.on_alarms_changed:
            self.on_alarms_changed()

    def dismiss_alarm(self, alarm_data: Dict[str, Any]):
        """Dismiss an active alarm."""
        self.stop_alarm_sound()
        # Remove any lingering snooze for this alarm
        aid = alarm_data.get("id")
        self.snoozed_alarms = [s for s in self.snoozed_alarms if s.get("alarm_id") != aid]
        if self.on_alarms_changed:
            self.on_alarms_changed()

    # ==========================
    # AUDIO PLAYBACK
    # ==========================

    def play_alarm_sound(self, sound_name: str, volume: float = 0.85):
        """Play alarm audio in a continuous loop."""
        self.stop_alarm_sound()

        # Resolve path
        if os.path.isabs(sound_name) and os.path.exists(sound_name):
            audio_path = sound_name
        else:
            audio_path = os.path.join(self.sounds_dir, sound_name)
            if not os.path.exists(audio_path):
                # Fallback to any available sound
                fallback = os.path.join(self.sounds_dir, "peaceful_chime.wav")
                audio_path = fallback if os.path.exists(fallback) else sound_name

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            self._loaded_sound = pygame.mixer.Sound(audio_path)
            self._loaded_sound.set_volume(max(0.1, min(1.0, volume)))
            # Play in infinite loop until stopped
            self._alarm_sound_channel = self._loaded_sound.play(loops=-1)
            self._alarm_sound_playing = True
        except Exception as e:
            print(f"Warning: Could not play alarm sound '{audio_path}': {e}")

    def stop_alarm_sound(self):
        """Stop alarm audio playback."""
        try:
            if self._alarm_sound_channel:
                self._alarm_sound_channel.stop()
            if self._loaded_sound:
                self._loaded_sound.stop()
        except Exception:
            pass
        self._alarm_sound_playing = False
        self._alarm_sound_channel = None
        self._loaded_sound = None

    def preview_sound(self, sound_name: str, volume: float = 0.8):
        """Play sound once for 3 seconds as a preview."""
        self.stop_alarm_sound()
        if os.path.isabs(sound_name) and os.path.exists(sound_name):
            audio_path = sound_name
        else:
            audio_path = os.path.join(self.sounds_dir, sound_name)

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            snd = pygame.mixer.Sound(audio_path)
            snd.set_volume(max(0.1, min(1.0, volume)))
            snd.play(loops=0)
        except Exception as e:
            print(f"Error previewing sound: {e}")
