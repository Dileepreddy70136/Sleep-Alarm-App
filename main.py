"""
SleepSync – AI Camera Sleep & Wake Alarm Application
Camera-based real-time sleep monitor. Blasts a loud wake-up alarm
immediately when sleep or closed eyes are detected.
Zero clutter, clean interface, instant response.
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import pygame
try:
    import winsound
except ImportError:
    winsound = None

from camera_detector import CameraSleepDetector
from sound_generator import ensure_built_in_sounds


class SleepSyncCameraApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.sounds_dir = os.path.join(self.app_dir, "sounds")
        ensure_built_in_sounds(self.sounds_dir)

        # Pygame mixer for loud alarm playback
        self.alarm_file = os.path.join(self.sounds_dir, "loud_alarm.wav")
        self._init_audio()

        # Detector
        self.detector = CameraSleepDetector(camera_index=0)
        self.detector.sleep_threshold_sec = 2.0
        self.detector.on_sleep_detected = self._on_sleep_detected
        self.detector.on_wake_up = self._on_wake_up

        # Alarm playback state
        self.is_alarm_ringing = False
        self._alarm_channel = None
        self._alarm_sound = None
        self._photo_image = None
        self._pulse_state = 0

        # Window setup
        self.title("SleepSync – AI Camera Sleep & Wake Alarm")
        self.geometry("720x690")
        self.minsize(660, 620)
        self.configure(bg="#0B0F19")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._center_window()

        self._build_ui()

    def _center_window(self):
        self.update_idletasks()
        w = 720
        h = 690
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw // 2) - (w // 2))
        y = max(0, (sh // 2) - (h // 2) - 20)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _init_audio(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            if os.path.exists(self.alarm_file):
                self._alarm_sound = pygame.mixer.Sound(self.alarm_file)
                self._alarm_sound.set_volume(1.0)
        except Exception as e:
            print(f"Warning: Audio init error: {e}")

    def _build_ui(self):
        pad = tk.Frame(self, bg="#0B0F19", padx=20, pady=16)
        pad.pack(fill="both", expand=True)

        # 1. HEADER
        header = tk.Frame(pad, bg="#0B0F19")
        header.pack(fill="x", pady=(0, 12))

        title_row = tk.Frame(header, bg="#0B0F19")
        title_row.pack(anchor="w")

        tk.Label(
            title_row,
            text="👁️",
            font=("Segoe UI Emoji", 20),
            bg="#0B0F19",
            fg="#C4B5FD"
        ).pack(side="left")

        tk.Label(
            title_row,
            text=" SleepSync – Camera Sleep & Wake Alarm",
            font=("Segoe UI", 16, "bold"),
            bg="#0B0F19",
            fg="#F8FAFC"
        ).pack(side="left")

        tk.Label(
            header,
            text="Monitors your eyes in real time. Blasts a loud alarm immediately when you fall asleep.",
            font=("Segoe UI", 9),
            bg="#0B0F19",
            fg="#94A3B8"
        ).pack(anchor="w", pady=(2, 0))

        # 2. CAMERA FEED CARD
        self.camera_card = tk.Frame(
            pad,
            bg="#162032",
            highlightbackground="#24324D",
            highlightthickness=1,
            padx=10,
            pady=10
        )
        self.camera_card.pack(fill="both", expand=True, pady=(0, 10))

        self.canvas = tk.Canvas(
            self.camera_card,
            width=580,
            height=370,
            bg="#0B0F19",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Initial placeholder on canvas
        self._draw_placeholder()

        # 3. REAL-TIME STATUS BAR
        self.status_bar = tk.Frame(
            pad,
            bg="#162032",
            highlightbackground="#24324D",
            highlightthickness=1,
            padx=14,
            pady=10
        )
        self.status_bar.pack(fill="x", pady=(0, 12))

        self.lbl_status = tk.Label(
            self.status_bar,
            text="📷 Camera Idle. Click 'Start Camera Monitor' below.",
            font=("Segoe UI", 12, "bold"),
            bg="#162032",
            fg="#94A3B8"
        )
        self.lbl_status.pack(side="left")

        self.lbl_timer = tk.Label(
            self.status_bar,
            text="",
            font=("Segoe UI", 10, "bold"),
            bg="#162032",
            fg="#EF4444"
        )
        self.lbl_timer.pack(side="right")

        # 4. CONTROLS BAR (Big Buttons & Direct Actions)
        ctrls_frame = tk.Frame(pad, bg="#0B0F19")
        ctrls_frame.pack(fill="x", pady=(0, 10))

        # Main Start / Stop Button
        self.btn_toggle_camera = tk.Button(
            ctrls_frame,
            text="▶ START CAMERA MONITOR",
            font=("Segoe UI", 12, "bold"),
            bg="#8B5CF6",
            fg="#FFFFFF",
            activebackground="#7C3AED",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=20,
            pady=12,
            command=self._toggle_camera
        )
        self.btn_toggle_camera.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # "I'm Awake" Stop Alarm Button
        self.btn_dismiss_alarm = tk.Button(
            ctrls_frame,
            text="🔔 I'M AWAKE (STOP ALARM)",
            font=("Segoe UI", 12, "bold"),
            bg="#1E2B42",
            fg="#64748B",
            activebackground="#059669",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=16,
            pady=12,
            command=self._stop_alarm
        )
        self.btn_dismiss_alarm.pack(side="right", fill="x", expand=True, padx=(8, 0))

        # 5. TRIGGER SENSITIVITY & TEST ROW
        opts_row = tk.Frame(pad, bg="#0B0F19")
        opts_row.pack(fill="x")

        # Sleep delay selector
        delay_col = tk.Frame(opts_row, bg="#0B0F19")
        delay_col.pack(side="left")

        tk.Label(
            delay_col,
            text="Trigger Alarm After Closed:",
            font=("Segoe UI", 9, "bold"),
            bg="#0B0F19",
            fg="#94A3B8"
        ).pack(side="left", padx=(0, 6))

        self.var_threshold = tk.StringVar(value="2.0s")
        for val, label in [("1.5s", "1.5s (Fast)"), ("2.0s", "2.0s (Normal)"), ("3.0s", "3.0s (Relaxed)")]:
            rb = tk.Radiobutton(
                delay_col,
                text=label,
                value=val,
                variable=self.var_threshold,
                command=self._update_threshold,
                bg="#0B0F19",
                fg="#F8FAFC",
                selectcolor="#162032",
                activebackground="#0B0F19",
                activeforeground="#F8FAFC",
                font=("Segoe UI", 9)
            )
            rb.pack(side="left", padx=3)

        # Test Alarm Sound Button
        btn_test = tk.Button(
            opts_row,
            text="🔊 Test Loud Sound",
            font=("Segoe UI", 9, "bold"),
            bg="#1E2B42",
            fg="#C4B5FD",
            activebackground="#24324D",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=12,
            pady=4,
            command=self._test_loud_alarm
        )
        btn_test.pack(side="right")

    def _draw_placeholder(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width() or 580
        h = self.canvas.winfo_height() or 370
        self.canvas.create_text(
            w // 2, h // 2 - 20,
            text="📷",
            font=("Segoe UI Emoji", 44),
            fill="#24324D"
        )
        self.canvas.create_text(
            w // 2, h // 2 + 30,
            text="Camera is Off\nClick 'START CAMERA MONITOR' to begin sleep tracking",
            font=("Segoe UI", 11),
            fill="#64748B",
            justify="center"
        )

    def _update_threshold(self):
        val_str = self.var_threshold.get().replace("s", "")
        try:
            self.detector.sleep_threshold_sec = float(val_str)
        except ValueError:
            pass

    def _toggle_camera(self):
        if self.detector.is_running:
            # Stop
            self.detector.stop()
            self._stop_alarm()
            self.btn_toggle_camera.configure(
                text="▶ START CAMERA MONITOR",
                bg="#8B5CF6",
                activebackground="#7C3AED"
            )
            self.lbl_status.configure(
                text="📷 Camera Idle. Click 'Start Camera Monitor' below.",
                fg="#94A3B8"
            )
            self.lbl_timer.configure(text="")
            self._draw_placeholder()
        else:
            # Start
            success = self.detector.start()
            if not success:
                messagebox.showerror(
                    "Camera Error",
                    "Could not open webcam. Please verify your camera is connected and not in use by another app."
                )
                return
            self.btn_toggle_camera.configure(
                text="⏹ STOP MONITOR",
                bg="#DC2626",
                activebackground="#B91C1C"
            )
            self.lbl_status.configure(
                text="🟢 Camera Active – Tracking Face & Eyes",
                fg="#10B981"
            )
            # Begin frame reading loop
            self._process_camera_loop()

    def _process_camera_loop(self):
        if not self.detector.is_running:
            return

        frame, info = self.detector.process_next_frame()

        if frame is not None:
            # Resize frame to fit canvas
            cw = self.canvas.winfo_width()
            ch = self.canvas.winfo_height()
            if cw > 50 and ch > 50:
                frame_resized = cv2.resize(frame, (cw, ch))
                rgb_frame = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_frame)
                self._photo_image = ImageTk.PhotoImage(image=pil_img)
                self.canvas.delete("all")
                self.canvas.create_image(0, 0, image=self._photo_image, anchor="nw")

            # Update status label
            self.lbl_status.configure(text=info["status"], fg=info["color"])

            if info.get("closed_duration", 0) > 0.3:
                self.lbl_timer.configure(text=f"Closed: {info['closed_duration']:.1f}s")
            else:
                self.lbl_timer.configure(text="")

        # Schedule next frame in ~30ms (~33 FPS)
        self.after(30, self._process_camera_loop)

    # ==========================
    # ALARM TRIGGER & SOUND
    # ==========================

    def _on_sleep_detected(self):
        """Called automatically when eyes remain closed past the threshold."""
        if not self.is_alarm_ringing:
            self._start_loud_alarm()

    def _on_wake_up(self):
        """Called automatically when user opens eyes and is awake."""
        if self.is_alarm_ringing:
            self._stop_alarm()

    def _start_loud_alarm(self):
        self.is_alarm_ringing = True
        self.btn_dismiss_alarm.configure(
            text="🚨 WAKE UP! (CLICK TO STOP)",
            bg="#EF4444",
            fg="#FFFFFF",
            activebackground="#DC2626"
        )
        self.status_bar.configure(highlightbackground="#EF4444", bg="#2B141E")
        self.camera_card.configure(highlightbackground="#EF4444")

        # Play loud alarm on infinite loop
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            if self._alarm_sound:
                self._alarm_sound.set_volume(1.0)
                self._alarm_channel = self._alarm_sound.play(loops=-1)
        except Exception as e:
            print(f"Error playing loud alarm: {e}")

        # Hardware motherboard beep fallback thread
        if winsound:
            threading.Thread(target=self._hardware_beep_loop, daemon=True).start()

        # Bring window to front
        self.lift()
        self.attributes("-topmost", True)
        self.after(1000, lambda: self.attributes("-topmost", False))

    def _hardware_beep_loop(self):
        """Supplemental high-frequency hardware beep while sleeping."""
        while self.is_alarm_ringing:
            try:
                winsound.Beep(2400, 250)
                time.sleep(0.08)
            except Exception:
                break

    def _stop_alarm(self):
        self.is_alarm_ringing = False
        try:
            if self._alarm_channel:
                self._alarm_channel.stop()
            if self._alarm_sound:
                self._alarm_sound.stop()
        except Exception:
            pass

        self.btn_dismiss_alarm.configure(
            text="🔔 I'M AWAKE (STOP ALARM)",
            bg="#1E2B42",
            fg="#64748B",
            activebackground="#059669"
        )
        self.status_bar.configure(highlightbackground="#24324D", bg="#162032")
        self.camera_card.configure(highlightbackground="#24324D")
        self.detector.reset_state()

    def _test_loud_alarm(self):
        """Play loud alarm for 2 seconds as test."""
        self._start_loud_alarm()
        self.after(2000, self._stop_alarm)

    def _on_close(self):
        self._stop_alarm()
        if self.detector.is_running:
            self.detector.stop()
        self.destroy()


def main():
    app = SleepSyncCameraApp()
    app.mainloop()


if __name__ == "__main__":
    main()
