"""
main.py — Offline RAG App entry point (Kivy / Android).

Single-screen design: one chat interface.
  • Tap + to attach a PDF or TXT document (RAG mode activates automatically)
  • Otherwise chat freely with the AI
  • Model is bundled in the APK — extracted to device storage on first launch
"""
import os
import sys

# Write startup marker to crash log for diagnostics
_startup_log = os.path.expanduser("~/.orag.startup.log")

# Try to also write to external storage if available
_ext_log = None
try:
    import pathlib
    # Try common Android external paths
    for path in ["/sdcard/O-RAG", "/storage/emulated/0/O-RAG", "/data/media/O-RAG"]:
        try:
            pathlib.Path(path).mkdir(parents=True, exist_ok=True)
            _ext_log = os.path.join(path, "startup.log")
            break
        except:
            pass
except:
    pass

def _write_diagnostic(msg: str):
    """Write diagnostic message to log files."""
    try:
        with open(_startup_log, "a") as f:
            f.write(msg + "\n")
    except:
        pass
    
    if _ext_log:
        try:
            with open(_ext_log, "a") as f:
                f.write(msg + "\n")
        except:
            pass

# Log startup
import datetime
_write_diagnostic(f"\n=== APP STARTUP {datetime.datetime.now()} ===")
_write_diagnostic(f"External log: {_ext_log}")

# ── Kivy config BEFORE any other kivy import ──────────────────────── #
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

# Log each import for diagnostics
_import_log = lambda msg: print(f"[IMPORT] {msg}")
_import_error = None
_import_traceback_str = ""

try:
    _import_log("Loading UI screens...")
    from ui.screens.chat_screen import ChatScreen
    from ui.screens.init_screen import InitScreen, init_screen_with_downloads
    from ui.screens.analytics_dashboard import AnalyticsDashboardScreen
    
    _import_log("Loading RAG pipeline...")
    from rag.pipeline import init
    _import_log("Loading downloader...")
    from rag.downloader import is_downloaded, QWEN_MODEL, NOMIC_MODEL
    _import_log("Core imports successful")
except Exception as e:
    _import_log(f"IMPORT ERROR: {type(e).__name__}: {e}")
    _write_diagnostic(f"IMPORT ERROR: {type(e).__name__}: {e}")
    _import_error = e
    _import_traceback_str = traceback.format_exc()
    print(_import_traceback_str)
    _write_diagnostic(_import_traceback_str)
    
    # Minimal fallback imports
    ChatScreen = None
    InitScreen = None
    init_screen_with_downloads = None
    AnalyticsDashboardScreen = None
    init = None
    is_downloaded = None
    QWEN_MODEL = None
    NOMIC_MODEL = None

# Analytics setup
try:
    _import_log("Loading analytics...")
    from analytics import start_continuous_monitoring
except ImportError as e:
    _import_log(f"Analytics not available: {e}")
    def start_continuous_monitoring(*args, **kwargs):
        pass  # Graceful fallback
except Exception as e:
    _import_log(f"Analytics load failed: {e}")
    def start_continuous_monitoring(*args, **kwargs):
        pass

# Memory optimization setup
try:
    _import_log("Loading memory manager...")
    from rag.memory_manager import start_memory_optimization
except ImportError as e:
    _import_log(f"Memory manager not available: {e}")
    def start_memory_optimization(*args, **kwargs):
        pass  # Graceful fallback
except Exception as e:
    _import_log(f"Memory manager load failed: {e}")
    def start_memory_optimization(*args, **kwargs):
        pass


def _global_exception_handler(exc_type, exc_value, exc_tb):
    """Log unhandled exceptions instead of silently crashing."""
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(f"[CRASH] Unhandled exception:\n{msg}")
    _write_diagnostic(f"[CRASH] Unhandled exception:\n{msg}")
    
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
    if is_downloaded is None or QWEN_MODEL is None or NOMIC_MODEL is None:
        print("[main] Model checker not available")
        return False
    try:
        qwen_ok = is_downloaded(QWEN_MODEL["filename"])
        nomic_ok = is_downloaded(NOMIC_MODEL["filename"])
        return qwen_ok and nomic_ok
    except Exception as e:
        print(f"[main] Error checking models: {e}")
        return False


class ErrorScreen:
    """Ultra-minimal error display - just text."""
    @staticmethod
    def create(error_msg: str):
        try:
            from kivy.uix.boxlayout import BoxLayout
            from kivy.uix.label import Label
            
            root = BoxLayout(orientation="vertical")
            
            # Just add the error text directly
            label = Label(
                text=error_msg,
                font_size="20sp"
            )
            root.add_widget(label)
            
            return root
        except:
            # Extreme fallback
            return BoxLayout()


