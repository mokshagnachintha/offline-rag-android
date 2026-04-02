"""
ui/screens/init_screen.py — Beautiful Material Design 3 initialization screen.

Shows model download progress, network status, storage space, and system readiness.
Display is user-friendly with pause/resume, retry, and real-time metrics.
"""
from __future__ import annotations

import time
import threading
from typing import Optional, Callable

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from kivy.clock import Clock, mainthread
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.animation import Animation

from ui.theme import MD3Theme, MD3Colors, MD3Button, MD3Card, MD3Spacing, MD3Radius


# ─────────────────────────────────────────────────────────────────── #
#  Status Stages                                                       #
# ─────────────────────────────────────────────────────────────────── #

class InitStage:
    """Initialization stages."""
    CHECKING = "checking"           # Checking for existing models
    DOWNLOADING_QWEN = "dl_qwen"   # Downloading LLM
    DOWNLOADING_NOMIC = "dl_nomic" # Downloading embeddings
    EXTRACTING = "extracting"       # Extracting bundled models
    VERIFYING = "verifying"         # Verifying checksums
    READY = "ready"                 # Ready to launch


class StatusCard(BoxLayout):
    """Material Design 3 status card showing download progress."""

    def __init__(self, model_name: str, model_size_mb: float, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(220),
            padding=MD3Spacing.MD,
            spacing=MD3Spacing.SM,
            **kwargs
        )
        self.model_name = model_name
        self.model_size_mb = model_size_mb
        self.downloaded_mb = 0.0
        self.is_paused = False

        # Background card styling
        with self.canvas.before:
            Color(*MD3Colors.BG_SECONDARY)
            self._bg_rect = RoundedRectangle(radius=[dp(12)])

        self.bind(pos=self._update_bg, size=self._update_bg)

        # ─────── Header row ──────────────────────────────────────── #
        header = BoxLayout(size_hint=(1, None), height=dp(32), spacing=MD3Spacing.SM)

        # Model icon/emoji
        icon_lbl = Label(
            text="📦" if "qwen" in model_name.lower() else "🔍",
            size_hint=(None, 1),
            width=dp(32),
            font_size=sp(24),
        )
        header.add_widget(icon_lbl)

        # Model name
        name_lbl = Label(
            text=f"[b]{model_name}[/b]",
            markup=True,
            size_hint=(1, 1),
            halign="left",
            valign="center",
            font_size=sp(16),
            bold=True,
            color=MD3Colors.ON_SURFACE,
        )
        header.add_widget(name_lbl)

        self.add_widget(header)

        # ─────── Description ────────────────────────────────────── #
        desc_lbl = Label(
            text=f"{model_size_mb:.0f} MB",
            size_hint=(1, None),
            height=dp(20),
            halign="left",
            font_size=sp(12),
            color=MD3Colors.ON_SURFACE_VARIANT,
        )
        self.add_widget(desc_lbl)

        # ─────── Progress bar ────────────────────────────────────── #
        self._progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint=(1, None),
            height=dp(8),
        )
        # Custom progress bar styling
        with self._progress_bar.canvas.before:
            Color(*MD3Colors.SURFACE_VARIANT)
            self._pb_bg = RoundedRectangle(radius=[dp(4)])

        self._progress_bar.bind(
            pos=lambda w, _: setattr(self._pb_bg, "pos", w.pos),
            size=lambda w, _: setattr(self._pb_bg, "size", w.size),
        )

        with self._progress_bar.canvas:
            Color(*MD3Colors.PRIMARY)
            self._pb_fill = RoundedRectangle(radius=[dp(4)])

        self._progress_bar.bind(
            value=self._update_progress_fill,
            pos=lambda w, _: self._update_progress_fill(),
            size=lambda w, _: self._update_progress_fill(),
        )
        self.add_widget(self._progress_bar)

        # ─────── Metrics row (downloaded / speed / ETA) ──────────── #
        metrics_box = BoxLayout(size_hint=(1, None), height=dp(24), spacing=dp(16))

        self._downloaded_lbl = Label(
            text="0 MB / 0 MB",
            size_hint=(None, 1),
            width=dp(120),
            halign="left",
            font_size=sp(11),
            color=MD3Colors.ON_SURFACE,
        )
        metrics_box.add_widget(self._downloaded_lbl)

        self._speed_lbl = Label(
            text="0 KB/s",
            size_hint=(None, 1),
            width=dp(80),
            halign="left",
            font_size=sp(11),
            color=MD3Colors.SECONDARY,
        )
        metrics_box.add_widget(self._speed_lbl)

        self._eta_lbl = Label(
            text="ETA: --",
            size_hint=(1, 1),
            halign="right",
            font_size=sp(11),
            color=MD3Colors.ON_SURFACE_VARIANT,
        )
        metrics_box.add_widget(self._eta_lbl)

        self.add_widget(metrics_box)

        # ─────── Control buttons ─────────────────────────────────── #
        btn_box = BoxLayout(size_hint=(1, None), height=dp(36), spacing=MD3Spacing.SM)

        self._pause_btn = MD3Button(
            text="⏸ Pause" if not self.is_paused else "▶ Resume",
            style="outlined",
            size_hint=(None, 1),
            width=dp(100),
        )
        btn_box.add_widget(self._pause_btn)

        self._retry_btn = MD3Button(
            text="🔄 Retry",
            style="text",
            size_hint=(1, 1),
        )
        btn_box.add_widget(self._retry_btn)

        self.add_widget(btn_box)

    def _update_bg(self, *args):
        """Update background rectangle."""
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def _update_progress_fill(self, *args):
        """Update progress bar fill."""
        if self._progress_bar.max > 0:
            pct = self._progress_bar.value / self._progress_bar.max
        else:
            pct = 0
        self._pb_fill.size = (self._progress_bar.width * pct, self._progress_bar.height)
        self._pb_fill.pos = self._progress_bar.pos

    def set_progress(self, downloaded_mb: float, speed_mbps: float = 0, eta_seconds: int = 0):
        """Update progress display."""
        self.downloaded_mb = downloaded_mb
        pct = (downloaded_mb / self.model_size_mb * 100) if self.model_size_mb > 0 else 0
        self._progress_bar.value = min(100, pct)

        self._downloaded_lbl.text = f"{downloaded_mb:.1f} MB / {self.model_size_mb:.0f} MB"
        
        if speed_mbps > 0:
            if speed_mbps < 1:
                self._speed_lbl.text = f"{speed_mbps * 1024:.0f} KB/s"
            else:
                self._speed_lbl.text = f"{speed_mbps:.1f} MB/s"

        if eta_seconds > 0:
            hours = eta_seconds // 3600
            minutes = (eta_seconds % 3600) // 60
            if hours > 0:
                self._eta_lbl.text = f"ETA: {hours}h {minutes}m"
            else:
                self._eta_lbl.text = f"ETA: {minutes}m {eta_seconds % 60}s"

    def complete(self):
        """Mark as completed."""
        self._progress_bar.value = 100
        self._downloaded_lbl.text = f"✅ Complete"
        self._speed_lbl.text = ""
        self._eta_lbl.text = ""
        self._pause_btn.disabled = True
        self._retry_btn.disabled = True


