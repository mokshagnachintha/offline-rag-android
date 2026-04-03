"""
downloader.py — Download GGUF models from Hugging Face Hub.


"""
from __future__ import annotations

import os
import shutil
import threading
from pathlib import Path
from typing import Callable, Optional

from . import model_config


# ------------------------------------------------------------------ #
#  Catalogue of available Mobile RAG GGUF models                     #
# ------------------------------------------------------------------ #

# The primary Generation model
QWEN_MODEL: dict = {
    "label":    "Qwen 3.5-2B Instruct Q4_K_M (~1.3 GB)",
    "repo_id":  "bartowski/Qwen_Qwen3.5-2B-GGUF",
    "filename": "Qwen_Qwen3.5-2B-Q4_K_M.gguf",
    "size_mb":  1330,
}

# The primary Embedding model
NOMIC_MODEL: dict = {
    "label":    "Nomic Embed Text v1.5 Q4_K_M (~80 MB)",
    "repo_id":  "nomic-ai/nomic-embed-text-v1.5-GGUF",
    "filename": "nomic-embed-text-v1.5.Q4_K_M.gguf",
    "size_mb":  80,
}

MOBILE_MODELS: list[dict] = [QWEN_MODEL, NOMIC_MODEL]


# ------------------------------------------------------------------ #
#  Destination directory (same as llm.py models dir)                  #
# ------------------------------------------------------------------ #

# App root: rag/downloader.py → ../..
_APP_ROOT_DL = Path(__file__).resolve().parent.parent


def _models_dir() -> str:
    base = os.environ.get("ANDROID_PRIVATE", os.path.expanduser("~"))
    d = os.path.join(base, "models")
    os.makedirs(d, exist_ok=True)
    return d


def model_dest_path(filename: str) -> str:
    return os.path.join(_models_dir(), filename)


def is_downloaded(filename: str) -> bool:
    return os.path.isfile(model_dest_path(filename)) or _bundled_model_path(filename) is not None


def _bundled_model_path(filename: str) -> Optional[str]:
    """
    Return the path to the GGUF if it was bundled inside the APK or
    sits in the project root (desktop).  Returns None if not found.

    On Android, python-for-android extracts all app files to the
    directory pointed to by ANDROID_APP_PATH (p4a >= 2023.09) or to
    $ANDROID_PRIVATE/app/ on older builds.
    """
    candidates = [
        # Desktop / development: model sitting next to main.py
        str(_APP_ROOT_DL / filename),
        # Android: p4a extracts app files to ANDROID_APP_PATH
        os.path.join(os.environ.get("ANDROID_APP_PATH", ""), filename),
        # Android alternative layout (older p4a)
        os.path.join(os.environ.get("ANDROID_PRIVATE", ""), "app", filename),
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None


# ------------------------------------------------------------------ #
#  Download logic                                                      #
# ------------------------------------------------------------------ #

def _get_hf_hub():
    try:
        from huggingface_hub import hf_hub_download
        return hf_hub_download
    except ImportError:
        raise RuntimeError(
            "huggingface_hub is not installed.\n"
            "Install it with: pip install huggingface-hub"
        )


def _expected_bytes(repo_id: str, filename: str, max_retries: int = 3) -> int:
    """Return the file size in bytes from the HF Hub metadata (no download). Retries on failure."""
    from time import sleep
    
    for attempt in range(max_retries):
        try:
            from huggingface_hub import get_hf_file_metadata, hf_hub_url
            url  = hf_hub_url(repo_id=repo_id, filename=filename)
            meta = get_hf_file_metadata(url, timeout=30)
            return meta.size or 0
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"[downloader] Metadata fetch failed (attempt {attempt+1}/{max_retries}): {e}. Retrying in {wait_time}s...")
                sleep(wait_time)
            else:
                print(f"[downloader] Failed to fetch metadata after {max_retries} attempts.")
    return 0


