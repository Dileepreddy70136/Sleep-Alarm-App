"""
SleepSync - Database Access Layer
SQLite database operations with parameterized queries and thread-safe connections.
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sleepsync.db")


class Database:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Create and return a new SQLite connection with row factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Initialize database schema with required tables and default settings."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Alarms Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alarms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    label TEXT NOT NULL,
                    hour INTEGER NOT NULL,
                    minute INTEGER NOT NULL,
                    days TEXT NOT NULL,
                    sound TEXT NOT NULL,
                    snooze_duration INTEGER DEFAULT 10,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 2. Sleep Records Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sleep_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    duration_minutes REAL NOT NULL,
                    quality_rating INTEGER DEFAULT 4,
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 3. Settings Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            
            # Default Settings
            default_settings = {
                "theme": "dark",
                "time_format": "12",  # '12' or '24'
                "sleep_goal_hours": "8.0",
                "default_snooze_mins": "10",
                "default_alarm_volume": "80",
                "math_challenge_enabled": "1",  # '1' or '0'
                "math_difficulty": "medium",    # 'easy', 'medium', 'hard'
                "bedtime_hour": "22",           # 10 PM
                "bedtime_minute": "30",
                "bedtime_reminder_enabled": "1",
                "bedtime_reminder_lead_mins": "30",
                "user_name": "Dileep",
                "active_sleep_start": "",       # If currently tracking an ongoing sleep session
            }

            for key, val in default_settings.items():
                cursor.execute("""
                    INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
                """, (key, val))

            conn.commit()

        # Seed sample sleep data if database is fresh to showcase realistic dashboard
        self._seed_sample_sleep_records_if_empty()

    def _seed_sample_sleep_records_if_empty(self):
        """Seed realistic sleep data for the past 7 days if no sleep records exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sleep_records")
            count = cursor.fetchone()[0]
            if count == 0:
                now = datetime.now()
                # Realistic sleep samples over past 7 nights
                sample_nights = [
                    (7, 23, 15, 7, 10, 4, "Felt rested and energized"),
                    (6, 23, 45, 6, 50, 3, "Woke up briefly around 3 AM"),
                    (5, 22, 50, 7, 30, 5, "Deep sleep, peaceful night"),
                    (4, 23, 30, 7, 0, 4, "Consistent routine"),
                    (3, 0, 15, 8, 0, 4, "Weekend recovery sleep"),
                    (2, 23, 10, 7, 20, 5, "Fell asleep very fast with rain sounds"),
                    (1, 22, 45, 7, 15, 4, "Refreshed morning"),
                ]
                for days_ago, b_hr, b_min, w_hr, w_min, quality, notes in sample_nights:
                    # Bedtime is (days_ago) nights ago
                    bed_date = (now - timedelta(days=days_ago)).date()
                    bed_dt = datetime(bed_date.year, bed_date.month, bed_date.day, b_hr, b_min)
                    
                    # Wake time is next morning
                    if b_hr >= 12:
                        wake_date = bed_date + timedelta(days=1)
                    else:
                        wake_date = bed_date
                    wake_dt = datetime(wake_date.year, wake_date.month, wake_date.day, w_hr, w_min)
                    
                    duration_mins = (wake_dt - bed_dt).total_seconds() / 60.0
                    cursor.execute("""
                        INSERT INTO sleep_records (start_time, end_time, duration_minutes, quality_rating, notes)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        bed_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        wake_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        duration_mins,
                        quality,
                        notes
                    ))

                # Also add default sample alarms if empty
                cursor.execute("SELECT COUNT(*) FROM alarms")
                alarm_count = cursor.fetchone()[0]
                if alarm_count == 0:
                    cursor.execute("""
                        INSERT INTO alarms (label, hour, minute, days, sound, snooze_duration, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, ("Morning Rise", 7, 0, "Mon,Tue,Wed,Thu,Fri", "peaceful_chime.wav", 10, 1))
                    cursor.execute("""
                        INSERT INTO alarms (label, hour, minute, days, sound, snooze_duration, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, ("Weekend Brunch", 8, 30, "Sat,Sun", "zen_harp.wav", 15, 1))

                conn.commit()

    # ==========================
    # SETTINGS OPERATIONS
    # ==========================

    def get_setting(self, key: str, default: Any = "") -> str:
        """Fetch a setting value by key with fallback default."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else str(default)

    def set_setting(self, key: str, value: Any):
        """Set or update a configuration key."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, str(value)))
            conn.commit()

    def get_all_settings(self) -> Dict[str, str]:
        """Fetch all key-value settings as a dictionary."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            return {row["key"]: row["value"] for row in cursor.fetchall()}

    # ==========================
    # ALARMS OPERATIONS
    # ==========================

    def get_all_alarms(self) -> List[Dict[str, Any]]:
        """Fetch all alarms sorted by hour and minute."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM alarms ORDER BY hour ASC, minute ASC")
            return [dict(row) for row in cursor.fetchall()]

    def get_alarm_by_id(self, alarm_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single alarm by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM alarms WHERE id = ?", (alarm_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_alarm(self, label: str, hour: int, minute: int, days: str,
                     sound: str, snooze_duration: int = 10, is_active: int = 1) -> int:
        """Create a new alarm record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO alarms (label, hour, minute, days, sound, snooze_duration, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (label.strip() or "Alarm", hour, minute, days, sound, snooze_duration, is_active))
            conn.commit()
            return cursor.lastrowid

    def update_alarm(self, alarm_id: int, label: str, hour: int, minute: int,
                     days: str, sound: str, snooze_duration: int, is_active: int):
        """Update an existing alarm record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE alarms
                SET label = ?, hour = ?, minute = ?, days = ?, sound = ?,
                    snooze_duration = ?, is_active = ?
                WHERE id = ?
            """, (label.strip() or "Alarm", hour, minute, days, sound, snooze_duration, is_active, alarm_id))
            conn.commit()

    def toggle_alarm(self, alarm_id: int, is_active: int):
        """Toggle an alarm's active state (1 for active, 0 for inactive)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE alarms SET is_active = ? WHERE id = ?", (is_active, alarm_id))
            conn.commit()

    def delete_alarm(self, alarm_id: int):
        """Delete an alarm record by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM alarms WHERE id = ?", (alarm_id,))
            conn.commit()

    # ==========================
    # SLEEP RECORDS OPERATIONS
    # ==========================

    def get_all_sleep_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch sleep records ordered by start_time descending."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM sleep_records ORDER BY start_time DESC"
            if limit:
                query += f" LIMIT {int(limit)}"
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def get_sleep_records_by_range(self, days: int = 7) -> List[Dict[str, Any]]:
        """Fetch sleep records from the past N days."""
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d 00:00:00")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sleep_records
                WHERE start_time >= ?
                ORDER BY start_time ASC
            """, (cutoff,))
            return [dict(row) for row in cursor.fetchall()]

    def get_sleep_record_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a specific sleep record by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sleep_records WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_sleep_record(self, start_time: str, end_time: str,
                            duration_minutes: float, quality_rating: int = 4,
                            notes: str = "") -> int:
        """Create a new sleep log entry."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sleep_records (start_time, end_time, duration_minutes, quality_rating, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (start_time, end_time, duration_minutes, quality_rating, notes.strip()))
            conn.commit()
            return cursor.lastrowid

    def update_sleep_record(self, record_id: int, start_time: str, end_time: str,
                            duration_minutes: float, quality_rating: int, notes: str):
        """Update an existing sleep log entry."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sleep_records
                SET start_time = ?, end_time = ?, duration_minutes = ?,
                    quality_rating = ?, notes = ?
                WHERE id = ?
            """, (start_time, end_time, duration_minutes, quality_rating, notes.strip(), record_id))
            conn.commit()

    def delete_sleep_record(self, record_id: int):
        """Delete a sleep record by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sleep_records WHERE id = ?", (record_id,))
            conn.commit()
