"""
ui/theme.py — Material Design 3 color palette, typography, and reusable components.

Provides consistent theming across all O-RAG screens with modern Material Design 3.
"""
from __future__ import annotations

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Line, Ellipse
from kivy.metrics import dp, sp
from kivy.animation import Animation
from typing import Tuple


# ─────────────────────────────────────────────────────────────────── #
#  Material Design 3 Color Palette                                    #
# ─────────────────────────────────────────────────────────────────── #

class MD3Colors:
    """Material Design 3 color tokens (Dark theme optimized for mobile)."""

    # Primary brand colors
    PRIMARY = (0.498, 0.318, 0.953, 1)           # #7F51F2 - Vibrant blue
    PRIMARY_VARIANT = (0.345, 0.145, 0.835, 1)   # #5824D5 - Darker blue
    SECONDARY = (0.325, 0.635, 0.976, 1)         # #53A2F8 - Light blue
    TERTIARY = (0.153, 0.776, 0.541, 1)          # #27C64A - Teal/Green

    # Neutral colors (dark theme)
    BG_PRIMARY = (0.102, 0.102, 0.102, 1)        # #1A1A1A - Page background
    BG_SECONDARY = (0.129, 0.129, 0.129, 1)      # #212121 - Card background
    BG_TERTIARY = (0.157, 0.157, 0.157, 1)       # #282828 - Slightly elevated

    SURFACE = (0.118, 0.118, 0.118, 1)           # #1E1E1E - Surface
    SURFACE_VARIANT = (0.145, 0.145, 0.153, 1)   # #252527 - Subdued surface

    # Text colors
    ON_PRIMARY = (1.0, 1.0, 1.0, 1)              # White text on primary
    ON_SECONDARY = (0.0, 0.0, 0.0, 1)            # Black text on secondary
    ON_SURFACE = (0.922, 0.922, 0.922, 1)        # #EBEBEB - Primary text
    ON_SURFACE_VARIANT = (0.647, 0.647, 0.659, 1) # #A5A5A8 - Secondary text

    # Semantic colors
    SUCCESS = (0.180, 0.745, 0.349, 1)           # #2EBE59 - Green
    WARNING = (0.937, 0.604, 0.145, 1)           # #EF9A25 - Orange
    ERROR = (0.937, 0.220, 0.220, 1)             # #EF3838 - Red
    INFO = (0.318, 0.592, 0.922, 1)              # #5196EB - Light blue

    # Outline & divider
    OUTLINE = (0.322, 0.322, 0.333, 1)           # #525255 - Subtle outline
    OUTLINE_VARIANT = (0.247, 0.247, 0.255, 1)   # #3F3F41 - Strong outline
    DIVIDER = (0.204, 0.204, 0.204, 1)           # #343434 - Light divider

    # Elevation shadows (for dp6, dp12, dp20 elevation)
    SHADOW_LIGHT = (0, 0, 0, 0.12)               # Very subtle
    SHADOW_MED = (0, 0, 0, 0.24)                 # Standard
    SHADOW_DARK = (0, 0, 0, 0.38)                # Deep


# ─────────────────────────────────────────────────────────────────── #
#  Typography Scale (Material Design 3)                               #
# ─────────────────────────────────────────────────────────────────── #

class MD3Typography:
    """Material Design 3 typography scale."""

    # Display styles (largest, for app name, hero text)
    DISPLAY_LARGE = {"size_sp": 57, "bold": True}
    DISPLAY_MEDIUM = {"size_sp": 45, "bold": True}
    DISPLAY_SMALL = {"size_sp": 36, "bold": False}

    # Headline styles (section headings)
    HEADLINE_LARGE = {"size_sp": 32, "bold": True}
    HEADLINE_MEDIUM = {"size_sp": 28, "bold": True}
    HEADLINE_SMALL = {"size_sp": 24, "bold": True}

    # Title styles (smaller headings)
    TITLE_LARGE = {"size_sp": 22, "bold": True}
    TITLE_MEDIUM = {"size_sp": 16, "bold": True}
    TITLE_SMALL = {"size_sp": 14, "bold": True}

    # Body styles (main content)
    BODY_LARGE = {"size_sp": 16, "bold": False}
    BODY_MEDIUM = {"size_sp": 14, "bold": False}
    BODY_SMALL = {"size_sp": 12, "bold": False}

    # Label styles (badges, tabs, buttons)
    LABEL_LARGE = {"size_sp": 14, "bold": True}
    LABEL_MEDIUM = {"size_sp": 12, "bold": True}
    LABEL_SMALL = {"size_sp": 11, "bold": True}


