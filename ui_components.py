"""
SleepSync - Reusable UI Components
Modern, beautiful desktop components built with Tkinter and custom Canvas drawing:
- CardFrame (Rounded card container)
- StatCard (KPI metric card with icon, value, subtitle)
- ModernButton / PillButton (Hover animations and custom color themes)
- ToggleSwitch (Interactive smooth animated pill toggle)
- CustomProgressBar (Sleek horizontal rounded progress bar)
- MathChallengeDialog (Wake-up arithmetic puzzle window)
- AlarmTriggerDialog (Dedicated alarm popup with sound, snooze, dismiss)
- BedtimeReminderDialog (Evening wind-down notification popup)
"""

import tkinter as tk
from tkinter import ttk
import random
from typing import Dict, Any, Optional, Callable


class CardFrame(tk.Frame):
    """
    A modern card container with theme-reactive background,
    subtle border, and comfortable internal padding.
    """
    def __init__(self, parent, theme: Dict[str, str], *args, **kwargs):
        self.theme = theme
        # Extract padding if passed
        pad_x = kwargs.pop("padx", 16)
        pad_y = kwargs.pop("pady", 16)
        bg_color = kwargs.pop("bg", theme.get("bg_card", "#162032"))
        highlight_color = kwargs.pop("highlightbackground", theme.get("border", "#24324D"))
        
        super().__init__(
            parent,
            bg=bg_color,
            highlightbackground=highlight_color,
            highlightthickness=1,
            *args,
            **kwargs
        )
        self.pad_x = pad_x
        self.pad_y = pad_y

    def apply_theme(self, theme: Dict[str, str]):
        self.theme = theme
        self.configure(
            bg=theme.get("bg_card", "#162032"),
            highlightbackground=theme.get("border", "#24324D")
        )
        for child in self.winfo_children():
            if hasattr(child, "apply_theme"):
                child.apply_theme(theme)


class StatCard(tk.Frame):
    """
    A KPI card displaying an icon, title, prominent value, and optional badge/subtitle.
    """
    def __init__(self, parent, theme: Dict[str, str], icon: str, title: str,
                 value: str = "--", subtitle: str = "", accent_color: Optional[str] = None, **kwargs):
        super().__init__(
            parent,
            bg=theme.get("bg_card", "#162032"),
            highlightbackground=theme.get("border", "#24324D"),
            highlightthickness=1,
            padx=16,
            pady=14,
            **kwargs
        )
        self.theme = theme
        self.accent_color = accent_color or theme.get("accent", "#8B5CF6")
        
        # Header row: Icon & Title
        header_frame = tk.Frame(self, bg=self["bg"])
        header_frame.pack(fill="x", anchor="w")
        
        self.icon_label = tk.Label(
            header_frame,
            text=icon,
            font=("Segoe UI Emoji", 14),
            bg=theme.get("bg_card_secondary", "#1E2B42"),
            fg=self.accent_color,
            padx=6,
            pady=4
        )
        self.icon_label.pack(side="left")
        
        self.title_label = tk.Label(
            header_frame,
            text=f"  {title.upper()}",
            font=("Segoe UI", 9, "bold"),
            bg=self["bg"],
            fg=theme.get("text_muted", "#64748B")
        )
        self.title_label.pack(side="left", padx=4)

        # Primary Value
        self.value_label = tk.Label(
            self,
            text=value,
            font=("Segoe UI", 20, "bold"),
            bg=self["bg"],
            fg=theme.get("text_primary", "#F8FAFC")
        )
        self.value_label.pack(anchor="w", pady=(8, 2))

        # Subtitle / Hint
        self.subtitle_label = tk.Label(
            self,
            text=subtitle,
            font=("Segoe UI", 9),
            bg=self["bg"],
            fg=theme.get("text_secondary", "#94A3B8")
        )
        self.subtitle_label.pack(anchor="w")

    def update_data(self, value: str, subtitle: Optional[str] = None):
        self.value_label.configure(text=value)
        if subtitle is not None:
            self.subtitle_label.configure(text=subtitle)

    def apply_theme(self, theme: Dict[str, str]):
        self.theme = theme
        bg = theme.get("bg_card", "#162032")
        self.configure(bg=bg, highlightbackground=theme.get("border", "#24324D"))
        for w in self.winfo_children():
            if isinstance(w, tk.Frame):
                w.configure(bg=bg)
        self.icon_label.configure(
            bg=theme.get("bg_card_secondary", "#1E2B42"),
            fg=self.accent_color
        )
        self.title_label.configure(bg=bg, fg=theme.get("text_muted", "#64748B"))
        self.value_label.configure(bg=bg, fg=theme.get("text_primary", "#F8FAFC"))
        self.subtitle_label.configure(bg=bg, fg=theme.get("text_secondary", "#94A3B8"))


