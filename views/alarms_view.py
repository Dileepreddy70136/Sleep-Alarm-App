"""
SleepSync - Alarms View
Complete smart alarm manager with 12/24h time picker, repeat options,
sound selector & preview, snooze configuration, and interactive toggle cards.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, List, Optional, Callable

from ui_components import CardFrame, ModernButton, ToggleSwitch
from alarm_manager import AlarmManager, DAY_NAMES
from settings import SettingsManager


class AlarmEditDialog(tk.Toplevel):
    """Modal dialog to create or edit an alarm."""
    def __init__(self, parent, theme: Dict[str, str], alarm_mgr: AlarmManager,
                 settings_mgr: SettingsManager, alarm_data: Optional[Dict[str, Any]] = None,
                 on_save: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        self.theme = theme
        self.alarm_mgr = alarm_mgr
        self.settings_mgr = settings_mgr
        self.alarm_data = alarm_data or {}
        self.on_save = on_save
        self.is_24h = settings_mgr.is_24h_format

        is_edit = bool(alarm_data)
        self.title("Edit Alarm" if is_edit else "Add New Alarm")
        self.geometry("480x560")
        self.resizable(False, False)
        self.configure(bg=theme.get("bg_root", "#0B0F19"))
        self.attributes("-topmost", True)
        self.grab_set()

        self.custom_sound_path = ""
        self._build_ui()
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        pad = tk.Frame(self, bg=self["bg"], padx=25, pady=20)
        pad.pack(fill="both", expand=True)

        # Title
        tk.Label(
            pad,
            text="⏰ " + ("Edit Alarm" if self.alarm_data else "Create Smart Alarm"),
            font=("Segoe UI", 16, "bold"),
            bg=self["bg"],
            fg=self.theme.get("text_primary", "#F8FAFC")
        ).pack(anchor="w", pady=(0, 15))

        # 1. TIME PICKER CARD
        time_card = CardFrame(pad, self.theme, padx=14, pady=12)
        time_card.pack(fill="x", pady=(0, 12))

        tk.Label(
            time_card,
            text="ALARM TIME",
            font=("Segoe UI", 8, "bold"),
            bg=time_card["bg"],
            fg=self.theme.get("text_muted", "#64748B")
        ).pack(anchor="w", pady=(0, 6))

        time_select_row = tk.Frame(time_card, bg=time_card["bg"])
        time_select_row.pack(anchor="w")

        init_hour = self.alarm_data.get("hour", 7)
        init_minute = self.alarm_data.get("minute", 0)

        # Hour selection
        if self.is_24h:
            hours = [f"{h:02d}" for h in range(24)]
            init_h_str = f"{init_hour:02d}"
        else:
            hours = [f"{h:02d}" for h in range(1, 13)]
            disp_h = init_hour % 12
            if disp_h == 0:
                disp_h = 12
            init_h_str = f"{disp_h:02d}"

        self.var_hour = tk.StringVar(value=init_h_str)
        cb_hour = ttk.Combobox(time_select_row, textvariable=self.var_hour, values=hours, width=4, state="readonly", font=("Segoe UI", 14, "bold"))
        cb_hour.pack(side="left")

        tk.Label(time_select_row, text=" : ", font=("Segoe UI", 16, "bold"), bg=time_card["bg"], fg=self.theme.get("text_primary", "#F8FAFC")).pack(side="left")

        # Minute selection
        minutes = [f"{m:02d}" for m in range(0, 60)]
        self.var_minute = tk.StringVar(value=f"{init_minute:02d}")
        cb_minute = ttk.Combobox(time_select_row, textvariable=self.var_minute, values=minutes, width=4, state="readonly", font=("Segoe UI", 14, "bold"))
        cb_minute.pack(side="left")

        # AM/PM selection (if 12h mode)
        if not self.is_24h:
            init_ampm = "AM" if init_hour < 12 else "PM"
            self.var_ampm = tk.StringVar(value=init_ampm)
            cb_ampm = ttk.Combobox(time_select_row, textvariable=self.var_ampm, values=["AM", "PM"], width=4, state="readonly", font=("Segoe UI", 12, "bold"))
            cb_ampm.pack(side="left", padx=(10, 0))

        # 2. LABEL ENTRY CARD
        label_card = CardFrame(pad, self.theme, padx=14, pady=10)
        label_card.pack(fill="x", pady=(0, 12))

        tk.Label(
            label_card,
            text="ALARM LABEL",
            font=("Segoe UI", 8, "bold"),
            bg=label_card["bg"],
            fg=self.theme.get("text_muted", "#64748B")
        ).pack(anchor="w", pady=(0, 4))

        self.var_label = tk.StringVar(value=self.alarm_data.get("label", "Morning Rise"))
        self.entry_label = tk.Entry(
            label_card,
            textvariable=self.var_label,
            font=("Segoe UI", 11),
            bg=self.theme.get("bg_input", "#111827"),
            fg=self.theme.get("text_primary", "#F8FAFC"),
            insertbackground="#FFFFFF",
            highlightthickness=1,
            highlightbackground=self.theme.get("border", "#24324D"),
            relief="flat"
        )
        self.entry_label.pack(fill="x", ipady=4)

        # 3. REPEAT DAYS CARD
        repeat_card = CardFrame(pad, self.theme, padx=14, pady=10)
        repeat_card.pack(fill="x", pady=(0, 12))

        rep_header = tk.Frame(repeat_card, bg=repeat_card["bg"])
        rep_header.pack(fill="x", pady=(0, 6))

        tk.Label(
            rep_header,
            text="REPEAT SCHEDULE",
            font=("Segoe UI", 8, "bold"),
            bg=repeat_card["bg"],
            fg=self.theme.get("text_muted", "#64748B")
        ).pack(side="left")

        # Shortcut buttons
        short_frame = tk.Frame(rep_header, bg=repeat_card["bg"])
        short_frame.pack(side="right")
        ModernButton(short_frame, self.theme, text="Once", command=self._set_once, variant="secondary", font_size=8, padx=6, pady=1).pack(side="left", padx=2)
        ModernButton(short_frame, self.theme, text="Daily", command=self._set_daily, variant="secondary", font_size=8, padx=6, pady=1).pack(side="left", padx=2)
        ModernButton(short_frame, self.theme, text="Weekdays", command=self._set_weekdays, variant="secondary", font_size=8, padx=6, pady=1).pack(side="left", padx=2)

        # Day Checkbuttons
        existing_days = self.alarm_data.get("days", "Daily")
        self.day_vars: Dict[str, tk.BooleanVar] = {}
        days_row = tk.Frame(repeat_card, bg=repeat_card["bg"])
        days_row.pack(fill="x", pady=4)

        for day in DAY_NAMES:
            is_checked = (existing_days == "Daily") or (day in existing_days.split(","))
            var = tk.BooleanVar(value=is_checked)
            self.day_vars[day] = var
            cb = tk.Checkbutton(
                days_row,
                text=day,
                variable=var,
                bg=repeat_card["bg"],
                fg=self.theme.get("text_primary", "#F8FAFC"),
                selectcolor=self.theme.get("bg_input", "#111827"),
                activebackground=repeat_card["bg"],
                activeforeground=self.theme.get("text_primary", "#F8FAFC"),
                font=("Segoe UI", 9)
            )
            cb.pack(side="left", padx=2)

        # 4. SOUND & SNOOZE ROW
        options_row = tk.Frame(pad, bg=self["bg"])
        options_row.pack(fill="x", pady=(0, 16))

        # Sound Selector
        sound_col = tk.Frame(options_row, bg=self["bg"])
        sound_col.pack(side="left", fill="x", expand=True, padx=(0, 6))

        tk.Label(sound_col, text="SOUND", font=("Segoe UI", 8, "bold"), bg=self["bg"], fg=self.theme.get("text_muted", "#64748B")).pack(anchor="w", pady=(0, 2))

        self.sound_options = [
            "peaceful_chime.wav",
            "zen_harp.wav",
            "digital_alarm.wav",
            "gentle_rain.wav",
            "white_noise.wav",
            "Browse Custom..."
        ]
        curr_sound = self.alarm_data.get("sound", "peaceful_chime.wav")
        if curr_sound not in self.sound_options:
            self.custom_sound_path = curr_sound
            self.sound_options.insert(0, os.path.basename(curr_sound))
            self.var_sound = tk.StringVar(value=os.path.basename(curr_sound))
        else:
            self.var_sound = tk.StringVar(value=curr_sound)

        sound_select_row = tk.Frame(sound_col, bg=self["bg"])
        sound_select_row.pack(fill="x")

        self.cb_sound = ttk.Combobox(sound_select_row, textvariable=self.var_sound, values=self.sound_options, state="readonly", width=16)
        self.cb_sound.pack(side="left", fill="x", expand=True)
        self.cb_sound.bind("<<ComboboxSelected>>", self._on_sound_selected)

        # Preview button
        ModernButton(sound_select_row, self.theme, text="▶", command=self._preview_sound, variant="secondary", font_size=9, padx=6, pady=2).pack(side="left", padx=(4, 0))

        # Snooze Duration
        snooze_col = tk.Frame(options_row, bg=self["bg"])
        snooze_col.pack(side="right", fill="x", padx=(6, 0))

        tk.Label(snooze_col, text="SNOOZE", font=("Segoe UI", 8, "bold"), bg=self["bg"], fg=self.theme.get("text_muted", "#64748B")).pack(anchor="w", pady=(0, 2))

        self.var_snooze = tk.StringVar(value=str(self.alarm_data.get("snooze_duration", self.settings_mgr.default_snooze_mins)))
        cb_snooze = ttk.Combobox(snooze_col, textvariable=self.var_snooze, values=["5", "10", "15", "20"], width=6, state="readonly")
        cb_snooze.pack()

        # 5. BUTTONS ROW
        btn_row = tk.Frame(pad, bg=self["bg"])
        btn_row.pack(fill="x", pady=(10, 0))

        ModernButton(btn_row, self.theme, text="Cancel", command=self.destroy, variant="secondary", font_size=10).pack(side="left", padx=(0, 6))
        ModernButton(btn_row, self.theme, text="Save Alarm", command=self._save, variant="primary", font_size=10).pack(side="right")

    def _set_once(self):
        for v in self.day_vars.values():
            v.set(False)

    def _set_daily(self):
        for v in self.day_vars.values():
            v.set(True)

    def _set_weekdays(self):
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        for d, v in self.day_vars.items():
            v.set(d in weekdays)

    def _on_sound_selected(self, event=None):
        if self.var_sound.get() == "Browse Custom...":
            path = filedialog.askopenfilename(
                title="Select Custom Alarm Audio",
                filetypes=[("Audio Files", "*.wav;*.mp3;*.ogg"), ("All Files", "*.*")]
            )
            if path:
                self.custom_sound_path = path
                base_name = os.path.basename(path)
                self.sound_options.insert(0, base_name)
                self.cb_sound.configure(values=self.sound_options)
                self.var_sound.set(base_name)
            else:
                self.var_sound.set("peaceful_chime.wav")

    def _preview_sound(self):
        snd = self.custom_sound_path if self.custom_sound_path else self.var_sound.get()
        vol = self.settings_mgr.default_alarm_volume / 100.0
        self.alarm_mgr.preview_sound(snd, volume=vol)

    def _save(self):
        label = self.var_label.get().strip() or "Alarm"
        
        # Calculate 24h hour and minute
        minute = int(self.var_minute.get())
        if self.is_24h:
            hour = int(self.var_hour.get())
        else:
            h_12 = int(self.var_hour.get())
            ampm = self.var_ampm.get()
            hour, _ = AlarmManager.parse_12h_to_24h(h_12, minute, ampm)

        # Days string
        active_days = [d for d, v in self.day_vars.items() if v.get()]
        if len(active_days) == 7:
            days_str = "Daily"
        elif len(active_days) == 0:
            days_str = "Once"
        else:
            days_str = ",".join(active_days)

        # Sound
        sound = self.custom_sound_path if self.custom_sound_path else self.var_sound.get()
        snooze_dur = int(self.var_snooze.get())

        if self.alarm_data.get("id"):
            # Update
            self.alarm_mgr.update_alarm(
                alarm_id=self.alarm_data["id"],
                label=label,
                hour=hour,
                minute=minute,
                days=days_str,
                sound=sound,
                snooze_duration=snooze_dur,
                is_active=self.alarm_data.get("is_active", 1)
            )
        else:
            # Create
            self.alarm_mgr.add_alarm(
                label=label,
                hour=hour,
                minute=minute,
                days=days_str,
                sound=sound,
                snooze_duration=snooze_dur,
                is_active=1
            )

        if self.on_save:
            self.on_save()
        self.destroy()


class AlarmsView(tk.Frame):
    def __init__(self, parent, theme: Dict[str, str],
                 alarm_mgr: AlarmManager,
                 settings_mgr: SettingsManager):
        super().__init__(parent, bg=theme.get("bg_root", "#0B0F19"))
        self.theme = theme
        self.alarm_mgr = alarm_mgr
        self.settings_mgr = settings_mgr

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Header Row
        header_frame = tk.Frame(self, bg=self["bg"], padx=25, pady=20)
        header_frame.pack(fill="x")

        title_col = tk.Frame(header_frame, bg=self["bg"])
        title_col.pack(side="left")

        tk.Label(
            title_col,
            text="⏰ Smart Alarms",
            font=("Segoe UI", 20, "bold"),
            bg=self["bg"],
            fg=self.theme.get("text_primary", "#F8FAFC")
        ).pack(anchor="w")

        tk.Label(
            title_col,
            text="Reliable scheduled wake-up alarms with math challenges and gentle tones",
            font=("Segoe UI", 10),
            bg=self["bg"],
            fg=self.theme.get("text_secondary", "#94A3B8")
        ).pack(anchor="w", pady=(2, 0))

        ModernButton(
            header_frame,
            self.theme,
            text="+ Add Alarm",
            command=self._open_add_dialog,
            variant="primary",
            font_size=11,
            padx=16,
            pady=8
        ).pack(side="right")

        # Desktop Reliability Notice Banner
        notice_card = tk.Frame(
            self,
            bg=self.theme.get("bg_card_secondary", "#1E2B42"),
            highlightbackground=self.theme.get("border", "#24324D"),
            highlightthickness=1,
            padx=16,
            pady=8
        )
        notice_card.pack(fill="x", padx=25, pady=(0, 15))

        tk.Label(
            notice_card,
            text="ℹ️ Desktop Alarm Note: SleepSync must remain running or minimized in Windows for alarms to trigger. Computer sleep/hibernation pauses desktop timers.",
            font=("Segoe UI", 8),
            bg=notice_card["bg"],
            fg=self.theme.get("accent_light", "#C4B5FD"),
            anchor="w"
        ).pack(fill="x")

        # Scrollable Alarm Cards List
        canvas = tk.Canvas(self, bg=self["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.alarms_list_frame = tk.Frame(canvas, bg=self["bg"])

        self.alarms_list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        self.canvas_win = canvas.create_window((0, 0), window=self.alarms_list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(self.canvas_win, width=e.width)
        )

        canvas.pack(side="left", fill="both", expand=True, padx=(25, 0), pady=(0, 20))
        scrollbar.pack(side="right", fill="y", padx=(0, 20), pady=(0, 20))

    def _open_add_dialog(self):
        AlarmEditDialog(self, self.theme, self.alarm_mgr, self.settings_mgr, on_save=self.refresh)

    def _open_edit_dialog(self, alarm_data: Dict[str, Any]):
        AlarmEditDialog(self, self.theme, self.alarm_mgr, self.settings_mgr, alarm_data=alarm_data, on_save=self.refresh)

    def _delete_alarm(self, alarm_id: int):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this alarm?"):
            self.alarm_mgr.delete_alarm(alarm_id)
            self.refresh()

    def refresh(self):
        """Re-render all alarm cards from SQLite."""
        for child in self.alarms_list_frame.winfo_children():
            child.destroy()

        alarms = self.alarm_mgr.get_alarms()
        is_24h = self.settings_mgr.is_24h_format

        if not alarms:
            empty_frame = CardFrame(self.alarms_list_frame, self.theme, padx=30, pady=35)
            empty_frame.pack(fill="x", pady=20)
            tk.Label(
                empty_frame,
                text="No alarms created yet.",
                font=("Segoe UI", 13, "bold"),
                bg=empty_frame["bg"],
                fg=self.theme.get("text_primary", "#F8FAFC")
            ).pack()
            tk.Label(
                empty_frame,
                text="Click '+ Add Alarm' above to set your first wake-up schedule.",
                font=("Segoe UI", 10),
                bg=empty_frame["bg"],
                fg=self.theme.get("text_muted", "#64748B")
            ).pack(pady=(4, 0))
            return

        for alarm in alarms:
            self._render_alarm_card(alarm, is_24h)

    def _render_alarm_card(self, alarm: Dict[str, Any], is_24h: bool):
        card = CardFrame(self.alarms_list_frame, self.theme, padx=18, pady=14)
        card.pack(fill="x", pady=(0, 10))

        # Left Column: Time & Repeat Days
        left_col = tk.Frame(card, bg=card["bg"])
        left_col.pack(side="left", anchor="w")

        time_str = AlarmManager.format_time(alarm["hour"], alarm["minute"], is_24h)
        time_lbl = tk.Label(
            left_col,
            text=time_str,
            font=("Segoe UI", 22, "bold"),
            bg=card["bg"],
            fg=self.theme.get("text_primary", "#F8FAFC") if alarm["is_active"] else self.theme.get("text_muted", "#64748B")
        )
        time_lbl.pack(anchor="w")

        # Label & Badges
        details_row = tk.Frame(left_col, bg=card["bg"])
        details_row.pack(anchor="w", pady=(3, 0))

        tk.Label(
            details_row,
            text=alarm.get("label", "Alarm"),
            font=("Segoe UI", 10, "bold"),
            bg=card["bg"],
            fg=self.theme.get("accent_light", "#C4B5FD") if alarm["is_active"] else self.theme.get("text_muted", "#64748B")
        ).pack(side="left")

        tk.Label(
            details_row,
            text=f" • {alarm.get('days', 'Daily')}",
            font=("Segoe UI", 9),
            bg=card["bg"],
            fg=self.theme.get("text_secondary", "#94A3B8")
        ).pack(side="left")

        sound_name = os.path.basename(alarm.get("sound", "peaceful_chime.wav"))
        tk.Label(
            details_row,
            text=f" • 🔔 {sound_name}",
            font=("Segoe UI", 9),
            bg=card["bg"],
            fg=self.theme.get("text_muted", "#64748B")
        ).pack(side="left")

        # Right Column: Controls (Toggle Switch, Preview, Edit, Delete)
        right_col = tk.Frame(card, bg=card["bg"])
        right_col.pack(side="right", anchor="e")

        # Preview Sound button
        ModernButton(
            right_col, self.theme,
            text="▶",
            command=lambda s=alarm["sound"]: self.alarm_mgr.preview_sound(s),
            variant="secondary",
            font_size=9,
            padx=6,
            pady=3
        ).pack(side="left", padx=(0, 8))

        # Edit button
        ModernButton(
            right_col, self.theme,
            text="Edit",
            command=lambda a=alarm: self._open_edit_dialog(a),
            variant="secondary",
            font_size=9,
            padx=8,
            pady=3
        ).pack(side="left", padx=(0, 8))

        # Delete button
        ModernButton(
            right_col, self.theme,
            text="✕",
            command=lambda aid=alarm["id"]: self._delete_alarm(aid),
            variant="danger",
            font_size=9,
            padx=8,
            pady=3
        ).pack(side="left", padx=(0, 16))

        # Interactive Toggle Switch
        toggle = ToggleSwitch(
            right_col,
            self.theme,
            is_on=bool(alarm["is_active"]),
            command=lambda state, aid=alarm["id"]: self._on_toggle(aid, state),
            width=46,
            height=24
        )
        toggle.pack(side="left")

    def _on_toggle(self, alarm_id: int, is_active: bool):
        self.alarm_mgr.toggle_alarm(alarm_id, 1 if is_active else 0)
        self.refresh()