# ─────────────────────────────────────────────────────────────────── #
#  Spacing & Sizing Constants                                         #
# ─────────────────────────────────────────────────────────────────── #

class MD3Spacing:
    """MD3 spacing scale."""
    XS = dp(4)      # Extra small
    SM = dp(8)      # Small
    MD = dp(12)     # Medium (default padding)
    LG = dp(16)     # Large
    XL = dp(24)     # Extra large
    XXL = dp(32)    # Extra extra large


class MD3Radius:
    """MD3 corner radius scale."""
    NONE = 0
    SM = dp(4)      # Small components
    MD = dp(8)      # Medium components (buttons, cards)
    LG = dp(12)     # Large components
    XL = dp(16)     # Extra large (elevated cards)
    FULL = dp(50)   # Fully rounded (chips, FAB)


# ─────────────────────────────────────────────────────────────────── #
#  Reusable Components                                                #
# ─────────────────────────────────────────────────────────────────── #

def paint_widget(widget: Widget, color: Tuple[float, float, float, float], 
                 radius: float = 0, outline: Tuple[float, float, float, float] = None) -> None:
    """Paint a solid background on a widget's canvas.before."""
    with widget.canvas.before:
        Color(*color)
        r = RoundedRectangle(radius=[dp(radius)])
        
        if outline:
            Color(*outline)
            Line(rounded_rectangle=(r.x, r.y, r.width, r.height, dp(radius)), width=dp(1))

    widget.bind(
        pos=lambda w, _: setattr(r, "pos", w.pos),
        size=lambda w, _: setattr(r, "size", w.size),
    )


class MD3Button(Button):
    """Material Design 3 button with elevation and ripple effect."""

    def __init__(self, text: str, style: str = "filled", on_press_cb=None, **kwargs):
        """
        Args:
            text: Button label
            style: "filled", "tonal", "outlined", "text"
            on_press_cb: Callback function
        """
        super().__init__(text=text, **kwargs)
        self.style = style
        self.size_hint_y = kwargs.get("size_hint_y", None)
        self.height = kwargs.get("height", dp(40))

        # Style button
        self._apply_style()

        if on_press_cb:
            self.bind(on_press=lambda: on_press_cb())

    def _apply_style(self):
        """Apply MD3 styling based on button type."""
        self.background_normal = ""
        self.background_down = ""
        self.font_size = sp(14)
        self.bold = True

        if self.style == "filled":
            self.background_color = MD3Colors.PRIMARY
            self.color = MD3Colors.ON_PRIMARY
        elif self.style == "tonal":
            # Tonal: colored background, less prominent
            self.background_color = MD3Colors.SECONDARY
            self.color = MD3Colors.ON_PRIMARY
        elif self.style == "outlined":
            # Outlined: transparent with border
            self.background_color = MD3Colors.BG_SECONDARY
            self.color = MD3Colors.PRIMARY
        else:  # text
            self.background_color = (0, 0, 0, 0)  # Transparent
            self.color = MD3Colors.PRIMARY

    def on_state(self, widget, value):
        """Handle pressed state with color change."""
        if value == "down":
            # Pressed state: darken
            if self.style == "filled":
                self.background_color = MD3Colors.PRIMARY_VARIANT
        else:
            self._apply_style()


class MD3Card(BoxLayout):
    """Material Design 3 card with elevation shadow."""

    def __init__(self, elevation: int = 1, **kwargs):
        """
        Args:
            elevation: Shadow depth (1, 3, 6, 12)
        """
        super().__init__(**kwargs)
        self.elevation = elevation
        self._apply_elevation()

    def _apply_elevation(self):
        """Apply shadow based on elevation level."""
        paint_widget(self, MD3Colors.BG_SECONDARY, radius=12)

        # Could add shadow via canvas.before, but Kivy doesn't support native shadows well
        # For now, use background color to suggest elevation


