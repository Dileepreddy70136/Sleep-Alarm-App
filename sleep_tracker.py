"""
SleepSync - Sleep Tracker Module
Handles active sleep sessions, duration calculation (including midnight-crossing),
manual log creation, editing, deletion, and validation.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from database import Database


class SleepTracker:
    def __init__(self, db: Database):
        self.db = db
        self.on_records_changed: Optional[Callable[[], None]] = None

    # ==========================
    # ACTIVE SLEEP SESSION
    # ==========================

    def is_active_session(self) -> bool:
        """Check if a sleep session is currently active."""
        start_str = self.db.get_setting("active_sleep_start", "")
        return bool(start_str.strip())

    def get_active_session_start(self) -> Optional[datetime]:
        """Return the start datetime of current active sleep session."""
        start_str = self.db.get_setting("active_sleep_start", "").strip()
        if not start_str:
            return None
        try:
            return datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

    def start_sleep(self) -> datetime:
        """Start tracking an active sleep session."""
        now = datetime.now().replace(microsecond=0)
        self.db.set_setting("active_sleep_start", now.strftime("%Y-%m-%d %H:%M:%S"))
        if self.on_records_changed:
            self.on_records_changed()
        return now

    def cancel_active_sleep(self):
        """Discard the ongoing active sleep session."""
        self.db.set_setting("active_sleep_start", "")
        if self.on_records_changed:
            self.on_records_changed()

    def get_active_sleep_duration(self) -> Tuple[int, int]:
        """Return (hours, minutes) elapsed since active sleep started."""
        start = self.get_active_session_start()
        if not start:
            return (0, 0)
        now = datetime.now()
        delta = max(timedelta(0), now - start)
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        mins = (total_seconds % 3600) // 60
        return (hours, mins)

    def wake_up(self, quality_rating: int = 4, notes: str = "") -> Optional[Dict[str, Any]]:
        """
        End active sleep session, save record to database, and return saved record.
        """
        start = self.get_active_session_start()
        if not start:
            return None

        now = datetime.now().replace(microsecond=0)
        duration_minutes = (now - start).total_seconds() / 60.0

        if duration_minutes < 1.0:
            duration_minutes = 1.0

        record_id = self.db.create_sleep_record(
            start_time=start.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=now.strftime("%Y-%m-%d %H:%M:%S"),
            duration_minutes=round(duration_minutes, 1),
            quality_rating=quality_rating,
            notes=notes
        )

        # Clear active session
        self.db.set_setting("active_sleep_start", "")
        if self.on_records_changed:
            self.on_records_changed()

        return self.db.get_sleep_record_by_id(record_id)

    # ==========================
    # DURATION CALCULATION HELPER
    # ==========================

    @staticmethod
    def calculate_sleep_duration(bed_dt: datetime, wake_dt: datetime) -> float:
        """
        Calculate duration in minutes between bedtime and wake time.
        If wake_dt is before bed_dt (e.g. bed at 23:00, wake at 07:00 next day),
        adjust wake_dt by adding 1 day.
        """
        if wake_dt <= bed_dt:
            wake_dt += timedelta(days=1)
        duration_sec = (wake_dt - bed_dt).total_seconds()
        return max(0.0, round(duration_sec / 60.0, 1))

    # ==========================
    # MANUAL CRUD
    # ==========================

    def add_manual_record(self, bed_dt: datetime, wake_dt: datetime,
                          quality_rating: int = 4, notes: str = "") -> int:
        """Manually log a past sleep record with midnight-crossing handling."""
        if wake_dt <= bed_dt:
            wake_dt += timedelta(days=1)

        duration_mins = (wake_dt - bed_dt).total_seconds() / 60.0
        if duration_mins <= 0:
            raise ValueError("Sleep duration must be greater than 0.")

        rec_id = self.db.create_sleep_record(
            start_time=bed_dt.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=wake_dt.strftime("%Y-%m-%d %H:%M:%S"),
            duration_minutes=round(duration_mins, 1),
            quality_rating=quality_rating,
            notes=notes
        )
        if self.on_records_changed:
            self.on_records_changed()
        return rec_id

    def update_record(self, record_id: int, bed_dt: datetime, wake_dt: datetime,
                      quality_rating: int, notes: str):
        """Update an existing sleep record."""
        if wake_dt <= bed_dt:
            wake_dt += timedelta(days=1)

        duration_mins = (wake_dt - bed_dt).total_seconds() / 60.0
        if duration_mins <= 0:
            raise ValueError("Sleep duration must be greater than 0.")

        self.db.update_sleep_record(
            record_id=record_id,
            start_time=bed_dt.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=wake_dt.strftime("%Y-%m-%d %H:%M:%S"),
            duration_minutes=round(duration_mins, 1),
            quality_rating=quality_rating,
            notes=notes
        )
        if self.on_records_changed:
            self.on_records_changed()

    def delete_record(self, record_id: int):
        """Delete a sleep record."""
        self.db.delete_sleep_record(record_id)
        if self.on_records_changed:
            self.on_records_changed()

    def get_records(self, filter_mode: str = "all") -> List[Dict[str, Any]]:
        """
        Fetch records with optional filter: 'all', '7days', '30days'.
        """
        if filter_mode == "7days":
            return self.db.get_sleep_records_by_range(7)
        elif filter_mode == "30days":
            return self.db.get_sleep_records_by_range(30)
        else:
            return self.db.get_all_sleep_records()

    def get_today_sleep_minutes(self) -> float:
        """Calculate total sleep minutes logged ending today."""
        today_date_str = datetime.now().strftime("%Y-%m-%d")
        all_recs = self.db.get_all_sleep_records(limit=20)
        today_mins = 0.0
        for r in all_recs:
            if r["end_time"].startswith(today_date_str):
                today_mins += r["duration_minutes"]
        return today_mins
