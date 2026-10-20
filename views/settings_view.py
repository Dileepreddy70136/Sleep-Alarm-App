"""
SleepSync - Settings View
Configure themes, time formats, bedtime reminders, math challenge puzzle,
default volumes, and application information.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable

from ui_components import CardFrame, ModernButton, ToggleSwitch, MathChallengeDialog, BedtimeReminderDialog
from settings import SettingsManager, THEMES
from alarm_manager import AlarmManager


class SettingsView(tk.Frame):
    def __init__(self, parent, theme: Dict[str, str],
                 settings_mgr: SettingsManager,
                 on_theme_changed: Callable[[str], None]):
        super().__init__(parent, bg=theme.get("bg_root", "#0B0F19"))
        self.theme = theme
        self.settings_mgr = settings_mgr
        self.on_theme_changed = on_theme_changed

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Scrollable container
        canvas = tk.Canvas(self, bg=self["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scroll_content = tk.Frame(canvas, bg=self["bg"])

        self.scroll_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        self.canvas_win = canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(self.canvas_win, width=e.width)
        )

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        pad_container = tk.Frame(self.scroll_content, bg=self["bg"], padx=25, pady=20)
        pad_container.pack(fill="both", expand=True)

        # Header Row
        header = tk.Frame(pad_container, bg=self["bg"])
        header.pack(fill="x", pady=(0, 16))

        tk.Label(
            header,
            text="⚙️ Preferences & Settings",
            font=("Segoe UI", 20, "bold"),
            bg=self["bg"],
            fg=self.theme.get("text_primary", "#F8FAFC")
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Customize themes, alarm defaults, bedtime notifications, and wake-up challenges",
            font=("Segoe UI", 10),
            bg=self["bg"],
            fg=self.theme.get("text_secondary", "#94A3B8")
        ).pack(anchor="w", pady=(2, 0))

        # 1. APPEARANCE & THEME CARD
        card_theme = CardFrame(pad_container, self.theme, padx=18, pady=14)
        card_theme.pack(fill="x", pady=(0, 14))

        tk.Label(card_theme, text="🎨 APPEARANCE & THEME", font=("Segoe UI", 9, "bold"), bg=card_theme["bg"], fg=self.theme.get("text_muted", "#64748B")).pack(anchor="w", pady=(0, 8))

        theme_row = tk.Frame(card_theme, bg=card_theme["bg"])
        theme_row.pack(fill="x")

        self.var_theme = tk.StringVar(value=self.settings_mgr.theme_name)
        for t_key, t_info in [("dark", "🌙 Modern Dark Navy"), ("light", "☀️ Clean Lavender Light")]:
            rb = tk.Radiobutton(
                theme_row,
                text=t_info,
                value=t_key,
                variable=self.var_theme,
                command=self._on_theme_select,
                bg=card_theme["bg"],
                fg=self.theme.get("text_primary", "#F8FAFC"),
                selectcolor=self.theme.get("bg_input", "#111827"),
                activebackground=card_theme["bg"],
                activeforeground=self.theme.get("text_primary", "#F8FAFC"),
                font=("Segoe UI", 10)
            )
            rb.pack(side="left", padx=(0, 20))

        # 2. TIME FORMAT & ALARM DEFAULTS CARD
        card_alarm = CardFrame(pad_container, self.theme, padx=18, pady=14)
        card_alarm.pack(fill="x", pady=(0, 14))

        tk.Label(card_alarm, text="⏰ CLOCK & ALARM PREFERENCES", font=("Segoe UI", 9, "bold"), bg=card_alarm["bg"], fg=self.theme.get("text_muted", "#64748B")).pack(anchor="w", pady=(0, 10))

        # Clock format row
        row_fmt = tk.Frame(card_alarm, bg=card_alarm["bg"])
        row_fmt.pack(fill="x", pady=(0, 8))

        tk.Label(row_fmt, text="Time Display Format:", font=("Segoe UI", 9), bg=card_alarm["bg"], fg=self.theme.get("text_secondary", "#94A3B8"), width=20, anchor="w").pack(side="left")

        self.var_fmt = tk.StringVar(value="24" if self.settings_mgr.is_24h_format else "12")
        tk.Radiobutton(row_fmt, text="12-Hour (AM/PM)", value="12", variable=self.var_fmt, bg=card_alarm["bg"], fg=self.theme.get("text_primary", "#F8FAFC"), selectcolor=self.theme.get("bg_input", "#111827"), activebackground=card_alarm["bg"], activeforeground=self.theme.get("text_primary", "#F8FAFC")).pack(side="left", padx=4)
        tk.Radiobutton(row_fmt, text="24-Hour Military", value="24", variable=self.var_fmt, bg=card_alarm["bg"], fg=self.theme.get("text_primary", "#F8FAFC"), selectcolor=self.theme.get("bg_input", "#111827"), activebackground=card_alarm["bg"], activeforeground=self.theme.get("text_primary", "#F8FAFC")).pack(side="left", padx=10)

        # Default snooze row
        row_snz = tk.Frame(card_alarm, bg=card_alarm["bg"])
        row_snz.pack(fill="x", pady=(0, 8))

        tk.Label(row_snz, text="Default Snooze Duration:", font=("Segoe UI", 9), bg=card_alarm["bg"], fg=self.theme.get("text_secondary", "#94A3B8"), width=20, anchor="w").pack(side="left")

        self.var_default_snooze = tk.StringVar(value=str(self.settings_mgr.default_snooze_mins))
        ttk.Combobox(row_snz, textvariable=self.var_default_snooze, values=["5", "10", "15", "20"], width=6, state="readonly").pack(side="left")
        tk.Label(row_snz, text=" minutes", font=("Segoe UI", 9), bg=card_alarm["bg"], fg=self.theme.get("text_secondary", "#94A3B8")).pack(side="left")

        # Default alarm volume
        row_vol = tk.Frame(card_alarm, bg=card_alarm["bg"])
        row_vol.pack(fill="x")

        tk.Label(row_vol, text="Default Alarm Volume:", font=("Segoe UI", 9), bg=card_alarm["bg"], fg=self.theme.get("text_secondary", "#94A3B8"), width=20, anchor="w").pack(side="left")

        self.slider_alarm_vol = ttk.Scale(row_vol, from_=10, to=100, orient="horizontal", length=140)
        self.slider_alarm_vol.set(self.settings_mgr.default_alarm_volume)
        self.slider_alarm_vol.pack(side="left", padx=(0, 8))

        self.lbl_alarm_vol_val = tk.Label(row_vol, text=f"{self.settings_mgr.default_alarm_volume}%", font=("Segoe UI", 9, "bold"), bg=card_alarm["bg"], fg=self.theme.get("text_primary", "#F8FAFC"))
        self.lbl_alarm_vol_val.pack(side="left")
        self.slider_alarm_vol.configure(command=lambda v: self.lbl_alarm_vol_val.configure(text=f"{int(float(v))}%"))

        # 3. WAKE-UP MATH CHALLENGE CARD
        card_math = CardFrame(pad_container, self.theme, padx=18, pady=14)
        card_math.pack(fill="x", pady=(0, 14))

        m_head = tk.Frame(card_math, bg=card_math["bg"])
        m_head.pack(fill="x", pady=(0, 8))

        tk.Label(m_head, text="🧠 WAKE-UP MATHEMATICAL CHALLENGE", font=("Segoe UI", 9, "bold"), bg=card_math["bg"], fg=self.theme.get("text_muted", "#64748B")).pack(side="left")

        # Toggle Switch
        self.math_toggle = ToggleSwitch(
            m_head,
            self.theme,
            is_on=self.settings_mgr.math_challenge_enabled,
            command=self._on_math_toggle,
            width=46,
            height=24
        )
        self.math_toggle.pack(side="right")

        tk.Label(
            card_math,
            text="Forces mental alertness before dismissing an alarm. Prevents accidental sleep-ins.",
            font=("Segoe UI", 9),
            bg=card_math["bg"],
            fg=self.theme.get("text_secondary", "#94A3B8")
        ).pack(anchor="w", pady=(0, 8))

        diff_row = tk.Frame(card_math, bg=card_math["bg"])
        diff_row.pack(fill="x")

        tk.Label(diff_row, text="Difficulty Level:", font=("Segoe UI", 9), bg=card_math["bg"], fg=self.theme.get("text_secondary", "#94A3B8"), width=15, anchor="w").pack(side="left")

        self.var_diff = tk.StringVar(value=self.settings_mgr.math_difficulty)
        ttk.Combobox(diff_row, textvariable=self.var_diff, values=["easy", "medium", "hard"], width=10, state="readonly").pack(side="left", padx=(0, 14))

        ModernButton(diff_row, self.theme, text="Test Challenge Dialog", command=self._test_math_dialog, variant="secondary", font_size=9, padx=10, pady=2).pack(side="left")

        # 4. BEDTIME REMINDER PREFERENCES CARD
        card_bedtime = CardFrame(pad_container, self.theme, padx=18, pady=14)
        card_bedtime.pack(fill="x", pady=(0, 14))

        b_head = tk.Frame(card_bedtime, bg=card_bedtime["bg"])
        b_head.pack(fill="x", pady=(0, 8))

        tk.Label(b_head, text="🌙 BEDTIME WIND-DOWN REMINDERS", font=("Segoe UI", 9, "bold"), bg=card_bedtime["bg"], fg=self.theme.get("text_muted", "#64748B")).pack(side="left")

        self.bedtime_toggle = ToggleSwitch(
            b_head,
            self.theme,
            is_on=self.settings_mgr.bedtime_reminder_enabled,
            command=self._on_bedtime_toggle,
            width=46,
            height=24
        )
        self.bedtime_toggle.pack(side="right")

        # Bedtime hour & min picker
        b_pick_row = tk.Frame(card_bedtime, bg=card_bedtime["bg"])
        b_pick_row.pack(fill="x", pady=(0, 8))

        tk.Label(b_pick_row, text="Scheduled Bedtime:", font=("Segoe UI", 9), bg=card_bedtime["bg"], fg=self.theme.get("text_secondary", "#94A3B8"), width=18, anchor="w").pack(side="left")

        b_hr = self.settings_mgr.bedtime_hour
        b_mn = self.settings_mgr.bedtime_minute
        self.var_b_hour = tk.StringVar(value=f"{b_hr:02d}")
        self.var_b_min = tk.StringVar(value=f"{b_mn:02d}")

        ttk.Combobox(b_pick_row, textvariable=self.var_b_hour, values=[f"{h:02d}" for h in range(24)], width=4, state="readonly").pack(side="left")
        tk.Label(b_pick_row, text=" : ", bg=card_bedtime["bg"], fg="#FFF").pack(side="left")
        ttk.Combobox(b_pick_row, textvariable=self.var_b_min, values=[f"{m:02d}" for m in range(0, 60, 5)], width=4, state="readonly").pack(side="left")

        # Lead time
        lead_row = tk.Frame(card_bedtime, bg=card_bedtime["bg"])
        lead_row.pack(fill="x", pady=(0, 8))

        tk.Label(lead_row, text="Remind Me Beforehand:", font=("Segoe UI", 9), bg=card_bedtime["bg"], fg=self.theme.get("text_secondary", "#94A3B8"), width=18, anchor="w").pack(side="left")

        self.var_lead = tk.StringVar(value=str(self.settings_mgr.bedtime_reminder_lead_mins))
        ttk.Combobox(lead_row, textvariable=self.var_lead, values=["15", "30", "45", "60"], width=6, state="readonly").pack(side="left")
        tk.Label(lead_row, text=" minutes before bedtime", font=("Segoe UI", 9), bg=card_bedtime["bg"], fg=self.theme.get("text_secondary", "#94A3B8")).pack(side="left", padx=(0, 14))

        ModernButton(lead_row, self.theme, text="Test Notification", command=self._test_bedtime_dialog, variant="secondary", font_size=9, padx=10, pady=2).pack(side="left")

        # 5. USER PROFILE & APPLICATION INFO CARD
        card_info = CardFrame(pad_container, self.theme, padx=18, pady=14)
        card_info.pack(fill="x", pady=(0, 20))

        tk.Label(card_info, text="ℹ️ APPLICATION INFORMATION & ABOUT", font=("Segoe UI", 9, "bold"), bg=card_info["bg"], fg=self.theme.get("text_muted", "#64748B")).pack(anchor="w", pady=(0, 8))

        info_grid = tk.Frame(card_info, bg=card_info["bg"])
        info_grid.pack(fill="x")

        app_meta = [
            ("Application:", "SleepSync – Smart Sleep & Alarm Desktop App"),
            ("Version:", "1.0.0 (Production Release)"),
            ("Database:", "SQLite local storage (data/sleepsync.db)"),
            ("Audio Engine:", "Pygame SDL Mixer (Offline 44.1kHz audio)"),
            ("Charts Engine:", "Matplotlib embedded canvas"),
            ("Author / Portfolio:", "Senior Python Desktop Project"),
        ]

        for i, (k, v) in enumerate(app_meta):
            tk.Label(info_grid, text=k, font=("Segoe UI", 9, "bold"), bg=card_info["bg"], fg=self.theme.get("text_secondary", "#94A3B8"), width=18, anchor="w").grid(row=i, column=0, sticky="w", pady=2)
            tk.Label(info_grid, text=v, font=("Segoe UI", 9), bg=card_info["bg"], fg=self.theme.get("text_primary", "#F8FAFC"), anchor="w").grid(row=i, column=1, sticky="w", pady=2)

        # 6. ACTION BUTTONS (Save Settings & Reset Defaults)
        btn_row = tk.Frame(pad_container, bg=self["bg"])
        btn_row.pack(fill="x", pady=(0, 25))

        ModernButton(btn_row, self.theme, text="Save All Settings", command=self._save_settings, variant="primary", font_size=11, padx=20, pady=8).pack(side="left", padx=(0, 10))
        ModernButton(btn_row, self.theme, text="Reset Defaults", command=self._reset_defaults, variant="secondary", font_size=10, padx=14, pady=8).pack(side="left")

    def _on_theme_select(self):
        new_theme = self.var_theme.get()
        self.settings_mgr.set("theme", new_theme)
        self.on_theme_changed(new_theme)

    def _on_math_toggle(self, is_on: bool):
        self.settings_mgr.set("math_challenge_enabled", "1" if is_on else "0")

    def _on_bedtime_toggle(self, is_on: bool):
        self.settings_mgr.set("bedtime_reminder_enabled", "1" if is_on else "0")

    def _test_math_dialog(self):
        diff = self.var_diff.get()
        MathChallengeDialog(self, self.theme, difficulty=diff, on_success=lambda: messagebox.showinfo("Solved!", "Math challenge completed successfully!"))

    def _test_bedtime_dialog(self):
        lead = int(self.var_lead.get())
        BedtimeReminderDialog(self, self.theme, lead_mins=lead)

    def _save_settings(self):
        self.settings_mgr.set("time_format", self.var_fmt.get())
        self.settings_mgr.set("default_snooze_mins", self.var_default_snooze.get())
        self.settings_mgr.set("default_alarm_volume", str(int(self.slider_alarm_vol.get())))
        self.settings_mgr.set("math_difficulty", self.var_diff.get())
        self.settings_mgr.set("bedtime_hour", self.var_b_hour.get())
        self.settings_mgr.set("bedtime_minute", self.var_b_min.get())
        self.settings_mgr.set("bedtime_reminder_lead_mins", self.var_lead.get())
        messagebox.showinfo("Settings Saved", "Your SleepSync preferences have been saved successfully!")

    def _reset_defaults(self):
        if messagebox.askyesno("Reset", "Reset all settings to default values?"):
            self.settings_mgr.set("theme", "dark")
            self.settings_mgr.set("time_format", "12")
            self.settings_mgr.set("default_snooze_mins", "10")
            self.settings_mgr.set("default_alarm_volume", "80")
            self.settings_mgr.set("math_challenge_enabled", "1")
            self.settings_mgr.set("math_difficulty", "medium")
            self.settings_mgr.set("bedtime_hour", "22")
            self.settings_mgr.set("bedtime_minute", "30")
            self.settings_mgr.set("bedtime_reminder_lead_mins", "30")
            self.var_theme.set("dark")
            self.on_theme_changed("dark")
            self.refresh()

    def refresh(self):
        pass