def download_model(
    repo_id:     str,
    filename:    str,
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_done:     Optional[Callable[[bool, str], None]]  = None,
    max_retries: int = 3,
) -> None:
    """
    Download a GGUF file from Hugging Face to the local models/ folder.
    Runs in a background thread with automatic retry on failure.

    Progress is reported by polling the partial file size every 0.5 s,
    so it works with any version of huggingface_hub.

    on_progress(fraction 0-1, status_text) — called ~2×/sec during download
    on_done(success, dest_path_or_error)   — called on completion
    max_retries: number of retry attempts for network failures
    """
    def _run():
        dest = model_dest_path(filename)
        from time import sleep

        if os.path.isfile(dest) and os.path.getsize(dest) > 10 * 1024 * 1024:
            if on_progress:
                on_progress(1.0, "Already downloaded.")
            if on_done:
                on_done(True, dest)
            return

        hf_hub_download = _get_hf_hub()

        for attempt in range(max_retries):
            if on_progress:
                msg = "Connecting to Hugging Face..." if attempt == 0 else f"Retrying... (attempt {attempt+1}/{max_retries})"
                on_progress(0.0, msg)

            # Fetch expected file size before download starts
            total_bytes = _expected_bytes(repo_id, filename, max_retries=2)

            # --- progress poller (runs in its own thread) ---
            _stop_poll = threading.Event()

            def _poller():
                # huggingface_hub writes to a .incomplete temp file first
                inc_path = dest + ".incomplete"
                while not _stop_poll.wait(0.5):
                    check = inc_path if os.path.isfile(inc_path) else dest
                    if os.path.isfile(check):
                        done = os.path.getsize(check)
                        if total_bytes:
                            frac = min(done / total_bytes, 0.99)
                            mb_d = done        / 1_048_576
                            mb_t = total_bytes / 1_048_576
                            if on_progress:
                                on_progress(frac, f"{mb_d:.0f} / {mb_t:.0f} MB")
                        else:
                            mb_d = done / 1_048_576
                            if on_progress:
                                on_progress(0.0, f"{mb_d:.0f} MB downloaded...")

            poll_thread = threading.Thread(target=_poller, daemon=True)
            poll_thread.start()

            try:
                # Build kwargs carefully — older HF versions don't have some args
                kwargs: dict = {
                    "repo_id":  repo_id,
                    "filename": filename,
                    "local_dir": _models_dir(),
                    "timeout": 300,  # 5 minute timeout (important for slow networks)
                }
                # local_dir_use_symlinks added in ~0.17; silently skip if absent
                try:
                    import inspect
                    from huggingface_hub import hf_hub_download as _hfd
                    if "local_dir_use_symlinks" in inspect.signature(_hfd).parameters:
                        kwargs["local_dir_use_symlinks"] = False
                except Exception:
                    pass

                cached = hf_hub_download(**kwargs)

                _stop_poll.set()
                poll_thread.join(timeout=1)

                if os.path.abspath(cached) != os.path.abspath(dest):
                    shutil.copy2(cached, dest)

                if on_progress:
                    on_progress(1.0, "Download complete ✓")
                if on_done:
                    on_done(True, dest)
                return  # Success, don't retry

            except Exception as e:
                _stop_poll.set()
                poll_thread.join(timeout=1)
                error_msg = str(e)
                
                # Clean up failed partial download
                for incomplete in [dest + ".incomplete", dest]:
                    if os.path.isfile(incomplete):
                        try:
                            os.remove(incomplete)
                        except Exception:
                            pass

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    if on_progress:
                        on_progress(0.0, f"Error: {error_msg[:50]}... Retrying in {wait_time}s...")
                    sleep(wait_time)
                else:
                    # Final attempt failed
                    if on_done:
                        on_done(False, f"Download failed after {max_retries} attempts: {error_msg}")
                    return

    threading.Thread(target=_run, daemon=True).start()


