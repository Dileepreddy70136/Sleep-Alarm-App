"""
SleepSync - Analytics & Sleep Goals Module
Calculates sleep metrics and renders custom-styled Matplotlib visualizations
integrated seamlessly into Tkinter.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from database import Database


class AnalyticsEngine:
    def __init__(self, db: Database):
        self.db = db

    def get_summary_stats(self, sleep_goal_hours: float = 8.0) -> Dict[str, Any]:
        """
        Calculate key sleep performance indicators:
        - today_sleep_hours
        - weekly_avg_hours
        - all_time_avg_hours
        - longest_session_hours
        - shortest_session_hours
        - goal_completion_pct
        - avg_quality_rating
        - total_nights_logged
        """
        all_records = self.db.get_all_sleep_records()
        if not all_records:
            return {
                "has_data": False,
                "today_sleep_hours": 0.0,
                "weekly_avg_hours": 0.0,
                "all_time_avg_hours": 0.0,
                "longest_session_hours": 0.0,
                "shortest_session_hours": 0.0,
                "goal_completion_pct": 0.0,
                "avg_quality_rating": 0.0,
                "total_nights_logged": 0,
            }

        # 1. Today's sleep
        today_date = datetime.now().strftime("%Y-%m-%d")
        today_mins = sum(r["duration_minutes"] for r in all_records if r["end_time"].startswith(today_date))
        today_hours = round(today_mins / 60.0, 1)

        # 2. Last 7 days records
        cutoff_7d = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")
        recent_7d = [r for r in all_records if r["start_time"] >= cutoff_7d]
        if recent_7d:
            weekly_avg = round(sum(r["duration_minutes"] for r in recent_7d) / len(recent_7d) / 60.0, 1)
        else:
            weekly_avg = 0.0

        # 3. All-time stats
        durations = [r["duration_minutes"] for r in all_records]
        all_time_avg = round(sum(durations) / len(durations) / 60.0, 1)
        longest = round(max(durations) / 60.0, 1)
        shortest = round(min(durations) / 60.0, 1)

        # 4. Goal completion percentage
        goal_minutes = sleep_goal_hours * 60.0
        met_goal_count = sum(1 for d in durations if d >= (goal_minutes - 15))  # 15m grace window
        completion_pct = round((met_goal_count / len(durations)) * 100.0, 1)

        # 5. Quality rating
        qualities = [r.get("quality_rating", 4) for r in all_records]
        avg_quality = round(sum(qualities) / len(qualities), 1)

        return {
            "has_data": True,
            "today_sleep_hours": today_hours,
            "weekly_avg_hours": weekly_avg,
            "all_time_avg_hours": all_time_avg,
            "longest_session_hours": longest,
            "shortest_session_hours": shortest,
            "goal_completion_pct": completion_pct,
            "avg_quality_rating": avg_quality,
            "total_nights_logged": len(all_records),
        }

    def get_past_7_days_daily_data(self) -> List[Dict[str, Any]]:
        """
        Aggregate sleep by each of the past 7 days (today down to 6 days ago).
        Returns list of dicts: [{'day': 'Mon', 'date': '10/19', 'hours': 7.5, 'date_str': '2026-10-19'}]
        """
        now = datetime.now()
        days_data = []

        # Last 7 days chronologically
        for i in range(6, -1, -1):
            target_date = (now - timedelta(days=i)).date()
            date_str = target_date.strftime("%Y-%m-%d")
            day_name = target_date.strftime("%a")  # Mon, Tue, etc.
            short_date = target_date.strftime("%m/%d")

            # Find all records ending on this target date
            all_records = self.db.get_all_sleep_records()
            day_mins = sum(r["duration_minutes"] for r in all_records if r["end_time"].startswith(date_str))
            day_hours = round(day_mins / 60.0, 1)

            days_data.append({
                "day": day_name,
                "date": short_date,
                "date_str": date_str,
                "hours": day_hours
            })

        return days_data

    # ==========================
    # MATPLOTLIB CHART FACTORIES
    # ==========================

    def create_weekly_chart_figure(self, theme: Dict[str, str], sleep_goal: float = 8.0,
                                   width: float = 6.2, height: float = 2.8) -> Figure:
        """
        Create a Matplotlib figure for the Weekly Sleep Duration chart matching the theme.
        """
        days_data = self.get_past_7_days_daily_data()
        
        fig = Figure(figsize=(width, height), dpi=100)
        fig.patch.set_facecolor(theme.get("bg_card", "#162032"))
        
        ax = fig.add_subplot(111)
        ax.set_facecolor(theme.get("bg_card", "#162032"))

        labels = [f"{d['day']}\n{d['date']}" for d in days_data]
        hours = [d["hours"] for d in days_data]

        # Bar colors: highlight when goal is met or approached
        bar_colors = []
        for h in hours:
            if h >= sleep_goal:
                bar_colors.append(theme.get("success", "#10B981"))
            elif h >= (sleep_goal * 0.75):
                bar_colors.append(theme.get("accent", "#8B5CF6"))
            elif h > 0:
                bar_colors.append(theme.get("accent_light", "#C4B5FD"))
            else:
                bar_colors.append(theme.get("chart_grid", "#24324D"))

        # Render bars
        bars = ax.bar(labels, hours, color=bar_colors, width=0.55, edgecolor="none", zorder=3)

        # Goal target reference line
        ax.axhline(y=sleep_goal, color=theme.get("warning", "#F59E0B"), linestyle="--",
                   linewidth=1.5, alpha=0.85, zorder=4, label=f"Goal: {sleep_goal}h")

        # Display numeric values above non-zero bars
        for bar, h in zip(bars, hours):
            if h > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    h + 0.25,
                    f"{h}h",
                    ha="center",
                    va="bottom",
                    color=theme.get("text_primary", "#F8FAFC"),
                    fontsize=8.5,
                    fontweight="bold"
                )

        # Styling aesthetics
        max_y = max(max(hours, default=0), sleep_goal) + 2.0
        ax.set_ylim(0, max_y)
        ax.set_ylabel("Hours", color=theme.get("text_secondary", "#94A3B8"), fontsize=9)
        
        # Grid
        ax.grid(axis="y", linestyle=":", color=theme.get("chart_grid", "#24324D"), alpha=0.7, zorder=1)
        ax.set_axisbelow(True)

        # Ticks styling
        ax.tick_params(axis="x", colors=theme.get("text_secondary", "#94A3B8"), labelsize=8.5)
        ax.tick_params(axis="y", colors=theme.get("text_secondary", "#94A3B8"), labelsize=8.5)

        # Spines removal
        for spine in ["top", "right", "left"]:
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color(theme.get("border", "#24324D"))

        # Legend
        ax.legend(loc="upper right", frameon=False,
                  labelcolor=theme.get("text_secondary", "#94A3B8"), fontsize=8)

        fig.tight_layout()
        return fig

    def create_quality_trend_figure(self, theme: Dict[str, str],
                                    width: float = 6.2, height: float = 2.4) -> Figure:
        """
        Create a Matplotlib figure for sleep quality trends.
        """
        records = self.db.get_all_sleep_records(limit=10)
        # Reverse to show chronological order left to right
        records = list(reversed(records))

        fig = Figure(figsize=(width, height), dpi=100)
        fig.patch.set_facecolor(theme.get("bg_card", "#162032"))
        ax = fig.add_subplot(111)
        ax.set_facecolor(theme.get("bg_card", "#162032"))

        if not records:
            ax.text(0.5, 0.5, "No sleep records yet",
                    color=theme.get("text_muted", "#64748B"),
                    ha="center", va="center", fontsize=11)
            ax.axis("off")
            return fig

        labels = []
        qualities = []
        for r in records:
            try:
                dt = datetime.strptime(r["start_time"], "%Y-%m-%d %H:%M:%S")
                labels.append(dt.strftime("%m/%d"))
            except Exception:
                labels.append("Log")
            qualities.append(r.get("quality_rating", 4))

        # Plot line and dots
        ax.plot(labels, qualities, marker="o", markersize=6,
                color=theme.get("accent_light", "#C4B5FD"),
                linewidth=2.2, label="Sleep Quality (1-5★)", zorder=3)

        # Fill under curve
        ax.fill_between(range(len(labels)), qualities, color=theme.get("accent", "#8B5CF6"), alpha=0.2, zorder=2)

        ax.set_ylim(0.5, 5.5)
        ax.set_yticks([1, 2, 3, 4, 5])
        ax.set_yticklabels(["1★", "2★", "3★", "4★", "5★"])
        ax.set_ylabel("Rating", color=theme.get("text_secondary", "#94A3B8"), fontsize=8.5)

        ax.grid(axis="both", linestyle=":", color=theme.get("chart_grid", "#24324D"), alpha=0.6, zorder=1)
        ax.tick_params(axis="x", colors=theme.get("text_secondary", "#94A3B8"), labelsize=8)
        ax.tick_params(axis="y", colors=theme.get("text_secondary", "#94A3B8"), labelsize=8)

        for spine in ["top", "right", "left"]:
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color(theme.get("border", "#24324D"))

        ax.legend(loc="upper left", frameon=False,
                  labelcolor=theme.get("text_secondary", "#94A3B8"), fontsize=8)

        fig.tight_layout()
        return fig