class RAGApp(App):
    title = "O-RAG"

    def build(self):
        try:
            # Log build start
            _write_diagnostic(f"=== BUILD START ===")
            
            # If there was an import error, show error screen
            if _import_error:
                _write_diagnostic(f"Showing error screen: {_import_error}")
                try:
                    error_text = (
                        f"ERROR LOADING APP\n\n"
                        f"Type: {type(_import_error).__name__}\n"
                        f"Message: {str(_import_error)[:300]}\n\n"
                        f"This is a startup error. Logs saved to:\n"
                        f"/sdcard/O-RAG/startup.log\n\n"
                        f"Please restart the app."
                    )
                    error_screen = ErrorScreen.create(error_text)
                    return error_screen
                except Exception as e:
                    _write_diagnostic(f"Error screen creation failed: {e}")
                    return BoxLayout()
            
            _write_diagnostic("Core imports OK, building normal UI")
            # Otherwise, proceed with normal startup
            return self._build_normal()
        except Exception as exc:
            _write_diagnostic(f"Build failed: {type(exc).__name__}: {exc}")
            print(f"[CRASH] App build failed: {exc}")
            import traceback as tb
            tb.print_exc()
            # Return minimal widget to prevent complete crash
            try:
                error_text = f"ERROR: {type(exc).__name__}\n{str(exc)[:200]}\n\nRestart the app"
                return ErrorScreen.create(error_text)
            except:
                return BoxLayout()
    
    def _build_normal(self):
        try:
            # Check if core modules loaded successfully
            if ChatScreen is None or InitScreen is None:
                raise RuntimeError("Core screen modules failed to import")
            
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

            # Add analytics dashboard screen if available
            if AnalyticsDashboardScreen:
                sm.add_widget(AnalyticsDashboardScreen(name="analytics"))

            root.add_widget(sm)

            # Start foreground service first
            _start_android_service()

            # Route to appropriate screen based on model availability
            Clock.schedule_once(lambda *_: self._route_initial_screen(sm, init_screen), 0.5)

            return root
        except Exception as exc:
            _write_diagnostic(f"Normal build failed: {type(exc).__name__}: {exc}")
            print(f"[CRASH] Normal build failed: {exc}")
            import traceback
            tb_str = traceback.format_exc()
            traceback.print_exc()
            _write_diagnostic(tb_str)
            
            # Return error screen instead of crashing
            try:
                error_text = (
                    f"BUILD ERROR\n\n"
                    f"Type: {type(exc).__name__}\n"
                    f"Message: {str(exc)[:250]}\n\n"
                    f"Logs saved to: /sdcard/O-RAG/startup.log\n"
                    f"Restart the app."
                )
                return ErrorScreen.create(error_text)
            except:
                return BoxLayout()

    def _route_initial_screen(self, sm: ScreenManager, init_screen: InitScreen):
        """Route to init screen or chat based on model availability."""
        try:
            if _models_ready():
                # Models ready → go to chat
                print("[main] Models ready, starting chat...")
                if init:
                    init(on_done=lambda ok, msg: sm.switch_to(sm.get_screen("chat")))
                else:
                    sm.switch_to(sm.get_screen("chat"))
            else:
                # Models not ready → show init screen and start downloads
                print("[main] Models not ready, showing initialization screen...")
                sm.current = "init"
                
                # Start downloads in background thread
                import threading
                def _start_downloads():
                    try:
                        if init_screen_with_downloads:
                            init_screen_with_downloads(
                                init_screen,
                                on_complete=lambda success: (
                                    self._on_download_complete(sm, success)
                                ),
                            )
                        else:
                            print("[main] Download function not available, skipping downloads")
                    except Exception as e:
                        print(f"[main] Download thread error: {e}")
                        import traceback
                        traceback.print_exc()
                
                threading.Thread(target=_start_downloads, daemon=True).start()
        except Exception as exc:
            print(f"[main] Route to initial screen failed: {exc}")
            import traceback
            traceback.print_exc()
            # Show init screen even if routing fails
            sm.current = "init"

    def _on_download_complete(self, sm: ScreenManager, success: bool):
        """Called when model downloads complete."""
        try:
            if success:
                print("[main] Downloads complete, initializing pipeline...")
                if init:
                    init(on_done=lambda ok, msg: sm.switch_to(sm.get_screen("chat")))
                else:
                    sm.switch_to(sm.get_screen("chat"))
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

