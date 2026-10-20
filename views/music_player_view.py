"""
SleepSync - Relaxing Music Player View
Ambient soundscape player with Pygame mixer, sleep timer countdown,
volume slider, custom audio file picker, and dynamic audio visualizer bars.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import random
from typing import Dict, Any

from ui_components import CardFrame, ModernButton
from music_player import MusicPlayer
from settings import SettingsManager


class MusicPlayerView(tk.Frame):
    def __init__(self, parent, theme: Dict[str, str],
                 music_player: MusicPlayer,
                 settings_mgr: SettingsManager):
        super().__init__(parent, bg=theme.get("bg_root", "#0B0F19"))
        self.theme = theme
        self.music_player = music_player
        self.settings_mgr = settings_mgr

        self.music_player.on_state_change = self.refresh
        self._visualizer_anim_id = None

        self._build_ui()
        self.refresh()
        self._animate_visualizer()

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
            text="🎵 Relaxing Ambient Player",
            font=("Segoe UI", 20, "bold"),
            bg=self["bg"],
            fg=self.theme.get("text_primary", "#F8FAFC")
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Soothing ambient tracks and custom sounds to help you unwind and fall asleep",
            font=("Segoe UI", 10),
            bg=self["bg"],
            fg=self.theme.get("text_secondary", "#94A3B8")
        ).pack(anchor="w", pady=(2, 0))

        # 1. NOW PLAYING CONTROLLER HERO CARD
        self.now_playing_card = CardFrame(pad_container, self.theme, padx=22, pady=18)
        self.now_playing_card.pack(fill="x", pady=(0, 18))

        top_ctrl_row = tk.Frame(self.now_playing_card, bg=self.now_playing_card["bg"])
        top_ctrl_row.pack(fill="x")

        # Track Info (Left)
        track_info_col = tk.Frame(top_ctrl_row, bg=self.now_playing_card["bg"])
        track_info_col.pack(side="left", anchor="w")

        self.lbl_playing_status = tk.Label(
            track_info_col,
            text="⏹ STOPPED",
            font=("Segoe UI", 8, "bold"),
            bg=self.now_playing_card["bg"],
            fg=self.theme.get("text_muted", "#64748B")
        )
        self.lbl_playing_status.pack(anchor="w")

        self.lbl_track_title = tk.Label(
            track_info_col,
            text="No Audio Playing",
            font=("Segoe UI", 16, "bold"),
            bg=self.now_playing_card["bg"],
            fg=self.theme.get("text_primary", "#F8FAFC")
        )
        self.lbl_track_title.pack(anchor="w", pady=(2, 0))

        # Dynamic Audio Visualizer Canvas (Right)
        self.viz_canvas = tk.Canvas(
            top_ctrl_row,
            width=140,
            height=36,
            bg=self.now_playing_card["bg"],
            highlightthickness=0
        )
        self.viz_canvas.pack(side="right", anchor="e")

        # Playback Controls Row (Play, Pause, Resume, Stop)
        ctrls_row = tk.Frame(self.now_playing_card, bg=self.now_playing_card["bg"])
        ctrls_row.pack(fill="x", pady=(16, 12))

        self.btn_play_pause = ModernButton(
            ctrls_row,
            self.theme,
            text="▶ Play",
            command=self._handle_play_pause,
            variant="primary",
            font_size=11,
            padx=18,
            pady=8
        )
        self.btn_play_pause.pack(side="left", padx=(0, 8))

        self.btn_stop = ModernButton(
            ctrls_row,
            self.theme,
            text="⏹ Stop",
            command=self._handle_stop,
            variant="secondary",
            font_size=10,
            padx=14,
            pady=8
        )
        self.btn_stop.pack(side="left", padx=(0, 16))

        # Volume Slider
        vol_frame = tk.Frame(ctrls_row, bg=self.now_playing_card["bg"])
        vol_frame.pack(side="left", padx=10)

        tk.Label(
            vol_frame,
            text="🔊",
            font=("Segoe UI Emoji", 11),
            bg=self.now_playing_card["bg"],
            fg=self.theme.get("text_secondary", "#94A3B8")
        ).pack(side="left", padx=(0, 4))

        self.lbl_volume = tk.Label(
            vol_frame,
            text=f"{int(self.music_player.volume * 100)}%",
            font=("Segoe UI", 9, "bold"),
            bg=self.now_playing_card["bg"],
            fg=self.theme.get("text_secondary", "#94A3B8"),
            width=5
        )

        self.vol_slider = ttk.Scale(
            vol_frame,
            from_=0,
            to=100,
            orient="horizontal",
            length=120,
            command=self._on_volume_change
        )
        self.vol_slider.set(int(self.music_player.volume * 100))
        self.vol_slider.pack(side="left", padx=4)
        self.lbl_volume.pack(side="left")

        # Sleep Timer Pill
        timer_frame = tk.Frame(ctrls_row, bg=self.now_playing_card["bg"])
        timer_frame.pack(side="right")

        tk.Label(
            timer_frame,
            text="⏱ Sleep Timer:",
            font=("Segoe UI", 9),
            bg=self.now_playing_card["bg"],
            fg=self.theme.get("text_secondary", "#94A3B8")
        ).pack(side="left", padx=(0, 6))

        self.var_sleep_timer = tk.StringVar(value="Off")
        cb_timer = ttk.Combobox(
            timer_frame,
            textvariable=self.var_sleep_timer,
            values=["Off", "15m", "30m", "45m", "60m", "90m"],
            width=6,
            state="readonly"
        )
        cb_timer.pack(side="left", padx=(0, 6))
        cb_timer.bind("<<ComboboxSelected>>", self._on_timer_selected)

        self.lbl_timer_remaining = tk.Label(
            timer_frame,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg=self.now_playing_card["bg"],
            fg=self.theme.get("accent_light", "#C4B5FD")
        )
        self.lbl_timer_remaining.pack(side="left")

        # 2. SELECT CUSTOM AUDIO CARD
        custom_card = CardFrame(pad_container, self.theme, padx=18, pady=12)
        custom_card.pack(fill="x", pady=(0, 18))

        c_left = tk.Frame(custom_card, bg=custom_card["bg"])
        c_left.pack(side="left", anchor="w")

        tk.Label(
            c_left,
            text="📁 PLAY YOUR OWN AUDIO FILES",
            font=("Segoe UI", 9, "bold"),
            bg=custom_card["bg"],
            fg=self.theme.get("text_muted", "#64748B")
        ).pack(anchor="w")

        tk.Label(
            c_left,
            text="Load sleep meditations, white noise tracks, or soothing MP3/WAV/OGG files from your computer.",
            font=("Segoe UI", 9),
            bg=custom_card["bg"],
            fg=self.theme.get("text_secondary", "#94A3B8")
        ).pack(anchor="w", pady=(2, 0))

        ModernButton(
            custom_card,
            self.theme,
            text="Browse File...",
            command=self._browse_custom_audio,
            variant="secondary",
            font_size=9,
            padx=14,
            pady=6
        ).pack(side="right")

        # 3. BUILT-IN SOOTHING SOUND PRESETS
        tk.Label(
            pad_container,
            text="🌿 BUILT-IN SOOTHING SOUNDSCAPES",
            font=("Segoe UI", 9, "bold"),
            bg=self["bg"],
            fg=self.theme.get("text_muted", "#64748B")
        ).pack(anchor="w", pady=(0, 10))

        presets = self.music_player.get_built_in_tracks()
        for p in presets:
            self._render_preset_card(pad_container, p)

    def _render_preset_card(self, parent, preset: Dict[str, str]):
        card = CardFrame(parent, self.theme, padx=16, pady=12)
        card.pack(fill="x", pady=(0, 8))

        left = tk.Frame(card, bg=card["bg"])
        left.pack(side="left", anchor="w")

        tk.Label(
            left,
            text=f"🎵 {preset['title']}",
            font=("Segoe UI", 11, "bold"),
            bg=card["bg"],
            fg=self.theme.get("text_primary", "#F8FAFC")
        ).pack(anchor="w")

        tk.Label(
            left,
            text=preset.get("desc", ""),
            font=("Segoe UI", 9),
            bg=card["bg"],
            fg=self.theme.get("text_secondary", "#94A3B8")
        ).pack(anchor="w", pady=(2, 0))

        ModernButton(
            card,
            self.theme,
            text="▶ Play Sound",
            command=lambda p=preset: self._play_track(p["path"], p["title"]),
            variant="primary",
            font_size=9,
            padx=12,
            pady=4
        ).pack(side="right")

    def _play_track(self, file_path: str, title: str):
        try:
            self.music_player.load_and_play(file_path, title=title, loop=True)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Audio Error", str(e))

    def _handle_play_pause(self):
        if not self.music_player.is_playing:
            # Play first preset if none active
            presets = self.music_player.get_built_in_tracks()
            if presets:
                self._play_track(presets[0]["path"], presets[0]["title"])
        elif self.music_player.is_paused:
            self.music_player.resume()
        else:
            self.music_player.pause()
        self.refresh()

    def _handle_stop(self):
        self.music_player.stop()
        self.refresh()

    def _on_volume_change(self, val):
        v = float(val) / 100.0
        self.music_player.set_volume(v)
        if hasattr(self, "lbl_volume"):
            self.lbl_volume.configure(text=f"{int(float(val))}%")

    def _on_timer_selected(self, event=None):
        choice = self.var_sleep_timer.get()
        if choice == "Off":
            self.music_player.cancel_sleep_timer()
        else:
            mins = int(choice.replace("m", ""))
            self.music_player.set_sleep_timer(mins)
        self.refresh()

    def _browse_custom_audio(self):
        path = filedialog.askopenfilename(
            title="Select Relaxing Audio File",
            filetypes=[("Audio Files", "*.mp3;*.wav;*.ogg"), ("All Files", "*.*")]
        )
        if path:
            title = os.path.basename(path)
            self._play_track(path, title)

    def _animate_visualizer(self):
        """Simulated pulsing equalizer bars on canvas when playing."""
        self.viz_canvas.delete("all")
        bar_count = 12
        bar_w = 6
        gap = 4
        canvas_h = 32

        for i in range(bar_count):
            x = i * (bar_w + gap) + 6
            if self.music_player.is_playing and not self.music_player.is_paused:
                h = random.randint(6, canvas_h - 2)
            else:
                h = 4
            y1 = canvas_h - h
            y2 = canvas_h
            fill = self.theme.get("accent", "#8B5CF6") if (self.music_player.is_playing and not self.music_player.is_paused) else self.theme.get("border", "#24324D")
            self.viz_canvas.create_rectangle(x, y1, x + bar_w, y2, fill=fill, outline="")

        if self.winfo_exists():
            self._visualizer_anim_id = self.after(150, self._animate_visualizer)

    def refresh(self):
        """Update Now Playing labels, buttons, and sleep timer display."""
        if self.music_player.is_playing:
            if self.music_player.is_paused:
                self.lbl_playing_status.configure(text="⏸ PAUSED", fg=self.theme.get("warning", "#F59E0B"))
                self.btn_play_pause.configure(text="▶ Resume", bg=self.theme.get("accent", "#8B5CF6"))
            else:
                self.lbl_playing_status.configure(text="▶ PLAYING", fg=self.theme.get("success", "#10B981"))
                self.btn_play_pause.configure(text="⏸ Pause", bg=self.theme.get("accent_hover", "#7C3AED"))
            self.lbl_track_title.configure(text=self.music_player.current_title)
        else:
            self.lbl_playing_status.configure(text="⏹ STOPPED", fg=self.theme.get("text_muted", "#64748B"))
            self.btn_play_pause.configure(text="▶ Play", bg=self.theme.get("accent", "#8B5CF6"))
            self.lbl_track_title.configure(text="No Audio Playing")

        # Sleep Timer Display
        if self.music_player.is_sleep_timer_active:
            countdown = self.music_player.get_sleep_timer_display()
            self.lbl_timer_remaining.configure(text=f"({countdown})")
        else:
            self.lbl_timer_remaining.configure(text="")
