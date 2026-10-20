"""
SleepSync - Dashboard View
Main hub showing dynamic greeting, live clock, stat cards, quick actions,
embedded weekly sleep chart, upcoming bedtime, and recent history.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Dict, Any, Callable
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ui_components import CardFrame, StatCard, ModernButton, CustomProgressBar
from alarm_manager import AlarmManager
from sleep_tracker import SleepTracker
from analytics import AnalyticsEngine
from settings import SettingsManager


class DashboardView(tk.Frame):
    def __init__(self, parent, theme: Dict[str, str],
                 alarm_mgr: AlarmManager,
                 sleep_tracker: SleepTracker,
                 analytics_engine: AnalyticsEngine,
                 settings_mgr: SettingsManager,
                 nav_callback: Callable[[str], None],
                 on_start_sleep: Callable[[], None],
                 on_wake_up: Callable[[], None]):
        super().__init__(parent, bg=theme.get("bg_root", "#0B0F19"))
        self.theme = theme
        self.alarm_mgr = alarm_mgr
        self.sleep_tracker = sleep_tracker
        self.analytics_engine = analytics_engine
        self.settings_mgr = settings_mgr
        self.nav_callback = nav_callback
        self.on_start_sleep = on_start_sleep
        self.on_wake_up = on_wake_up

        self.chart_canvas = None
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Scrollable container or spacious frame
        canvas = tk.Canvas(self, bg=self["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_content = tk.Frame(canvas, bg=self["bg"])

        self.scrollable_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        self.canvas_window = canvas.create_window((0, 0), window=self.scrollable_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Ensure content frame resizes with canvas width
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(self.canvas_window, width=e.width)
        )

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        pad_container = tk.Frame(self.scrollable_content, bg=self["bg"], padx=25, pady=20)
        pad_container.pack(fill="both", expand=True)

        # ==========================================
        # 1. HEADER ROW: Greeting, Date, Live Clock
        # ==========================================
        header_row = tk.Frame(pad_container, bg=self["bg"])
        header_row.pack(fill="x", pady=(0, 20))

        # Greeting & Subtitle
        greeting_col = tk.Frame(header_row, bg=self["bg"])
        greeting_col.pack(side="left", anchor="w")

        self.greeting_label = tk.Label(
            greeting_col,
            text="Welcome to SleepSync",
            font=("Segoe UI", 22, "bold"),
            bg=self["bg"],
            fg=self.theme.get("text_primary", "#F8FAFC")
        )
        self.greeting_label.pack(anchor="w")

        self.date_label = tk.Label(
            greeting_col,
            text="",
            font=("Segoe UI", 11),
            bg=self["bg"],
            fg=self.theme.get("text_secondary", "#94A3B8")
        )
        self.date_label.pack(anchor="w", pady=(2, 0))

        # Digital Clock Pill Card (Right)
        clock_card = tk.Frame(
            header_row,
            bg=self.theme.get("bg_card", "#162032"),
            highlightbackground=self.theme.get("border", "#24324D"),
            highlightthickness=1,
            padx=18,
            pady=8
        )
        clock_card.pack(side="right", anchor="e")

        self.clock_label = tk.Label(
            clock_card,
            text="--:--:--",
            font=("Segoe UI", 20, "bold"),
            bg=clock_card["bg"],
            fg=self.theme.get("accent_light", "#C4B5FD")
        )
        self.clock_label.pack()

        # ==========================================
        # 2. STAT CARDS ROW (4 Cards)
        # ==========================================
        stats_row = tk.Frame(pad_container, bg=self["bg"])
        stats_row.pack(fill="x", pady=(0, 20))
        for i in range(4):
            stats_row.grid_columnconfigure(i, weight=1, uniform="stat_cards")

        # Stat 1: Next Alarm
        self.card_next_alarm = StatCard(
            stats_row, self.theme,
            icon="⏰", title="Next Alarm",
            value="--:--", subtitle="No alarms active",
            accent_color=self.theme.get("accent", "#8B5CF6")
        )
        self.card_next_alarm.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # Stat 2: Today's Sleep
        self.card_today_sleep = StatCard(
            stats_row, self.theme,
            icon="🌙", title="Today's Sleep",
            value="0.0h", subtitle="Goal: 8.0h",
            accent_color=self.theme.get("accent_light", "#C4B5FD")
        )
        self.card_today_sleep.grid(row=0, column=1, sticky="nsew", padx=4)

        # Stat 3: 7-Day Average
        self.card_weekly_avg = StatCard(
            stats_row, self.theme,
            icon="📊", title="7-Day Average",
            value="0.0h", subtitle="Past week records",
            accent_color=self.theme.get("success", "#10B981")
        )
        self.card_weekly_avg.grid(row=0, column=2, sticky="nsew", padx=4)

        # Stat 4: Goal Progress
        self.card_goal_progress = StatCard(
            stats_row, self.theme,
            icon="🎯", title="Goal Met",
            value="0%", subtitle="Adherence rate",
            accent_color=self.theme.get("warning", "#F59E0B")
        )
        self.card_goal_progress.grid(row=0, column=3, sticky="nsew", padx=(8, 0))

        # ==========================================
        # 3. QUICK ACTION BUTTONS BAR
        # ==========================================
        actions_card = CardFrame(pad_container, self.theme, padx=16, pady=12)
        actions_card.pack(fill="x", pady=(0, 20))

        tk.Label(
            actions_card,
            text="⚡ QUICK ACTIONS",
            font=("Segoe UI", 9, "bold"),
            bg=actions_card["bg"],
            fg=self.theme.get("text_muted", "#64748B")
        ).pack(side="left", padx=(0, 16))

        # Quick Action: Set Alarm
        ModernButton(
            actions_card, self.theme,
            text="⏰ Set Alarm",
            command=lambda: self.nav_callback("alarms"),
            variant="secondary"
        ).pack(side="left", padx=4)

        # Quick Action: Start/Stop Sleep
        self.btn_sleep_toggle = ModernButton(
            actions_card, self.theme,
            text="🌙 Start Sleep Session",
            command=self._handle_sleep_toggle,
            variant="primary"
        )
        self.btn_sleep_toggle.pack(side="left", padx=4)

        # Quick Action: Play Relaxing Music
        ModernButton(
            actions_card, self.theme,
            text="🎵 Relaxing Sounds",
            command=lambda: self.nav_callback("music"),
            variant="secondary"
        ).pack(side="left", padx=4)

        # ==========================================
        # 4. LOWER SPLIT: Chart (Left) + Bedtime & Recent (Right)
        # ==========================================
        split_row = tk.Frame(pad_container, bg=self["bg"])
        split_row.pack(fill="both", expand=True)
        split_row.grid_columnconfigure(0, weight=3)
        split_row.grid_columnconfigure(1, weight=2)

        # Left Column: Weekly Sleep Chart Card
        self.chart_card = CardFrame(split_row, self.theme, padx=14, pady=14)
        self.chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        chart_header = tk.Frame(self.chart_card, bg=self.chart_card["bg"])
        chart_header.pack(fill="x", pady=(0, 8))

        tk.Label(
            chart_header,
            text="📈 Weekly Sleep Duration (Hours)",
            font=("Segoe UI", 12, "bold"),
            bg=self.chart_card["bg"],
            fg=self.theme.get("text_primary", "#F8FAFC")
        ).pack(side="left")

        self.chart_container = tk.Frame(self.chart_card, bg=self.chart_card["bg"])
        self.chart_container.pack(fill="both", expand=True)

        # Right Column: Stacked Cards (Bedtime Reminder & Recent Sleep)
        right_col = tk.Frame(split_row, bg=self["bg"])
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # Bedtime Reminder Card
        bedtime_card = CardFrame(right_col, self.theme, padx=14, pady=12)
        bedtime_card.pack(fill="x", pady=(0, 12))

        tk.Label(
            bedtime_card,
            text="🌙 UPCOMING BEDTIME",
            font=("Segoe UI", 9, "bold"),
            bg=bedtime_card["bg"],
            fg=self.theme.get("text_muted", "#64748B")
        ).pack(anchor="w")

        self.bedtime_time_label = tk.Label(
            bedtime_card,
            text="10:30 PM",
            font=("Segoe UI", 16, "bold"),
            bg=bedtime_card["bg"],
            fg=self.theme.get("text_primary", "#F8FAFC")
        )
        self.bedtime_time_label.pack(anchor="w", pady=(4, 2))

        self.bedtime_info_label = tk.Label(
            bedtime_card,
            text="Wind down reminder active (30m before)",
            font=("Segoe UI", 9),
            bg=bedtime_card["bg"],
            fg=self.theme.get("accent_light", "#C4B5FD")
        )
        self.bedtime_info_label.pack(anchor="w")

        # Recent Sleep History Card
        self.recent_card = CardFrame(right_col, self.theme, padx=14, pady=12)
        self.recent_card.pack(fill="both", expand=True)

        recent_header = tk.Frame(self.recent_card, bg=self.recent_card["bg"])
        recent_header.pack(fill="x", pady=(0, 8))

        tk.Label(
            recent_header,
            text="📝 RECENT SLEEP LOGS",
            font=("Segoe UI", 9, "bold"),
            bg=self.recent_card["bg"],
            fg=self.theme.get("text_muted", "#64748B")
        ).pack(side="left")

        ModernButton(
            recent_header, self.theme,
            text="View All",
            command=lambda: self.nav_callback("sleep"),
            variant="secondary",
            font_size=8,
            padx=8,
            pady=2
        ).pack(side="right")

        self.recent_list_frame = tk.Frame(self.recent_card, bg=self.recent_card["bg"])
        self.recent_list_frame.pack(fill="both", expand=True)

    def _handle_sleep_toggle(self):
        if self.sleep_tracker.is_active_session():
            self.on_wake_up()
        else:
            self.on_start_sleep()
        self.refresh()

    def update_clock(self):
        """Update live clock text and dynamic greeting."""
        now = datetime.now()
        is_24h = self.settings_mgr.is_24h_format

        # Clock
        if is_24h:
            time_str = now.strftime("%H:%M:%S")
        else:
            time_str = now.strftime("%I:%M:%S %p")
        self.clock_label.configure(text=time_str)

        # Date
        date_str = now.strftime("%A, %B %d, %Y")
        self.date_label.configure(text=date_str)

        # Dynamic Greeting
        hour = now.hour
        user_name = self.settings_mgr.user_name
        if hour < 12:
            greet = f"Good morning, {user_name}! ☀️"
        elif hour < 17:
            greet = f"Good afternoon, {user_name}! 🌤️"
        elif hour < 21:
            greet = f"Good evening, {user_name}! 🌆"
        else:
            greet = f"Time to relax, {user_name}! 🌙"
        self.greeting_label.configure(text=greet)

    def refresh(self):
        """Refresh all statistics, next alarm, sleep chart, and recent items."""
        self.update_clock()
        is_24h = self.settings_mgr.is_24h_format
        goal = self.settings_mgr.sleep_goal_hours

        # 1. Next Alarm
        next_alarm = self.alarm_mgr.get_next_alarm(is_24h)
        if next_alarm:
            self.card_next_alarm.update_data(
                value=next_alarm["time_str"],
                subtitle=f"{next_alarm['label']} ({next_alarm['delta_str']})"
            )
        else:
            self.card_next_alarm.update_data(
                value="--:--",
                subtitle="No alarms active"
            )

        # 2. Stats
        stats = self.analytics_engine.get_summary_stats(goal)
        today_h = stats["today_sleep_hours"]
        self.card_today_sleep.update_data(
            value=f"{today_h}h",
            subtitle=f"Goal: {goal}h ({int((today_h / goal) * 100)}%)" if goal > 0 else f"{today_h}h"
        )
        self.card_weekly_avg.update_data(
            value=f"{stats['weekly_avg_hours']}h",
            subtitle="7-day nightly average"
        )
        self.card_goal_progress.update_data(
            value=f"{stats['goal_completion_pct']}%",
            subtitle=f"{stats['total_nights_logged']} total nights logged"
        )

        # 3. Active Sleep Button State
        if self.sleep_tracker.is_active_session():
            hours, mins = self.sleep_tracker.get_active_sleep_duration()
            self.btn_sleep_toggle.configure(
                text=f"☀️ Wake Up ({hours}h {mins}m)",
                bg=self.theme.get("success", "#10B981")
            )
        else:
            self.btn_sleep_toggle.configure(
                text="🌙 Start Sleep Session",
                bg=self.theme.get("accent", "#8B5CF6")
            )

        # 4. Bedtime Card
        b_hour = self.settings_mgr.bedtime_hour
        b_min = self.settings_mgr.bedtime_minute
        b_str = AlarmManager.format_time(b_hour, b_min, is_24h)
        self.bedtime_time_label.configure(text=b_str)

        lead = self.settings_mgr.bedtime_reminder_lead_mins
        is_rem_enabled = self.settings_mgr.bedtime_reminder_enabled
        if is_rem_enabled:
            self.bedtime_info_label.configure(
                text=f"Wind down reminder active ({lead}m before)",
                fg=self.theme.get("accent_light", "#C4B5FD")
            )
        else:
            self.bedtime_info_label.configure(
                text="Bedtime reminder is currently disabled",
                fg=self.theme.get("text_muted", "#64748B")
            )

        # 5. Render Weekly Chart
        self._render_chart()

        # 6. Render Recent Logs
        self._render_recent_logs()

    def _render_chart(self):
        """Draw embedded Matplotlib bar chart."""
        # Clean up existing chart canvas
        for child in self.chart_container.winfo_children():
            child.destroy()

        try:
            goal = self.settings_mgr.sleep_goal_hours
            fig = self.analytics_engine.create_weekly_chart_figure(self.theme, sleep_goal=goal, width=5.6, height=2.6)
            self.chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
            self.chart_canvas.draw()
            self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)
        except Exception as e:
            print(f"Error rendering dashboard chart: {e}")

    def _render_recent_logs(self):
        """Populate recent sleep entries list."""
        for child in self.recent_list_frame.winfo_children():
            child.destroy()

        records = self.sleep_tracker.get_records(filter_mode="all")[:3]
        if not records:
            empty_lbl = tk.Label(
                self.recent_list_frame,
                text="No sleep records logged yet.",
                font=("Segoe UI", 9),
                bg=self.recent_card["bg"],
                fg=self.theme.get("text_muted", "#64748B"),
                pady=10
            )
            empty_lbl.pack()
            return

        for r in records:
            item_row = tk.Frame(
                self.recent_list_frame,
                bg=self.theme.get("bg_card_secondary", "#1E2B42"),
                padx=8,
                pady=6
            )
            item_row.pack(fill="x", pady=2)

            # Date and hours
            try:
                start_dt = datetime.strptime(r["start_time"], "%Y-%m-%d %H:%M:%S")
                date_str = start_dt.strftime("%b %d")
            except Exception:
                date_str = "Recent"

            dur_hours = round(r["duration_minutes"] / 60.0, 1)
            stars = "★" * int(r.get("quality_rating", 4))

            tk.Label(
                item_row,
                text=f"{date_str} • {dur_hours}h",
                font=("Segoe UI", 9, "bold"),
                bg=item_row["bg"],
                fg=self.theme.get("text_primary", "#F8FAFC")
            ).pack(side="left")

            tk.Label(
                item_row,
                text=stars,
                font=("Segoe UI", 8),
                bg=item_row["bg"],
                fg=self.theme.get("warning", "#F59E0B")
            ).pack(side="right")