class MD3ProgressBar(ProgressBar):
    """Material Design 3 progress bar with smooth animation."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""

        # Paint bar background (track)
        paint_widget(self, MD3Colors.SURFACE_VARIANT, radius=4)

        # Paint progress fill
        with self.canvas:
            Color(*MD3Colors.PRIMARY)
            self._progress_rect = RoundedRectangle(radius=[dp(4)])

    def on_value(self, instance, value):
        """Update progress fill width."""
        if hasattr(self, "_progress_rect"):
            percentage = value / self.max if self.max > 0 else 0
            self._progress_rect.size = (self.width * percentage, self.height)
            self._progress_rect.pos = self.pos


class MD3Chip(Button):
    """Material Design 3 chip (small, rounded button)."""

    def __init__(self, label: str, **kwargs):
        super().__init__(text=label, size_hint=(None, None), size=(dp(100), dp(32)), **kwargs)
        self.background_normal = ""
        self.background_color = MD3Colors.SURFACE_VARIANT
        self.color = MD3Colors.ON_SURFACE
        self.font_size = sp(12)
        self.bold = True

        with self.canvas.before:
            Color(*MD3Colors.SURFACE_VARIANT)
            self._bg = RoundedRectangle(radius=[self.height / 2])

        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size


class MD3Badge(Widget):
    """Material Design 3 notification badge (small red circle with number)."""

    def __init__(self, count: int = 1, **kwargs):
        super().__init__(size_hint=(None, None), size=(dp(24), dp(24)), **kwargs)
        self.count = count

        with self.canvas:
            Color(*MD3Colors.ERROR)
            self._circle = Ellipse(size=self.size, pos=self.pos)

        self._label = Label(
            text=str(count),
            font_size=sp(10),
            bold=True,
            color=MD3Colors.ON_PRIMARY,
            center=self.center,
        )
        self.add_widget(self._label)

        self.bind(pos=self._update_circle, size=self._update_circle)

    def _update_circle(self, *args):
        self._circle.pos = self.pos
        self._circle.size = self.size
        self._label.center = self.center


class MD3Dialog(BoxLayout):
    """Material Design 3 dialog base (for confirmation/input dialogs)."""

    def __init__(self, title: str, message: str, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.title_text = title
        self.message_text = message

        # Title
        title_lbl = Label(
            text=f"[b]{title}[/b]",
            markup=True,
            size_hint_y=None,
            height=dp(56),
            font_size=sp(20),
            bold=True,
            color=MD3Colors.ON_SURFACE,
        )
        self.add_widget(title_lbl)

        # Message
        msg_lbl = Label(
            text=message,
            size_hint_y=None,
            height=dp(100),
            font_size=sp(14),
            color=MD3Colors.ON_SURFACE_VARIANT,
            text_size=(self.width - dp(32), None),
            halign="left",
            valign="top",
        )
        self.add_widget(msg_lbl)


# ─────────────────────────────────────────────────────────────────── #
#  Animation Helpers                                                   #
# ─────────────────────────────────────────────────────────────────── #

def create_fade_animation(duration: float = 0.3, start_val: float = 0.0, 
                         end_val: float = 1.0) -> Animation:
    """Create smooth fade-in/out animation."""
    return Animation(opacity=end_val, duration=duration)


def create_slide_animation(target_x: float, duration: float = 0.3) -> Animation:
    """Create slide animation."""
    return Animation(x=target_x, duration=duration)


def create_scale_animation(scale: float = 1.1, duration: float = 0.2) -> Animation:
    """Create scale (zoom) animation."""
    return Animation(scale=scale, duration=duration)


# ─────────────────────────────────────────────────────────────────── #
#  Theme Application Utility                                          #
# ─────────────────────────────────────────────────────────────────── #

class MD3Theme:
    """Centralized theme manager."""

    colors = MD3Colors
    typography = MD3Typography
    spacing = MD3Spacing
    radius = MD3Radius

    @staticmethod
    def apply_background(widget: Widget, bg_type: str = "primary"):
        """Apply background color to widget."""
        bg_color = getattr(MD3Colors, f"BG_{bg_type.upper()}", MD3Colors.BG_PRIMARY)
        paint_widget(widget, bg_color)

    @staticmethod
    def apply_card_style(widget: Widget, elevation: int = 1):
        """Apply card styling."""
        paint_widget(widget, MD3Colors.BG_SECONDARY, radius=12)
