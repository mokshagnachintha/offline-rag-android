"""
analytics_dashboard.py — Analytics & Health Monitoring Dashboard.

Material Design 3 screen showing:
  • Device memory usage and pressure status
  • Network information
  • Query performance metrics
  • Download history
  • Session statistics
  • Export analytics to CSV
"""
from __future__ import annotations

from datetime import datetime
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.progressbar import ProgressBar
from kivy.clock import mainthread
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle

# ── Material Design 3 Theme ──────────────────────────────────────── #
from ui.theme import MD3Colors, MD3Spacing, MD3Radius, MD3Typography, paint_widget, MD3Button

def _paint(widget, color, radius=0):
    """Bind background color with optional rounded corners."""
    with widget.canvas.before:
        Color(*color)
        rect = RoundedRectangle(radius=[dp(radius)]) if radius else RoundedRectangle()
    widget.bind(
        pos =lambda w, _: setattr(rect, "pos",  w.pos),
        size=lambda w, _: setattr(rect, "size", w.size),
    )
    return rect


# ================================================================== #
#  Metric Card Widget                                                 #
# ================================================================== #

class MetricCard(BoxLayout):
    """Shows a single metric with icon, value, and trend."""
    
    def __init__(self, title: str, value: str, icon: str = "", 
                 unit: str = "", status: str = "normal", **kw):
        """
        Args:
            title: Metric name (e.g., 'Memory Usage')
            value: Current value (e.g., '1024')
            icon: Emoji icon (e.g., '💾')
            unit: Unit of measurement (e.g., 'MB')
            status: 'normal', 'caution', 'critical', 'success'
        """
        super().__init__(
            orientation="vertical",
            size_hint=(1, None),
            padding=[MD3Spacing.MD, MD3Spacing.MD],
            spacing=MD3Spacing.SM,
            height=dp(120),
            **kw,
        )
        _paint(self, MD3Colors.SURFACE_VARIANT, radius=MD3Radius.LARGE)
        
        # Status indicator color
        status_color = {
            "normal": MD3Colors.PRIMARY,
            "caution": MD3Colors.WARNING,
            "critical": MD3Colors.ERROR,
            "success": MD3Colors.SUCCESS,
        }.get(status, MD3Colors.PRIMARY)
        
        # Header: icon + title
        header = BoxLayout(size_hint=(1, None), height=dp(28), spacing=MD3Spacing.SM)
        if icon:
            header.add_widget(Label(
                text=icon, size_hint=(None, 1), width=dp(28),
                font_size=sp(16), halign="center", valign="middle",
            ))
        header.add_widget(Label(
            text=title, size_hint=(1, 1),
            font_size=sp(12), color=MD3Colors.ON_SURFACE_VARIANT,
            halign="left", valign="middle",
        ))
        self.add_widget(header)
        
        # Value display
        value_box = BoxLayout(size_hint=(1, None), height=dp(36), spacing=dp(4))
        value_box.add_widget(Label(
            text=value, size_hint=(1, 1),
            font_size=sp(28), bold=True, color=status_color,
            halign="left", valign="bottom",
        ))
        if unit:
            value_box.add_widget(Label(
                text=unit, size_hint=(None, 1), width=dp(32),
                font_size=sp(12), color=MD3Colors.ON_SURFACE_VARIANT,
                halign="left", valign="bottom",
            ))
        self.add_widget(value_box)
        
        # Spacer
        self.add_widget(Widget(size_hint=(1, None), height=dp(8)))


# ================================================================== #
#  Health Status Card                                                 #
# ================================================================== #