# ─────────────────────────────────────────────────────────────────── #
#  Main Initialization Screen                                         #
# ─────────────────────────────────────────────────────────────────── #

class InitScreen(Screen):
    """Material Design 3 initialization screen with download progress."""

    def __init__(self, on_ready: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(**kwargs)
        self.on_ready = on_ready
        self.stage = InitStage.CHECKING
        self._build_ui()

    def _build_ui(self):
        """Build the initialization UI."""
        root = BoxLayout(orientation="vertical")

        # Background
        with root.canvas.before:
            Color(*MD3Colors.BG_PRIMARY)
            bg_rect = RoundedRectangle()
        root.bind(
            pos=lambda w, _: setattr(bg_rect, "pos", w.pos),
            size=lambda w, _: setattr(bg_rect, "size", w.size),
        )

        # ─────── Header ──────────────────────────────────────────── #
        header = BoxLayout(size_hint=(1, None), height=dp(120), padding=MD3Spacing.MD)
        header_bg_rect = RoundedRectangle()
        with header.canvas.before:
            Color(*MD3Colors.BG_SECONDARY)
            header_bg_rect = RoundedRectangle()
        header.bind(
            pos=lambda w, _: setattr(header_bg_rect, "pos", w.pos),
            size=lambda w, _: setattr(header_bg_rect, "size", w.size),
        )

        header_inner = BoxLayout(orientation="vertical", spacing=MD3Spacing.SM)
        
        title = Label(
            text="[b]O-RAG Initialization[/b]",
            markup=True,
            font_size=sp(28),
            bold=True,
            color=MD3Colors.ON_SURFACE,
            size_hint_y=None,
            height=dp(40),
        )
        header_inner.add_widget(title)

        subtitle = Label(
            text="Downloading AI models for offline use...\nEstimated time: 5-15 minutes (WiFi)",
            font_size=sp(12),
            color=MD3Colors.ON_SURFACE_VARIANT,
            size_hint_y=None,
            height=dp(40),
        )
        header_inner.add_widget(subtitle)

        header.add_widget(header_inner)
        root.add_widget(header)

        # ─────── Status indicator ────────────────────────────────── #
        status_box = BoxLayout(size_hint=(1, None), height=dp(48), padding=MD3Spacing.MD)
        self._status_indicator = Label(
            text="🔄 Checking for existing models...",
            font_size=sp(14),
            color=MD3Colors.SECONDARY,
        )
        status_box.add_widget(self._status_indicator)
        root.add_widget(status_box)

        # ─────── Download cards (scrollable) ──────────────────────── #
        scroll = ScrollView(size_hint=(1, 1))
        cards_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=MD3Spacing.MD,
            padding=MD3Spacing.MD,
        )
        cards_container.bind(minimum_height=cards_container.setter("height"))

        self._qwen_card = StatusCard("Qwen 2.5 Model (LLM)", 800.0)
        cards_container.add_widget(self._qwen_card)

        self._nomic_card = StatusCard("Nomic Embedding Model", 80.0)
        cards_container.add_widget(self._nomic_card)

        # System status card
        self._system_card = self._build_system_status_card()
        cards_container.add_widget(self._system_card)

        scroll.add_widget(cards_container)
        root.add_widget(scroll)

        # ─────── Footer (action buttons) ──────────────────────────── #
        footer = BoxLayout(
            size_hint=(1, None),
            height=dp(64),
            padding=MD3Spacing.MD,
            spacing=MD3Spacing.SM,
        )

        with footer.canvas.before:
            Color(*MD3Colors.BG_SECONDARY)
            footer_bg = RoundedRectangle()
        footer.bind(
            pos=lambda w, _: setattr(footer_bg, "pos", w.pos),
            size=lambda w, _: setattr(footer_bg, "size", w.size),
        )

        self._open_wifi_btn = MD3Button(
            text="📡 Open WiFi Settings",
            style="tonal",
            size_hint=(None, 1),
            width=dp(140),
        )
        self._open_wifi_btn.bind(on_press=self._on_wifi_settings)
        footer.add_widget(self._open_wifi_btn)

        footer.add_widget(Widget(size_hint=(1, 1)))  # Spacer

        self._skip_btn = MD3Button(
            text="⏭ Skip (use later)",
            style="text",
            size_hint=(None, 1),
            width=dp(120),
        )
        self._skip_btn.bind(on_press=self._on_skip)
        footer.add_widget(self._skip_btn)

        root.add_widget(footer)

        # Store card references for updates
        self._cards_container = cards_container
        self.root_widget = root
        self.add_widget(root)

    def _build_system_status_card(self) -> MD3Card:
        """Build system status card showing device health."""
        card = MD3Card()
        card.size_hint_y = None
        card.height = dp(140)
        
        inner = BoxLayout(orientation="vertical", padding=MD3Spacing.MD, spacing=MD3Spacing.SM)

        title = Label(
            text="[b]System Status[/b]",
            markup=True,
            size_hint_y=None,
            height=dp(24),
            font_size=sp(14),
            bold=True,
            color=MD3Colors.ON_SURFACE,
        )
        inner.add_widget(title)

        # Status items
        status_items = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(100), spacing=dp(6))
        
        self._memory_status = Label(
            text="💾 Memory: Checking...",
            size_hint_y=None,
            height=dp(20),
            font_size=sp(12),
            color=MD3Colors.ON_SURFACE_VARIANT,
        )
        status_items.add_widget(self._memory_status)

        self._storage_status = Label(
            text="💿 Storage: Checking...",
            size_hint_y=None,
            height=dp(20),
            font_size=sp(12),
            color=MD3Colors.ON_SURFACE_VARIANT,
        )
        status_items.add_widget(self._storage_status)

        self._network_status = Label(
            text="📡 Network: Checking...",
            size_hint_y=None,
            height=dp(20),
            font_size=sp(12),
            color=MD3Colors.ON_SURFACE_VARIANT,
        )
        status_items.add_widget(self._network_status)

        self._time_estimate = Label(
            text="⏱ Estimated time: Computing...",
            size_hint_y=None,
            height=dp(20),
            font_size=sp(12),
            color=MD3Colors.SECONDARY,
        )
        status_items.add_widget(self._time_estimate)

        inner.add_widget(status_items)
        card.add_widget(inner)
        
        return card

    def update_status(self, message: str, color: str = "secondary"):
        """Update status message."""
        @mainthread
        def _update():
            color_map = {
                "secondary": MD3Colors.SECONDARY,
                "success": MD3Colors.SUCCESS,
                "warning": MD3Colors.WARNING,
                "error": MD3Colors.ERROR,
            }
            self._status_indicator.text = message
            self._status_indicator.color = color_map.get(color, MD3Colors.SECONDARY)

        _update()

    def update_qwen_progress(self, downloaded_mb: float, speed_mbps: float = 0, eta_seconds: int = 0):
        """Update Qwen download progress."""
        @mainthread
        def _update():
            self._qwen_card.set_progress(downloaded_mb, speed_mbps, eta_seconds)
        
        _update()

    def update_nomic_progress(self, downloaded_mb: float, speed_mbps: float = 0, eta_seconds: int = 0):
        """Update Nomic download progress."""
        @mainthread
        def _update():
            self._nomic_card.set_progress(downloaded_mb, speed_mbps, eta_seconds)
        
        _update()

    def complete_initialization(self):
        """Mark initialization as complete and transition to chat."""
        @mainthread
        def _finish():
            self._qwen_card.complete()
            self._nomic_card.complete()
            self.update_status("✅ Ready to chat!", color="success")

            # Fade out and transition after 1 second
            anim = Animation(opacity=0, duration=1.0)
            anim.bind(on_complete=lambda *a: (
                self._transition_to_chat() if self.on_ready else None
            ))
            anim.start(self.root_widget)

        _finish()

    def _transition_to_chat(self):
        """Transition to chat screen."""
        app = self.manager.app if hasattr(self.manager, "app") else None
        if app and self.on_ready:
            self.on_ready()
        elif self.manager:
            self.manager.current = "chat"

    def _on_wifi_settings(self, *args):
        """Open WiFi settings."""
        try:
            from jnius import autoclass
            Intent = autoclass("android.content.Intent")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            
            intent = Intent("android.intent.action.MAIN")
            intent.setClassName("com.android.settings", "com.android.settings.wifi.WifiSettings")
            PythonActivity.mActivity.startActivity(intent)
        except Exception as e:
            print(f"[init] Could not open WiFi settings: {e}")

    def _on_skip(self, *args):
        """Skip initialization and go to chat."""
        self._transition_to_chat()