class ModernButton(tk.Button):
    """
    Styled button with smooth hover effects and flat modern aesthetic.
    """
    def __init__(self, parent, theme: Dict[str, str], text: str, command: Optional[Callable] = None,
                 variant: str = "primary", font_size: int = 10, **kwargs):
        self.theme = theme
        self.variant = variant
        self.normal_bg, self.hover_bg, self.text_color = self._get_colors()
        
        super().__init__(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", font_size, "bold"),
            bg=self.normal_bg,
            fg=self.text_color,
            activebackground=self.hover_bg,
            activeforeground=self.text_color,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=kwargs.pop("padx", 14),
            pady=kwargs.pop("pady", 7),
            **kwargs
        )
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _get_colors(self):
        if self.variant == "primary":
            return (self.theme.get("accent", "#8B5CF6"),
                    self.theme.get("accent_hover", "#7C3AED"),
                    "#FFFFFF")
        elif self.variant == "success":
            return (self.theme.get("success", "#10B981"),
                    "#059669",
                    "#FFFFFF")
        elif self.variant == "danger":
            return (self.theme.get("danger", "#EF4444"),
                    self.theme.get("danger_hover", "#DC2626"),
                    "#FFFFFF")
        elif self.variant == "secondary":
            return (self.theme.get("bg_card_secondary", "#1E2B42"),
                    self.theme.get("border", "#24324D"),
                    self.theme.get("text_primary", "#F8FAFC"))
        else:
            return (self.theme.get("bg_card", "#162032"),
                    self.theme.get("bg_card_secondary", "#1E2B42"),
                    self.theme.get("text_primary", "#F8FAFC"))

    def _on_enter(self, event=None):
        self.configure(bg=self.hover_bg)

    def _on_leave(self, event=None):
        self.configure(bg=self.normal_bg)

    def apply_theme(self, theme: Dict[str, str]):
        self.theme = theme
        self.normal_bg, self.hover_bg, self.text_color = self._get_colors()
        self.configure(
            bg=self.normal_bg,
            fg=self.text_color,
            activebackground=self.hover_bg,
            activeforeground=self.text_color
        )


class ToggleSwitch(tk.Canvas):
    """
    Modern pill-shaped interactive toggle switch.
    """
    def __init__(self, parent, theme: Dict[str, str], is_on: bool = False,
                 command: Optional[Callable[[bool], None]] = None, width: int = 48, height: int = 24):
        self.theme = theme
        self.is_on = is_on
        self.command = command
        self.w = width
        self.h = height
        
        super().__init__(
            parent,
            width=self.w,
            height=self.h,
            bg=parent["bg"],
            highlightthickness=0,
            cursor="hand2"
        )
        
        self.bind("<Button-1>", self._on_click)
        self.draw()

    def set_state(self, is_on: bool):
        self.is_on = is_on
        self.draw()

    def _on_click(self, event=None):
        self.is_on = not self.is_on
        self.draw()
        if self.command:
            self.command(self.is_on)

    def draw(self):
        self.delete("all")
        bg_pill = self.theme.get("accent", "#8B5CF6") if self.is_on else self.theme.get("border", "#24324D")
        knob_color = "#FFFFFF"

        r = self.h / 2.0
        # Draw rounded pill
        self.create_oval(0, 0, self.h, self.h, fill=bg_pill, outline="")
        self.create_oval(self.w - self.h, 0, self.w, self.h, fill=bg_pill, outline="")
        self.create_rectangle(r, 0, self.w - r, self.h, fill=bg_pill, outline="")

        # Draw circle knob
        pad = 2
        knob_d = self.h - (pad * 2)
        if self.is_on:
            x1 = self.w - knob_d - pad
            x2 = self.w - pad
        else:
            x1 = pad
            x2 = pad + knob_d
        
        self.create_oval(x1, pad, x2, pad + knob_d, fill=knob_color, outline="")

    def apply_theme(self, theme: Dict[str, str]):
        self.theme = theme
        self.configure(bg=self.master["bg"])
        self.draw()