class HealthStatusCard(BoxLayout):
    """Shows device health with pressure indicator."""
    
    def __init__(self, **kw):
        super().__init__(
            orientation="vertical",
            size_hint=(1, None), height=dp(140),
            padding=[MD3Spacing.MD, MD3Spacing.MD],
            spacing=MD3Spacing.MD,
            **kw,
        )
        _paint(self, MD3Colors.SECONDARY, radius=MD3Radius.LARGE)
        
        # Header
        header = Label(
            text="🏥 Device Health Status",
            size_hint=(1, None), height=dp(24),
            font_size=sp(14), bold=True, color=MD3Colors.ON_SECONDARY,
            halign="left", valign="middle",
        )
        self.add_widget(header)
        
        # Memory pressure display
        pressure_box = BoxLayout(size_hint=(1, None), height=dp(36), spacing=MD3Spacing.MD)
        
        self._pressure_lbl = Label(
            text="NORMAL", size_hint=(None, 1), width=dp(80),
            font_size=sp(12), bold=True, color=MD3Colors.SUCCESS,
            halign="center", valign="middle",
        )
        pressure_box.add_widget(self._pressure_lbl)
        
        self._pressure_bar = ProgressBar(
            max=100, value=30,
            size_hint=(1, 1),
        )
        pressure_box.add_widget(self._pressure_bar)
        
        self.add_widget(pressure_box)
        
        # Status details
        details = BoxLayout(size_hint=(1, None), height=dp(64), spacing=MD3Spacing.MD)
        
        self._mem_detail = Label(
            text="Memory: calculating...",
            size_hint=(1, None), height=dp(32),
            font_size=sp(11), color=MD3Colors.ON_SECONDARY,
            halign="left", valign="top",
        )
        self._disk_detail = Label(
            text="Storage: calculating...",
            size_hint=(1, None), height=dp(32),
            font_size=sp(11), color=MD3Colors.ON_SECONDARY,
            halign="left", valign="top",
        )
        
        detail_col = BoxLayout(orientation="vertical", size_hint=(1, 1), spacing=MD3Spacing.SM)
        detail_col.add_widget(self._mem_detail)
        detail_col.add_widget(self._disk_detail)
        details.add_widget(detail_col)
        
        self.add_widget(details)
        
        # Refresh data
        self.update_health()
    
    def update_health(self):
        """Update health status from HealthMonitor."""
        try:
            from analytics import get_health_monitor
            health = get_health_monitor()
            report = health.get_full_report()
            
            # Parse pressure
            pressure = report.get("memory_pressure", "NORMAL")
            pressure_pct = {
                "NORMAL": 30,
                "CAUTION": 65,
                "CRITICAL": 100,
            }.get(pressure, 30)
            
            color = {
                "NORMAL": MD3Colors.SUCCESS,
                "CAUTION": MD3Colors.WARNING,
                "CRITICAL": MD3Colors.ERROR,
            }.get(pressure, MD3Colors.PRIMARY)
            
            self._pressure_lbl.text = pressure
            self._pressure_lbl.color = color
            self._pressure_bar.value = pressure_pct
            
            mem_avail_mb = report.get("available_memory_mb", 0)
            disk_avail_gb = report.get("available_storage_gb", 0)
            
            self._mem_detail.text = f"Memory: {mem_avail_mb:.0f} MB available"
            self._disk_detail.text = f"Storage: {disk_avail_gb:.1f} GB free"
        except Exception:
            self._mem_detail.text = "Memory: unavailable"
            self._disk_detail.text = "Storage: unavailable"


# ================================================================== #
#  Session Stats Card                                                 #
# ================================================================== #