# ─────────────────────────────────────────────────────────────────── #
#  Download Manager Integration                                       #
# ─────────────────────────────────────────────────────────────────── #

def init_screen_with_downloads(screen: InitScreen, on_complete: Optional[Callable] = None):
    """
    Start model downloads and update InitScreen progress.
    Run this in a background thread.
    """
    try:
        from rag.downloader import DownloadManager
        from rag.pipeline import register_auto_download_callbacks

        # Register callbacks for progress updates
        def on_progress(frac: float, text: str):
            """Called during download."""
            percent = int(frac * 100)
            
            # Estimate time
            elapsed = time.time() - getattr(on_progress, "start_time", time.time())
            if frac > 0:
                total_time = elapsed / frac
                eta = int(total_time - elapsed)
            else:
                eta = 0

            # Determine which model
            if "qwen" in text.lower():
                speed = frac * 800 / (elapsed / 3600) if elapsed > 0 else 0  # MB/s estimate
                screen.update_qwen_progress(frac * 800, speed, eta)
            elif "nomic" in text.lower():
                speed = frac * 80 / (elapsed / 3600) if elapsed > 0 else 0
                screen.update_nomic_progress(frac * 80, speed, eta)

            screen.update_status(text, "secondary")

        on_progress.start_time = time.time()

        def on_done(success: bool, message: str):
            """Called when downloads complete."""
            if success:
                screen.update_status(f"✅ {message}", "success")
                screen.complete_initialization()
                if on_complete:
                    on_complete(True)
            else:
                screen.update_status(f"⚠️ {message}", "warning")
                if on_complete:
                    on_complete(False)

        register_auto_download_callbacks(on_progress, on_done)

    except Exception as e:
        print(f"[init_screen] Download manager error: {e}")
        screen.update_status(f"❌ Error: {e}", "error")