class CustomProgressBar(tk.Canvas):
    """
    A sleek rounded horizontal progress bar.
    """
    def __init__(self, parent, theme: Dict[str, str], width: int = 200, height: int = 12,
                 progress: float = 0.0, **kwargs):
        self.theme = theme
        self.w = width
        self.h = height
        self.progress = max(0.0, min(1.0, progress))
        
        super().__init__(
            parent,
            width=self.w,
            height=self.h,
            bg=parent["bg"],
            highlightthickness=0,
            **kwargs
        )
        self.draw()

    def set_progress(self, progress: float):
        self.progress = max(0.0, min(1.0, progress))
        self.draw()

    def draw(self):
        self.delete("all")
        bg_track = self.theme.get("bg_card_secondary", "#1E2B42")
        bar_color = self.theme.get("accent", "#8B5CF6")
        
        r = self.h / 2.0
        # Draw track
        self.create_oval(0, 0, self.h, self.h, fill=bg_track, outline="")
        self.create_oval(self.w - self.h, 0, self.w, self.h, fill=bg_track, outline="")
        self.create_rectangle(r, 0, self.w - r, self.h, fill=bg_track, outline="")

        # Draw filled progress
        fill_w = max(self.h, int(self.w * self.progress))
        if self.progress > 0.01:
            self.create_oval(0, 0, self.h, self.h, fill=bar_color, outline="")
            if fill_w > self.h:
                self.create_oval(fill_w - self.h, 0, fill_w, self.h, fill=bar_color, outline="")
                self.create_rectangle(r, 0, fill_w - r, self.h, fill=bar_color, outline="")

    def apply_theme(self, theme: Dict[str, str]):
        self.theme = theme
        self.configure(bg=self.master["bg"])
        self.draw()


# ==========================================================
# DIALOGS AND POPUPS
# ==========================================================

class MathChallengeDialog(tk.Toplevel):
    """
    Mathematical wake-up challenge dialog before dismissing an alarm.
    Prevents mindless snooze/dismissal and stimulates cognitive alertness.
    """
    def __init__(self, parent, theme: Dict[str, str], difficulty: str = "medium",
                 on_success: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        self.theme = theme
        self.difficulty = difficulty
        self.on_success = on_success
        self.is_solved = False

        self.title("SleepSync – Wake-Up Challenge")
        self.geometry("420x330")
        self.resizable(False, False)
        self.configure(bg=theme.get("bg_root", "#0B0F19"))
        self.attributes("-topmost", True)
        self.grab_set()  # Modal

        self._generate_equation()
        self._build_ui()
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _generate_equation(self):
        if self.difficulty == "easy":
            a = random.randint(10, 50)
            b = random.randint(5, 40)
            op = random.choice(["+", "-"])
            if op == "-" and a < b:
                a, b = b, a
            self.equation_str = f"{a} {op} {b}"
            self.correct_answer = a + b if op == "+" else a - b
        elif self.difficulty == "hard":
            a = random.randint(12, 40)
            b = random.randint(3, 9)
            c = random.randint(15, 60)
            self.equation_str = f"({a} × {b}) + {c}"
            self.correct_answer = (a * b) + c
        else:  # medium
            a = random.randint(15, 65)
            b = random.randint(15, 55)
            c = random.randint(5, 30)
            op = random.choice(["+", "-"])
            if op == "+":
                self.equation_str = f"{a} + {b} - {c}"
                self.correct_answer = a + b - c
            else:
                self.equation_str = f"{a + b} - {b} + {c}"
                self.correct_answer = a + c

    def _build_ui(self):
        pad_frame = tk.Frame(self, bg=self["bg"], padx=25, pady=20)
        pad_frame.pack(fill="both", expand=True)

        # Icon and Title
        header = tk.Label(
            pad_frame,
            text="🧠 Wake-Up Math Challenge",
            font=("Segoe UI", 14, "bold"),
            bg=self["bg"],
            fg=self.theme.get("accent_light", "#C4B5FD")
        )
        header.pack(pady=(0, 6))

        sub = tk.Label(
            pad_frame,
            text="Solve the arithmetic equation to confirm you are awake!",
            font=("Segoe UI", 9),
            bg=self["bg"],
            fg=self.theme.get("text_secondary", "#94A3B8")
        )
        sub.pack(pady=(0, 16))

        # Equation Card
        eq_card = tk.Frame(
            pad_frame,
            bg=self.theme.get("bg_card", "#162032"),
            highlightbackground=self.theme.get("border", "#24324D"),
            highlightthickness=1,
            padx=20,
            pady=16
        )
        eq_card.pack(fill="x", pady=6)

        self.eq_label = tk.Label(
            eq_card,
            text=f"{self.equation_str} = ?",
            font=("Segoe UI", 24, "bold"),
            bg=self.theme.get("bg_card", "#162032"),
            fg=self.theme.get("text_primary", "#F8FAFC")
        )
        self.eq_label.pack()

        # Input Row
        input_frame = tk.Frame(pad_frame, bg=self["bg"])
        input_frame.pack(fill="x", pady=(12, 6))

        self.answer_entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 16, "bold"),
            justify="center",
            bg=self.theme.get("bg_input", "#111827"),
            fg=self.theme.get("text_primary", "#F8FAFC"),
            insertbackground="#FFFFFF",
            highlightthickness=1,
            highlightbackground=self.theme.get("border", "#24324D"),
            highlightcolor=self.theme.get("accent", "#8B5CF6"),
            relief="flat"
        )
        self.answer_entry.pack(ipady=4, fill="x")
        self.answer_entry.focus_set()
        self.answer_entry.bind("<Return>", lambda e: self._verify())

        # Feedback Message
        self.msg_label = tk.Label(
            pad_frame,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg=self["bg"],
            fg=self.theme.get("danger", "#EF4444")
        )
        self.msg_label.pack(pady=4)

        # Buttons Row
        btn_frame = tk.Frame(pad_frame, bg=self["bg"])
        btn_frame.pack(fill="x", pady=(4, 0))

        ModernButton(
            btn_frame,
            self.theme,
            text="Verify & Dismiss Alarm",
            command=self._verify,
            variant="success"
        ).pack(fill="x")

    def _verify(self):
        val = self.answer_entry.get().strip()
        try:
            user_ans = int(val)
            if user_ans == self.correct_answer:
                self.is_solved = True
                self.msg_label.configure(
                    text="✓ Correct! Good morning!",
                    fg=self.theme.get("success", "#10B981")
                )
                self.after(500, self._finish_success)
            else:
                self.msg_label.configure(
                    text="✗ Incorrect answer! Try again.",
                    fg=self.theme.get("danger", "#EF4444")
                )
                self.answer_entry.delete(0, "end")
        except ValueError:
            self.msg_label.configure(
                text="Please enter a valid number.",
                fg=self.theme.get("danger", "#EF4444")
            )

    def _finish_success(self):
        if self.on_success:
            self.on_success()
        self.destroy()