class SessionStatsCard(BoxLayout):
    """Shows current session statistics."""
    
    def __init__(self, **kw):
        super().__init__(
            orientation="vertical",
            size_hint=(1, None), height=dp(160),
            padding=[MD3Spacing.MD, MD3Spacing.MD],
            spacing=MD3Spacing.MD,
            **kw,
        )
        _paint(self, MD3Colors.TERTIARY, radius=MD3Radius.LARGE)
        
        # Header
        header = Label(
            text="📊 Session Statistics",
            size_hint=(1, None), height=dp(24),
            font_size=sp(14), bold=True, color=MD3Colors.ON_TERTIARY,
            halign="left", valign="middle",
        )
        self.add_widget(header)
        
        # Stats grid (2 columns, 3 rows)
        grid = GridLayout(
            cols=2, size_hint=(1, None), height=dp(110),
            spacing=MD3Spacing.SM, padding=[0, MD3Spacing.SM],
        )
        
        # Query stats
        self._query_count = Label(
            text="Queries: 0",
            size_hint=(1, None), height=dp(32),
            font_size=sp(11), color=MD3Colors.ON_TERTIARY,
            halign="left", valign="middle",
        )
        self._avg_latency = Label(
            text="Avg Latency: 0.0s",
            size_hint=(1, None), height=dp(32),
            font_size=sp(11), color=MD3Colors.ON_TERTIARY,
            halign="left", valign="middle",
        )
        self._cache_hits = Label(
            text="Cache Hits: 0%",
            size_hint=(1, None), height=dp(32),
            font_size=sp(11), color=MD3Colors.ON_TERTIARY,
            halign="left", valign="middle",
        )
        self._uptime = Label(
            text="Uptime: 0m",
            size_hint=(1, None), height=dp(32),
            font_size=sp(11), color=MD3Colors.ON_TERTIARY,
            halign="left", valign="middle",
        )
        
        grid.add_widget(self._query_count)
        grid.add_widget(self._avg_latency)
        grid.add_widget(self._cache_hits)
        grid.add_widget(self._uptime)
        
        self.add_widget(grid)
        
        # Refresh data
        self.update_stats()
    
    def update_stats(self):
        """Update statistics from AnalyticsCollector."""
        try:
            from analytics import get_analytics
            analytics = get_analytics()
            
            session_stats = analytics.get_session_metrics()
            query_stats = analytics.get_query_stats()
            
            self._query_count.text = f"Queries: {session_stats.get('total_queries', 0)}"
            
            avg_latency = session_stats.get('avg_query_latency_ms', 0)
            self._avg_latency.text = f"Avg Latency: {avg_latency/1000:.1f}s"
            
            cache_hit_pct = query_stats.get('cache_hit_percentage', 0)
            self._cache_hits.text = f"Cache Hits: {cache_hit_pct:.0f}%"
            
            uptime_sec = session_stats.get('session_duration_sec', 0)
            uptime_min = uptime_sec // 60
            self._uptime.text = f"Uptime: {uptime_min}m"
        except Exception:
            self._query_count.text = "Queries: —"
            self._avg_latency.text = "Avg Latency: —"
            self._cache_hits.text = "Cache Hits: —"
            self._uptime.text = "Uptime: —"


# ================================================================== #
#  Analytics Dashboard Screen                                         #
# ================================================================== #

