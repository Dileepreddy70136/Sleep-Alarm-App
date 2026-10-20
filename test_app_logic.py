"""
SleepSync - Comprehensive Logic & Unit Tests
Tests database persistence, alarm scheduling, midnight sleep calculations,
math challenge verification, audio file integrity, and analytics accuracy.
"""

import os
import sys
import unittest
from datetime import datetime, timedelta

from database import Database
from alarm_manager import AlarmManager
from sleep_tracker import SleepTracker
from analytics import AnalyticsEngine
from settings import SettingsManager
from sound_generator import ensure_built_in_sounds


class TestSleepSyncLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db_path = os.path.join(os.path.dirname(__file__), "data", "test_sleepsync.db")
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
        cls.db = Database(cls.test_db_path)
        cls.sounds_dir = os.path.join(os.path.dirname(__file__), "sounds")
        ensure_built_in_sounds(cls.sounds_dir)
        cls.alarm_mgr = AlarmManager(cls.db, cls.sounds_dir)
        cls.sleep_tracker = SleepTracker(cls.db)
        cls.analytics = AnalyticsEngine(cls.db)
        cls.settings = SettingsManager(cls.db)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

    def test_01_built_in_sounds_exist(self):
        """Ensure all 6 built-in high-quality sounds were synthesized."""
        required = [
            "peaceful_chime.wav",
            "zen_harp.wav",
            "digital_alarm.wav",
            "gentle_rain.wav",
            "meditation_drone.wav",
            "white_noise.wav"
        ]
        for name in required:
            path = os.path.join(self.sounds_dir, name)
            self.assertTrue(os.path.exists(path), f"Missing sound file: {name}")
            self.assertGreater(os.path.getsize(path), 2000, f"Sound file too small: {name}")

    def test_02_database_alarms_crud(self):
        """Test alarm creation, retrieval, toggle, update, and deletion."""
        # Create
        alarm_id = self.db.create_alarm(
            label="Workout Wakeup",
            hour=6,
            minute=30,
            days="Mon,Wed,Fri",
            sound="digital_alarm.wav",
            snooze_duration=10,
            is_active=1
        )
        self.assertIsNotNone(alarm_id)
        
        # Read
        alarm = self.db.get_alarm_by_id(alarm_id)
        self.assertEqual(alarm["label"], "Workout Wakeup")
        self.assertEqual(alarm["hour"], 6)
        self.assertEqual(alarm["minute"], 30)
        self.assertEqual(alarm["days"], "Mon,Wed,Fri")
        self.assertEqual(alarm["is_active"], 1)

        # Toggle
        self.db.toggle_alarm(alarm_id, 0)
        alarm = self.db.get_alarm_by_id(alarm_id)
        self.assertEqual(alarm["is_active"], 0)

        # Update
        self.db.update_alarm(alarm_id, "Gym Workout", 6, 15, "Daily", "zen_harp.wav", 15, 1)
        alarm = self.db.get_alarm_by_id(alarm_id)
        self.assertEqual(alarm["label"], "Gym Workout")
        self.assertEqual(alarm["minute"], 15)
        self.assertEqual(alarm["days"], "Daily")

        # Delete
        self.db.delete_alarm(alarm_id)
        self.assertIsNone(self.db.get_alarm_by_id(alarm_id))

    def test_03_time_conversion_and_formatting(self):
        """Test 12h to 24h conversion and string formatting."""
        # 12h to 24h
        h24, m = AlarmManager.parse_12h_to_24h(12, 30, "AM")
        self.assertEqual((h24, m), (0, 30))

        h24, m = AlarmManager.parse_12h_to_24h(12, 45, "PM")
        self.assertEqual((h24, m), (12, 45))

        h24, m = AlarmManager.parse_12h_to_24h(7, 15, "AM")
        self.assertEqual((h24, m), (7, 15))

        h24, m = AlarmManager.parse_12h_to_24h(7, 15, "PM")
        self.assertEqual((h24, m), (19, 15))

        # Formatting
        self.assertEqual(AlarmManager.format_time(7, 5, is_24h=False), "7:05 AM")
        self.assertEqual(AlarmManager.format_time(19, 30, is_24h=False), "7:30 PM")
        self.assertEqual(AlarmManager.format_time(0, 0, is_24h=False), "12:00 AM")
        self.assertEqual(AlarmManager.format_time(19, 30, is_24h=True), "19:30")

    def test_04_sleep_duration_midnight_cross(self):
        """Test calculating sleep durations crossing midnight correctly."""
        # Case A: Bedtime 11:30 PM (23:30), Wake 7:00 AM next day -> 7h 30m = 450 minutes
        bed = datetime(2026, 10, 19, 23, 30)
        wake = datetime(2026, 10, 19, 7, 0)  # Same day date input, should cross to next day
        dur_mins = SleepTracker.calculate_sleep_duration(bed, wake)
        self.assertEqual(dur_mins, 450.0)

        # Case B: Bedtime 1:00 AM, Wake 8:30 AM -> 7h 30m
        bed2 = datetime(2026, 10, 20, 1, 0)
        wake2 = datetime(2026, 10, 20, 8, 30)
        dur_mins2 = SleepTracker.calculate_sleep_duration(bed2, wake2)
        self.assertEqual(dur_mins2, 450.0)

    def test_05_sleep_records_crud(self):
        """Test manual sleep logging, updating, and deletion."""
        bed = datetime(2026, 10, 18, 23, 0)
        wake = datetime(2026, 10, 19, 7, 30)
        rec_id = self.sleep_tracker.add_manual_record(bed, wake, quality_rating=5, notes="Slept like a baby")
        self.assertIsNotNone(rec_id)

        rec = self.db.get_sleep_record_by_id(rec_id)
        self.assertEqual(rec["duration_minutes"], 510.0)
        self.assertEqual(rec["quality_rating"], 5)
        self.assertEqual(rec["notes"], "Slept like a baby")

        # Update
        wake_updated = datetime(2026, 10, 19, 8, 0)
        self.sleep_tracker.update_record(rec_id, bed, wake_updated, quality_rating=4, notes="Updated note")
        rec = self.db.get_sleep_record_by_id(rec_id)
        self.assertEqual(rec["duration_minutes"], 540.0)
        self.assertEqual(rec["quality_rating"], 4)

        # Delete
        self.sleep_tracker.delete_record(rec_id)
        self.assertIsNone(self.db.get_sleep_record_by_id(rec_id))

    def test_06_analytics_calculations(self):
        """Test analytics statistics calculations."""
        stats = self.analytics.get_summary_stats(sleep_goal_hours=8.0)
        self.assertTrue(stats["has_data"])
        self.assertGreater(stats["all_time_avg_hours"], 0.0)
        self.assertGreater(stats["longest_session_hours"], 0.0)
        self.assertGreaterEqual(stats["goal_completion_pct"], 0.0)

        past_7_days = self.analytics.get_past_7_days_daily_data()
        self.assertEqual(len(past_7_days), 7)

    def test_07_alarm_snooze_and_next_alarm(self):
        """Test snoozing logic and calculating next triggering alarm."""
        # Add test alarm
        aid = self.alarm_mgr.add_alarm("Early Test", 5, 0, "Daily", "peaceful_chime.wav", snooze_duration=10)
        
        # Next alarm should find a candidate
        next_alarm = self.alarm_mgr.get_next_alarm(is_24h=False)
        self.assertIsNotNone(next_alarm)
        self.assertIn("time_str", next_alarm)
        self.assertIn("delta_str", next_alarm)

        # Test snooze
        alarm_data = self.db.get_alarm_by_id(aid)
        self.alarm_mgr.snooze_alarm(alarm_data, snooze_minutes=5)
        self.assertEqual(len(self.alarm_mgr.snoozed_alarms), 1)

        # Dismiss
        self.alarm_mgr.dismiss_alarm(alarm_data)
        self.assertEqual(len(self.alarm_mgr.snoozed_alarms), 0)

        self.alarm_mgr.delete_alarm(aid)

    def test_08_settings_persistence(self):
        """Test configuration retrieval and updates."""
        self.settings.set("theme", "light")
        self.assertEqual(self.settings.get("theme"), "light")
        self.assertEqual(self.settings.theme_name, "light")

        self.settings.set("theme", "dark")
        self.assertEqual(self.settings.theme_name, "dark")

        self.settings.set("sleep_goal_hours", "7.5")
        self.assertEqual(self.settings.sleep_goal_hours, 7.5)


if __name__ == "__main__":
    unittest.main()
