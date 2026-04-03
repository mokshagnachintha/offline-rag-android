"""
main.py — Offline RAG App entry point (Kivy / Android).

Single-screen design: one chat interface.
  • Tap + to attach a PDF or TXT document (RAG mode activates automatically)
  • Otherwise chat freely with the AI
  • Model is bundled in the APK — extracted to device storage on first launch
"""

# ── Kivy config BEFORE any other kivy import ──────────────────────── #
import os
os.environ.setdefault("KIVY_LOG_LEVEL", "warning")

from kivy.config import Config
Config.set("kivy", "window_icon", "assets/app_icon.png")
# ─────────────────────────────────────────────────────────────────── #

# Keep input bar visible above the soft keyboard on Android
from kivy.core.window import Window
Window.softinput_mode = "below_target"

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock

import sys
import traceback
sys.path.insert(0, os.path.dirname(__file__))

from ui.screens.chat_screen import ChatScreen
from ui.screens.init_screen import InitScreen, init_screen_with_downloads
from ui.screens.analytics_dashboard import AnalyticsDashboardScreen
from rag.pipeline           import init
from rag.downloader import is_downloaded, QWEN_MODEL, NOMIC_MODEL

# Analytics setup
try:
    from analytics import start_continuous_monitoring
except ImportError:
    def start_continuous_monitoring(*args, **kwargs):
        pass  # Graceful fallback

# Memory optimization setup
try:
    from rag.memory_manager import start_memory_optimization
except ImportError:
    def start_memory_optimization(*args, **kwargs):
        pass  # Graceful fallback


def _global_exception_handler(exc_type, exc_value, exc_tb):
    """Log unhandled exceptions instead of silently crashing."""
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(f"[CRASH] Unhandled exception:\n{msg}")
    
    # Write to Android log file if possible
    priv = os.environ.get("ANDROID_PRIVATE", "")
    if priv:
        try:
            with open(os.path.join(priv, "crash.log"), "a") as f:
                f.write(msg + "\n")
        except Exception:
            pass

sys.excepthook = _global_exception_handler


def _start_android_service():
    """Start the foreground service that owns llama-server processes.
    No-op on desktop (ImportError is silently ignored).
    """
    try:
        from android import AndroidService  # type: ignore
        svc = AndroidService("O-RAG AI Engine", "AI engine running in background")
        svc.start("start")
        print("[main] Android foreground service started.")
    except ImportError:
        print("[main] Android service not available (desktop mode)")
    except Exception as exc:
        print(f"[main] Service start failed: {exc}")
        import traceback
        traceback.print_exc()


def _models_ready() -> bool:
    """Check if both models are downloaded and ready."""
    qwen_ok = is_downloaded(QWEN_MODEL["filename"])
    nomic_ok = is_downloaded(NOMIC_MODEL["filename"])
    return qwen_ok and nomic_ok


class RAGApp(App):
    title = "O-RAG"

    def build(self):
        try:
            # Start analytics monitoring
            start_continuous_monitoring(interval_seconds=5.0)

            # Start memory optimization for 4GB devices
            start_memory_optimization()

            root = BoxLayout(orientation="vertical")
            with root.canvas.before:
                Color(0.102, 0.102, 0.102, 1)   # #1a1a1a
                bg = Rectangle()
            root.bind(
                pos =lambda w, _: setattr(bg, "pos",  w.pos),
                size=lambda w, _: setattr(bg, "size", w.size),
            )

            sm = ScreenManager(transition=FadeTransition(duration=0.12))

            # Add init screen (shown first if models not ready)
            init_screen = InitScreen(name="init", on_ready=lambda: self._on_init_complete(sm))
            sm.add_widget(init_screen)

            # Add chat screen
            sm.add_widget(ChatScreen(name="chat"))

            # Add analytics dashboard screen
            sm.add_widget(AnalyticsDashboardScreen(name="analytics"))

            root.add_widget(sm)

            # Start foreground service first
            _start_android_service()

            # Route to appropriate screen based on model availability
            Clock.schedule_once(lambda *_: self._route_initial_screen(sm, init_screen), 0.5)

            return root
        except Exception as exc:
            print(f"[CRASH] App build failed: {exc}")
            import traceback
            traceback.print_exc()
            raise

    def _route_initial_screen(self, sm: ScreenManager, init_screen: InitScreen):
        """Route to init screen or chat based on model availability."""
        try:
            if _models_ready():
                # Models ready → go to chat
                print("[main] Models ready, starting chat...")
                init(on_done=lambda ok, msg: sm.switch_to(sm.get_screen("chat")))
            else:
                # Models not ready → show init screen and start downloads
                print("[main] Models not ready, showing initialization screen...")
                sm.current = "init"
                
                # Start downloads in background thread
                import threading
                def _start_downloads():
                    try:
                        init_screen_with_downloads(
                            init_screen,
                            on_complete=lambda success: (
                                self._on_download_complete(sm, success)
                            ),
                        )
                    except Exception as e:
                        print(f"[main] Download thread error: {e}")
                        import traceback
                        traceback.print_exc()
                
                threading.Thread(target=_start_downloads, daemon=True).start()
        except Exception as exc:
            print(f"[main] Route to initial screen failed: {exc}")
            import traceback
            traceback.print_exc()

    def _on_download_complete(self, sm: ScreenManager, success: bool):
        """Called when model downloads complete."""
        try:
            if success:
                print("[main] Downloads complete, initializing pipeline...")
                init(on_done=lambda ok, msg: sm.switch_to(sm.get_screen("chat")))
            else:
                print("[main] Download failed, allowing user to retry/skip")
                # User can manually tap "Skip" button or retry
        except Exception as exc:
            print(f"[main] Download complete handler failed: {exc}")
            import traceback
            traceback.print_exc()

    def _on_init_complete(self, sm: ScreenManager):
        """Called when init screen signals initialization complete."""
        sm.current = "chat"


if __name__ == "__main__":
    RAGApp().run()