class AnalyticsDashboardScreen(Screen):
    """Main analytics and health monitoring dashboard."""
    
    def __init__(self, **kw):
        super().__init__(**kw)
        self._build_ui()
    
    def on_enter(self, *_):
        """Refresh all metrics when screen is displayed."""
        self._refresh_all()
    
    def _build_ui(self):
        """Build the complete UI layout."""
        root = BoxLayout(orientation="vertical")
        _paint(root, MD3Colors.BG_PRIMARY)
        
        # ── Header ────────────────────────────────────────────────── #
        header = BoxLayout(
            size_hint=(1, None), height=dp(54),
            padding=[MD3Spacing.MD, 0],
        )
        _paint(header, MD3Colors.BG_SECONDARY)
        header.add_widget(Label(
            text="[b]📈 Analytics[/b]", markup=True,
            color=MD3Colors.ON_SURFACE, font_size=sp(16),
            halign="center", valign="middle",
        ))
        root.add_widget(header)
        
        # Separator
        sep = Widget(size_hint=(1, None), height=dp(1))
        _paint(sep, MD3Colors.OUTLINE_VARIANT)
        root.add_widget(sep)
        
        # ── Scrollable content ──────────────────────────────────── #
        scroll = ScrollView(size_hint=(1, 1))
        _paint(scroll, MD3Colors.BG_PRIMARY)
        
        content = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            spacing=MD3Spacing.MD,
            padding=[MD3Spacing.MD, MD3Spacing.MD],
        )
        content.bind(minimum_height=content.setter("height"))
        
        # Device Health Status
        self._health_card = HealthStatusCard()
        content.add_widget(self._health_card)
        
        # Memory Metrics (grid of metric cards)
        memory_section = Label(
            text="💾 Memory",
            size_hint=(1, None), height=dp(22),
            font_size=sp(12), bold=True, color=MD3Colors.PRIMARY,
            halign="left", valign="middle",
        )
        content.add_widget(memory_section)
        
        memory_grid = GridLayout(
            cols=2, size_hint=(1, None), height=dp(140),
            spacing=MD3Spacing.MD, padding=[0, 0],
        )
        
        self._mem_used_card = MetricCard(
            "Memory Used", "calculating...", 
            icon="📊", unit="MB", status="normal"
        )
        self._mem_available_card = MetricCard(
            "Available", "calculating...",
            icon="💚", unit="MB", status="normal"
        )
        
        memory_grid.add_widget(self._mem_used_card)
        memory_grid.add_widget(self._mem_available_card)
        content.add_widget(memory_grid)
        
        # Query Performance Section
        query_section = Label(
            text="⏱ Query Performance",
            size_hint=(1, None), height=dp(22),
            font_size=sp(12), bold=True, color=MD3Colors.PRIMARY,
            halign="left", valign="middle",
        )
        content.add_widget(query_section)
        
        query_grid = GridLayout(
            cols=2, size_hint=(1, None), height=dp(140),
            spacing=MD3Spacing.MD, padding=[0, 0],
        )
        
        self._avg_latency_card = MetricCard(
            "Avg Latency", "calculating...",
            icon="⏱", unit="ms", status="normal"
        )
        self._cache_rate_card = MetricCard(
            "Cache Hit Rate", "calculating...",
            icon="✅", unit="%", status="normal"
        )
        
        query_grid.add_widget(self._avg_latency_card)
        query_grid.add_widget(self._cache_rate_card)
        content.add_widget(query_grid)
        
        # Session Stats
        self._session_card = SessionStatsCard()
        content.add_widget(self._session_card)
        
        # Export button
        export_btn = Button(
            text="📥  Export Analytics (CSV)",
            size_hint=(1, None), height=dp(48),
            font_size=sp(13), bold=True,
            background_normal="", background_color=MD3Colors.PRIMARY,
            color=MD3Colors.ON_PRIMARY,
        )
        _paint(export_btn, MD3Colors.PRIMARY, radius=MD3Radius.LARGE)
        export_btn.bind(on_release=self._on_export)
        
        export_box = BoxLayout(
            size_hint=(1, None), height=dp(56),
            padding=[0, MD3Spacing.MD],
        )
        export_box.add_widget(export_btn)
        content.add_widget(export_box)
        
        # Spacer
        content.add_widget(Widget(size_hint=(1, None), height=dp(20)))
        
        scroll.add_widget(content)
        root.add_widget(scroll)
        
        self.add_widget(root)
    
    def _refresh_all(self):
        """Refresh all metric cards."""
        try:
            from analytics import get_analytics, get_health_monitor
            
            analytics = get_analytics()
            health = get_health_monitor()
            
            # Update health card
            self._health_card.update_health()
            
            # Update session card
            self._session_card.update_stats()
            
            # Update memory cards
            report = health.get_full_report()
            mem_used = report.get("memory_used_mb", 0)
            mem_avail = report.get("available_memory_mb", 0)
            
            status = report.get("memory_pressure", "NORMAL")
            status_map = {"NORMAL": "normal", "CAUTION": "caution", "CRITICAL": "critical"}
            status_display = status_map.get(status, "normal")
            
            self._mem_used_card.children[1].text = f"{mem_used:.0f}"
            self._mem_used_card.children[1].children[0].color = {
                "normal": MD3Colors.PRIMARY,
                "caution": MD3Colors.WARNING,
                "critical": MD3Colors.ERROR,
            }.get(status_display, MD3Colors.PRIMARY)
            
            self._mem_available_card.children[1].text = f"{mem_avail:.0f}"
            
            # Update query cards
            query_stats = analytics.get_query_stats()
            avg_latency = query_stats.get("average_latency_ms", 0)
            cache_hit_pct = query_stats.get("cache_hit_percentage", 0)
            
            self._avg_latency_card.children[1].text = f"{avg_latency:.0f}"
            self._cache_rate_card.children[1].text = f"{cache_hit_pct:.0f}"
            
        except Exception as e:
            print(f"[dashboard] Error refreshing metrics: {e}")
    
    def _on_export(self, *_):
        """Export analytics data to CSV."""
        try:
            from analytics import get_analytics
            from datetime import datetime
            import os
            
            analytics = get_analytics()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analytics_{timestamp}.csv"
            
            # Try to export to accessible location
            try:
                android_dir = os.environ.get("ANDROID_PRIVATE")
                if android_dir:
                    filepath = os.path.join(android_dir, filename)
                else:
                    filepath = os.path.join(os.path.expanduser("~"), "Desktop", filename)
            except Exception:
                filepath = filename
            
            analytics.export_to_csv(filepath)
            self._show_status(f"✅ Exported to: {os.path.basename(filepath)}", MD3Colors.SUCCESS)
        except Exception as e:
            self._show_status(f"❌ Export failed: {str(e)}", MD3Colors.ERROR)
    
    def _show_status(self, message: str, color):
        """Show temporary status message."""
        from kivy.clock import Clock
        
        # Could add a toast/snackbar here
        print(f"[toast] {message} (color={color})")