def _extract_model_from_apk(
    asset_name:  str,
    dest_path:   str,
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_done:     Optional[Callable[[bool, str], None]]  = None,
) -> None:
    """
    Internal helper: extract any APK asset entry to an arbitrary dest_path.
    Runs in a background thread.
    """
    def _run():
        try:
            from android import mActivity  # type: ignore
        except ImportError:
            if on_done:
                on_done(False, "Not on Android — skipping asset extraction.")
            return

        try:
            import zipfile as _zf

            apk_path = str(mActivity.getPackageCodePath())
            entry  = f"assets/{asset_name}"
            label  = os.path.basename(asset_name)

            with _zf.ZipFile(apk_path, "r") as zf:
                info  = zf.getinfo(entry)
                total = info.file_size
                print(f"[downloader] Extracting {entry}  ({total//1_048_576} MB) → {dest_path}")

                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                copied = 0
                if on_progress:
                    on_progress(0.0, f"Extracting {label}…")

                with zf.open(info) as zin, open(dest_path, "wb") as f:
                    while True:
                        chunk = zin.read(512 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
                        copied += len(chunk)
                        if on_progress and total > 0:
                            frac = min(copied / total, 0.99)
                            mb_d = copied // 1_048_576
                            mb_t = total  // 1_048_576
                            on_progress(frac, f"Extracting {label}… {mb_d} / {mb_t} MB")

            if on_progress:
                on_progress(1.0, f"Extracted {label}.")
            if on_done:
                on_done(True, dest_path)

        except Exception as e:
            if on_done:
                on_done(False, str(e))

    threading.Thread(target=_run, daemon=True).start()


def extract_from_apk_asset(
    asset_name:  str = "models/model.gguf",
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_done:     Optional[Callable[[bool, str], None]]  = None,
) -> None:
    """Backward-compatible wrapper: extracts Qwen model from APK assets."""
    _extract_model_from_apk(
        asset_name  = asset_name,
        dest_path   = model_dest_path(QWEN_MODEL["filename"]),
        on_progress = on_progress,
        on_done     = on_done,
    )



def auto_download_default(
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_done:     Optional[Callable[[bool, str], None]]  = None,
) -> None:
    """
    Ensure both the Qwen (Generation) and Nomic (Embedding) models are ready.
    Logic priority:
      1. Already present in models/ dir
      2. Bundled inside the APK (Android) -> Extract Qwen
      3. Bundled in project dev folder
      4. Download from HuggingFace
    """
    qwen_dest  = model_dest_path(QWEN_MODEL["filename"])
    nomic_dest = model_dest_path(NOMIC_MODEL["filename"])

    def _prepare_nomic():
        # Step 2: Ensure Nomic embedding model is present
        if os.path.isfile(nomic_dest) and os.path.getsize(nomic_dest) > 10 * 1024 * 1024:
            if on_progress: on_progress(1.0, "All models ready.")
            if on_done: on_done(True, "All models ready.")
            return

        # On Android, try extracting from APK first
        if os.environ.get("ANDROID_PRIVATE"):
            def _after_nomic_extract(ok, path_or_err):
                if ok:
                    if on_progress: on_progress(1.0, "All models ready.")
                    if on_done: on_done(True, "All models ready.")
                else:
                    # Fallback: download from HuggingFace
                    download_model(
                        repo_id     = NOMIC_MODEL["repo_id"],
                        filename    = NOMIC_MODEL["filename"],
                        on_progress = on_progress,
                        on_done     = on_done,
                    )
            _extract_model_from_apk(
                asset_name   = "models/nomic.gguf",
                dest_path    = nomic_dest,
                on_progress  = on_progress,
                on_done      = _after_nomic_extract,
            )
            return

        # Desktop / no APK: download directly from HF
        download_model(
            repo_id     = NOMIC_MODEL["repo_id"],
            filename    = NOMIC_MODEL["filename"],
            on_progress = on_progress,
            on_done     = on_done
        )

    def _prepare_qwen():
        # Step 1: Ensure Qwen generation model is present
        
        # 1. Already on disk
        if os.path.isfile(qwen_dest) and os.path.getsize(qwen_dest) > 50 * 1024 * 1024:
            _prepare_nomic()
            return

        # 2. Extract from APK asset (Android only)
        if os.environ.get("ANDROID_PRIVATE"):
            def _after_extract(ok, path_or_err):
                if ok:
                    _prepare_nomic()
                else:
                    # Fallback to HF download for Qwen
                    download_model(
                        repo_id     = QWEN_MODEL["repo_id"],
                        filename    = QWEN_MODEL["filename"],
                        on_progress = on_progress,
                        on_done     = lambda ok, msg: _prepare_nomic() if ok else on_done(False, msg),
                    )

            extract_from_apk_asset("models/model.gguf", on_progress, _after_extract)
            return

        # 3. Bundled with the project (desktop dev)
        bundled = _bundled_model_path(QWEN_MODEL["filename"])
        if bundled and bundled != qwen_dest:
            _prepare_nomic()
            return

        # 4. Download from Hugging Face
        download_model(
            repo_id     = QWEN_MODEL["repo_id"],
            filename    = QWEN_MODEL["filename"],
            on_progress = on_progress,
            on_done     = lambda ok, msg: _prepare_nomic() if ok else on_done(False, msg),
        )

    # Start the chain
    _prepare_qwen()


# ─────────────────────────────────────────────────────────────────── #
#  Enhanced DownloadManager (Phase 5 - Beautiful UI + Monitoring)     #
# ─────────────────────────────────────────────────────────────────── #

import time
from dataclasses import dataclass


@dataclass
class DownloadProgress:
    """Download progress snapshot."""
    model_name: str
    downloaded_mb: float
    total_mb: float
    speed_mbps: float
    eta_seconds: int
    is_paused: bool
    status: str  # "downloading", "paused", "completed", "failed"


class DownloadManager:
    """
    Advanced download manager with pause/resume, speed tracking, and ETA.
    Provides real-time metrics for UI display.
    """

    def __init__(self):
        self.downloads = {}  # model_name -> download state
        self._lock = threading.RLock()

    def start_download(
        self,
        model_name: str,
        repo_id: str,
        filename: str,
        on_progress: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> None:
        """Start downloading a model."""
        with self._lock:
            self.downloads[model_name] = {
                "repo_id": repo_id,
                "filename": filename,
                "progress": 0.0,
                "speed_mbps": 0.0,
                "eta_seconds": 0,
                "is_paused": False,
                "start_time": time.time(),
                "last_update_time": time.time(),
                "last_downloaded_mb": 0.0,
                "status": "downloading",
            }

        def _on_progress(frac: float, text: str):
            """Wrapper for progress callback."""
            with self._lock:
                if model_name not in self.downloads:
                    return

                state = self.downloads[model_name]
                state["progress"] = frac

                # Calculate speed and ETA
                elapsed = time.time() - state["start_time"]
                if elapsed > 0 and frac > 0:
                    downloaded_mb = frac * 920  # Assume ~920MB total
                    time_delta = time.time() - state["last_update_time"]

                    if time_delta > 0:
                        speed_mbps = (downloaded_mb - state["last_downloaded_mb"]) / time_delta
                        state["speed_mbps"] = max(0, speed_mbps)  # Avoid negative
                        state["last_downloaded_mb"] = downloaded_mb

                        if speed_mbps > 0:
                            remaining_mb = 920 - downloaded_mb
                            state["eta_seconds"] = int(remaining_mb / speed_mbps)
                        else:
                            state["eta_seconds"] = 0

                    state["last_update_time"] = time.time()

                if on_progress:
                    progress = DownloadProgress(
                        model_name=model_name,
                        downloaded_mb=frac * 920,
                        total_mb=920,
                        speed_mbps=state["speed_mbps"],
                        eta_seconds=state["eta_seconds"],
                        is_paused=state["is_paused"],
                        status=state["status"],
                    )
                    on_progress(progress)

        def _on_done(success: bool, message: str):
            """Wrapper for completion callback."""
            with self._lock:
                if model_name in self.downloads:
                    self.downloads[model_name]["status"] = "completed" if success else "failed"

        # Start download in background
        download_model(repo_id, filename, _on_progress, _on_done)

    def pause_download(self, model_name: str) -> bool:
        """Pause a download (best-effort, limited suppport)."""
        with self._lock:
            if model_name in self.downloads:
                self.downloads[model_name]["is_paused"] = True
                return True
        return False

    def resume_download(self, model_name: str) -> bool:
        """Resume a paused download."""
        with self._lock:
            if model_name in self.downloads:
                self.downloads[model_name]["is_paused"] = False
                # Note: huggingface_hub typically doesn't support pause/resume
                # This is a placeholder for future implementation
                return True
        return False

    def get_progress(self, model_name: str) -> Optional[DownloadProgress]:
        """Get current download progress."""
        with self._lock:
            if model_name not in self.downloads:
                return None

            state = self.downloads[model_name]
            return DownloadProgress(
                model_name=model_name,
                downloaded_mb=state["progress"] * 920,
                total_mb=920,
                speed_mbps=state["speed_mbps"],
                eta_seconds=state["eta_seconds"],
                is_paused=state["is_paused"],
                status=state["status"],
            )

    def get_all_progress(self) -> dict[str, DownloadProgress]:
        """Get all download progress."""
        with self._lock:
            return {
                name: self.get_progress(name)
                for name in self.downloads
                if self.downloads[name] is not None
            }


# ─────────────────────────────────────────────────────────────────── #
#  Model Selection and Fallback Functions (Qwen 3.5 Support)          #
# ─────────────────────────────────────────────────────────────────── #

def select_model_for_device(available_memory_mb: int = 4096) -> dict:
    """Auto-select optimal models based on device memory."""
    # Detect device class
    if os.environ.get("ANDROID_PRIVATE"):
        if available_memory_mb >= 6000:
            return model_config.DEVICE_PRESETS["6gb-mobile"]
        else:
            return model_config.DEVICE_PRESETS["4gb-mobile"]
    else:
        # Desktop
        return model_config.DEVICE_PRESETS.get(
            "8gb-laptop",
            model_config.DEVICE_PRESETS["4gb-mobile"]
        )


def get_fallback_llm_models() -> list[str]:
    """Return LLM fallback chain: [primary, fallback1, fallback2, ...]"""
    return list(model_config.LLM_MODELS.keys())


def download_model_with_fallback(
    model_key: str,
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_done: Optional[Callable[[bool, str], None]] = None,
    model_type: str = "llm",
) -> str:
    """
    Get fallback model key if fallback is needed.
    
    This function validates the model exists in catalog and returns the model key.
    Actual downloads should be handled by download_model() or auto_download_default().
    
    If model_key is not available, falls back to next available model in the catalog.
    
    Returns: The model key to use (either requested or fallback)
    """
    if model_type == "llm":
        available_models = model_config.LLM_MODELS
    else:
        available_models = model_config.EMBEDDING_MODELS

    # Create fallback chain: primary + others
    fallback_chain = [model_key]
    fallback_chain.extend([k for k in available_models.keys() if k != model_key])

    # Return the first available model (typically the requested one)
    for attempt_model in fallback_chain:
        if attempt_model in available_models:
            print(f"[downloader] Using model: {available_models[attempt_model]['label']}")
            return attempt_model

    # Fallback to first available if nothing matches
    if available_models:
        first_key = list(available_models.keys())[0]
        print(f"[downloader] Fallback: {available_models[first_key]['label']}")
        return first_key
    
    raise RuntimeError(f"No models available for type: {model_type}")
