"""
SleepSync - Analytics & Goals View
Embedded Matplotlib visualizations for weekly sleep duration vs goals,
trend analytics, consistency score, and KPI metrics.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ui_components import CardFrame, StatCard, ModernButton
from analytics import AnalyticsEngine
from settings import SettingsManager


class AnalyticsView(tk.Frame):
    def __init__(self, parent, theme: Dict[str, str],
                 analytics_engine: AnalyticsEngine,
                 settings_mgr: SettingsManager):
        super().__init__(parent, bg=theme.get("bg_root", "#0B0F19"))
        self.theme = theme
        self.analytics_engine = analytics_engine
        self.settings_mgr = settings_mgr

        self.chart_canvas_1 = None
        self.chart_canvas_2 = None

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
            text="📊 Sleep Goals & Analytics",
            font=("Segoe UI", 20, "bold"),
            bg=self["bg"],
            fg=self.theme.get("text_primary", "#F8FAFC")
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Deep insights into your sleep duration, consistency, and goal adherence",
            font=("Segoe UI", 10),
            bg=self["bg"],
            fg=self.theme.get("text_secondary", "#94A3B8")
        ).pack(anchor="w", pady=(2, 0))

        # 1. GOAL CONFIGURATION HERO CARD
        goal_card = CardFrame(pad_container, self.theme, padx=18, pady=14)
        goal_card.pack(fill="x", pady=(0, 18))

        g_left = tk.Frame(goal_card, bg=goal_card["bg"])
        g_left.pack(side="left", anchor="w")

        tk.Label(
            g_left,
            text="🎯 DAILY SLEEP GOAL",
            font=("Segoe UI", 9, "bold"),
            bg=goal_card["bg"],
            fg=self.theme.get("text_muted", "#64748B")
        ).pack(anchor="w")

        self.lbl_goal_status = tk.Label(
            g_left,
            text="Current Goal: 8.0 Hours / Night",
            font=("Segoe UI", 15, "bold"),
            bg=goal_card["bg"],
            fg=self.theme.get("text_primary", "#F8FAFC")
        )
        self.lbl_goal_status.pack(anchor="w", pady=(2, 0))

        g_right = tk.Frame(goal_card, bg=goal_card["bg"])
        g_right.pack(side="right", anchor="e")

        tk.Label(g_right, text="Set Goal:", font=("Segoe UI", 9), bg=goal_card["bg"], fg=self.theme.get("text_secondary", "#94A3B8")).pack(side="left", padx=(0, 6))

        goal_values = ["6.0", "6.5", "7.0", "7.5", "8.0", "8.5", "9.0", "9.5", "10.0"]
        self.var_goal_select = tk.StringVar(value=str(self.settings_mgr.sleep_goal_hours))
        cb_goal = ttk.Combobox(g_right, textvariable=self.var_goal_select, values=goal_values, width=5, state="readonly")
        cb_goal.pack(side="left", padx=(0, 8))

        ModernButton(
            g_right, self.theme,
            text="Update Goal",
            command=self._update_goal,
            variant="primary",
            font_size=9,
            padx=10,
            pady=4
        ).pack(side="left")

        # 2. METRICS OVERVIEW (4 Cards)
        stats_row = tk.Frame(pad_container, bg=self["bg"])
        stats_row.pack(fill="x", pady=(0, 20))
        for i in range(4):
            stats_row.grid_columnconfigure(i, weight=1, uniform="analytics_cards")

        self.card_avg = StatCard(stats_row, self.theme, icon="📈", title="Weekly Avg", value="--", subtitle="Hours/night")
        self.card_avg.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.card_longest = StatCard(stats_row, self.theme, icon="🏆", title="Longest Sleep", value="--", subtitle="Single session", accent_color=self.theme.get("success", "#10B981"))
        self.card_longest.grid(row=0, column=1, sticky="nsew", padx=4)

        self.card_shortest = StatCard(stats_row, self.theme, icon="⚡", title="Shortest Sleep", value="--", subtitle="Single session", accent_color=self.theme.get("warning", "#F59E0B"))
        self.card_shortest.grid(row=0, column=2, sticky="nsew", padx=4)

        self.card_quality = StatCard(stats_row, self.theme, icon="⭐", title="Quality Rating", value="--", subtitle="Average rating", accent_color=self.theme.get("accent_light", "#C4B5FD"))
        self.card_quality.grid(row=0, column=3, sticky="nsew", padx=(8, 0))

        # 3. CHARTS CONTAINER (Two full-width modern charts)
        # Chart 1: Weekly Sleep Duration
        chart1_card = CardFrame(pad_container, self.theme, padx=16, pady=14)
        chart1_card.pack(fill="x", pady=(0, 16))

        tk.Label(
            chart1_card,
            text="📊 Past 7 Days Sleep Duration vs Target Goal",
            font=("Segoe UI", 12, "bold"),
            bg=chart1_card["bg"],
            fg=self.theme.get("text_primary", "#F8FAFC")
        ).pack(anchor="w", pady=(0, 8))

        self.chart_container_1 = tk.Frame(chart1_card, bg=chart1_card["bg"])
        self.chart_container_1.pack(fill="both", expand=True)

        # Chart 2: Sleep Quality Trend
        chart2_card = CardFrame(pad_container, self.theme, padx=16, pady=14)
        chart2_card.pack(fill="x", pady=(0, 20))

        tk.Label(
            chart2_card,
            text="⭐ Sleep Quality & Restfulness Trends",
            font=("Segoe UI", 12, "bold"),
            bg=chart2_card["bg"],
            fg=self.theme.get("text_primary", "#F8FAFC")
        ).pack(anchor="w", pady=(0, 8))

        self.chart_container_2 = tk.Frame(chart2_card, bg=chart2_card["bg"])
        self.chart_container_2.pack(fill="both", expand=True)

    def _update_goal(self):
        try:
            val = float(self.var_goal_select.get())
            self.settings_mgr.set("sleep_goal_hours", str(val))
            messagebox.showinfo("Goal Updated", f"Daily sleep goal updated to {val} hours!")
            self.refresh()
        except ValueError:
            pass

    def refresh(self):
        goal = self.settings_mgr.sleep_goal_hours
        self.lbl_goal_status.configure(text=f"Current Goal: {goal} Hours / Night")
        self.var_goal_select.set(str(goal))

        stats = self.analytics_engine.get_summary_stats(goal)
        if stats["has_data"]:
            self.card_avg.update_data(f"{stats['weekly_avg_hours']}h", "7-day average")
            self.card_longest.update_data(f"{stats['longest_session_hours']}h", "Personal record")
            self.card_shortest.update_data(f"{stats['shortest_session_hours']}h", "Minimum session")
            self.card_quality.update_data(f"{stats['avg_quality_rating']} ★", "Out of 5.0")
        else:
            self.card_avg.update_data("--", "No logs")
            self.card_longest.update_data("--", "No logs")
            self.card_shortest.update_data("--", "No logs")
            self.card_quality.update_data("--", "No logs")

        # Render Chart 1
        for child in self.chart_container_1.winfo_children():
            child.destroy()
        try:
            fig1 = self.analytics_engine.create_weekly_chart_figure(self.theme, sleep_goal=goal, width=7.5, height=2.8)
            self.chart_canvas_1 = FigureCanvasTkAgg(fig1, master=self.chart_container_1)
            self.chart_canvas_1.draw()
            self.chart_canvas_1.get_tk_widget().pack(fill="both", expand=True)
        except Exception as e:
            print(f"Error rendering chart 1: {e}")

        # Render Chart 2
        for child in self.chart_container_2.winfo_children():
            child.destroy()
        try:
            fig2 = self.analytics_engine.create_quality_trend_figure(self.theme, width=7.5, height=2.4)
            self.chart_canvas_2 = FigureCanvasTkAgg(fig2, master=self.chart_container_2)
            self.chart_canvas_2.draw()
            self.chart_canvas_2.get_tk_widget().pack(fill="both", expand=True)
        except Exception as e:
            print(f"Error rendering chart 2: {e}")