class AlarmTriggerDialog(tk.Toplevel):
    """
    Dedicated fullscreen or prominent alarm ringing modal popup.
    Features glowing animation, alarm time, label, snooze, and dismiss.
    """
    def __init__(self, parent, theme: Dict[str, str], alarm_data: Dict[str, Any],
                 on_snooze: Callable[[Dict[str, Any]], None],
                 on_dismiss: Callable[[Dict[str, Any]], None],
                 math_enabled: bool = True, math_difficulty: str = "medium"):
        super().__init__(parent)
        self.theme = theme
        self.alarm_data = alarm_data
        self.on_snooze = on_snooze
        self.on_dismiss = on_dismiss
        self.math_enabled = math_enabled
        self.math_difficulty = math_difficulty

        self.title("⏰ ALARM RINGING – SleepSync")
        self.geometry("520x420")
        self.resizable(False, False)
        self.configure(bg=theme.get("bg_root", "#0B0F19"))
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self._on_close_attempt)

        self._pulse_state = 0
        self._build_ui()
        self._animate_pulse()
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _on_close_attempt(self):
        # Do not close window silently without snoozing or dismissing!
        self._handle_snooze()

    def _build_ui(self):
        pad = tk.Frame(self, bg=self["bg"], padx=30, pady=25)
        pad.pack(fill="both", expand=True)

        # Pulsing icon label
        self.icon_label = tk.Label(
            pad,
            text="⏰",
            font=("Segoe UI Emoji", 42),
            bg=self["bg"],
            fg=self.theme.get("accent_light", "#C4B5FD")
        )
        self.icon_label.pack(pady=(5, 5))

        # Time banner
        hour = self.alarm_data.get("hour", 7)
        minute = self.alarm_data.get("minute", 0)
        period = "AM" if hour < 12 else "PM"
        disp_h = hour % 12
        if disp_h == 0:
            disp_h = 12
        time_str = f"{disp_h}:{minute:02d} {period}"

        self.time_label = tk.Label(
            pad,
            text=time_str,
            font=("Segoe UI", 36, "bold"),
            bg=self["bg"],
            fg=self.theme.get("text_primary", "#F8FAFC")
        )
        self.time_label.pack()

        # Alarm Label
        label_text = self.alarm_data.get("label", "Morning Alarm")
        self.label_lbl = tk.Label(
            pad,
            text=f"🔔 {label_text}",
            font=("Segoe UI", 14),
            bg=self["bg"],
            fg=self.theme.get("accent_light", "#C4B5FD")
        )
        self.label_lbl.pack(pady=(4, 15))

        # Card container for actions
        card = tk.Frame(
            pad,
            bg=self.theme.get("bg_card", "#162032"),
            highlightbackground=self.theme.get("border", "#24324D"),
            highlightthickness=1,
            padx=20,
            pady=18
        )
        card.pack(fill="x")

        snooze_dur = self.alarm_data.get("snooze_duration", 10)
        snooze_text = f"Snooze ({snooze_dur} mins)"
        
        btn_row = tk.Frame(card, bg=card["bg"])
        btn_row.pack(fill="x")

        # Snooze button
        ModernButton(
            btn_row,
            self.theme,
            text=f"💤 {snooze_text}",
            command=self._handle_snooze,
            variant="secondary",
            font_size=11,
            padx=16,
            pady=10
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Dismiss button
        ModernButton(
            btn_row,
            self.theme,
            text="✓ Dismiss Alarm",
            command=self._handle_dismiss,
            variant="primary",
            font_size=11,
            padx=16,
            pady=10
        ).pack(side="right", fill="x", expand=True, padx=(8, 0))

        if self.math_enabled:
            note_lbl = tk.Label(
                card,
                text="🧠 Math challenge required to dismiss",
                font=("Segoe UI", 8),
                bg=card["bg"],
                fg=self.theme.get("text_muted", "#64748B")
            )
            note_lbl.pack(pady=(10, 0))

    def _animate_pulse(self):
        """Pulsing glow animation on alarm icon."""
        colors = [
            self.theme.get("accent_light", "#C4B5FD"),
            self.theme.get("accent", "#8B5CF6"),
            self.theme.get("warning", "#F59E0B"),
            self.theme.get("accent", "#8B5CF6")
        ]
        self._pulse_state = (self._pulse_state + 1) % len(colors)
        if self.winfo_exists():
            self.icon_label.configure(fg=colors[self._pulse_state])
            self.after(450, self._animate_pulse)

    def _handle_snooze(self):
        self.on_snooze(self.alarm_data)
        self.destroy()

    def _handle_dismiss(self):
        if self.math_enabled:
            # Open Math Challenge
            MathChallengeDialog(
                self,
                self.theme,
                difficulty=self.math_difficulty,
                on_success=self._final_dismiss
            )
        else:
            self._final_dismiss()

    def _final_dismiss(self):
        self.on_dismiss(self.alarm_data)
        self.destroy()


class BedtimeReminderDialog(tk.Toplevel):
    """
    Soothing bedtime wind-down notification popup.
    """
    def __init__(self, parent, theme: Dict[str, str], lead_mins: int = 30,
                 on_play_music: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        self.theme = theme
        self.lead_mins = lead_mins
        self.on_play_music = on_play_music

        self.title("🌙 Bedtime Wind-Down – SleepSync")
        self.geometry("450x260")
        self.resizable(False, False)
        self.configure(bg=theme.get("bg_root", "#0B0F19"))
        self.attributes("-topmost", True)

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

        tk.Label(
            pad,
            text="🌙 Time to Wind Down",
            font=("Segoe UI", 16, "bold"),
            bg=self["bg"],
            fg=self.theme.get("accent_light", "#C4B5FD")
        ).pack(pady=(0, 6))

        tk.Label(
            pad,
            text=f"Your scheduled bedtime is in {self.lead_mins} minutes.\n"
                 "Dim bright room lights, put screens away, and begin your night routine.",
            font=("Segoe UI", 10),
            bg=self["bg"],
            fg=self.theme.get("text_secondary", "#94A3B8"),
            justify="center"
        ).pack(pady=(0, 18))

        btn_row = tk.Frame(pad, bg=self["bg"])
        btn_row.pack(fill="x")

        ModernButton(
            btn_row,
            self.theme,
            text="🎵 Play Soothing Sleep Music",
            command=self._handle_music,
            variant="primary",
            font_size=10
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ModernButton(
            btn_row,
            self.theme,
            text="Got It",
            command=self.destroy,
            variant="secondary",
            font_size=10
        ).pack(side="right", fill="x", expand=True, padx=(6, 0))

    def _handle_music(self):
        if self.on_play_music:
            self.on_play_music()
        self.destroy()
