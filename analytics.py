"""
analytics.py — Centralized analytics, health monitoring, and session tracking for O-RAG.

Tracks:
  • Memory usage (RSS, VMS, peak)
  • Query performance (latency, cache hits)
  • Download statistics
  • Battery impact estimation
  • Device constraints & health status
  • User session analytics

Stores metrics in local SQLite database for dashboard visualization.
"""
from __future__ import annotations

import os
import sqlite3
import threading
import time
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

try:
    import psutil
except ImportError:
    psutil = None  # Graceful fallback


# ─────────────────────────────────────────────────────────────────── #
#  Enums & Data Classes                                               #
# ─────────────────────────────────────────────────────────────────── #

class MemoryPressure(Enum):
    """Memory pressure level on device."""
    NORMAL = "normal"        # >400MB available
    CAUTION = "caution"      # 200-400MB available
    CRITICAL = "critical"    # <200MB available


@dataclass
class MemoryMetrics:
    """Snapshot of current memory state."""
    rss_mb: float             # Resident set size (physical RAM)
    vms_mb: float             # Virtual memory size
    peak_rss_mb: float        # Peak RSS this session
    available_mb: float       # Available system memory
    device_total_mb: float    # Total device RAM
    pressure: MemoryPressure  # Current pressure level


@dataclass
class QueryMetrics:
    """Metrics for a single query."""
    query_text: str
    latency_ms: float
    cache_hit: bool
    tokens_generated: int
    device_temp_c: Optional[float]
    battery_drain_pct: Optional[float]
    timestamp: str           # ISO8601


@dataclass
class DownloadMetrics:
    """Metrics for a model download."""
    model_name: str
    model_size_mb: float
    downloaded_mb: float
    speed_mbps: float
    eta_seconds: int
    status: str               # "downloading", "completed", "failed", "paused"
    timestamp: str


@dataclass
class SessionMetrics:
    """Aggregated metrics for current session."""
    session_start: str
    queries_total: int
    cache_hits: int
    cache_misses: int
    avg_latency_ms: float
    peak_memory_mb: float
    documents_loaded: int
    session_duration_seconds: int


# ─────────────────────────────────────────────────────────────────── #
#  AnalyticsCollector — Central metrics capture                       #
# ─────────────────────────────────────────────────────────────────── #

class AnalyticsCollector:
    """Centralized analytics collection with SQLite persistence."""

    def __init__(self, db_path: Optional[str] = None, device_ram_mb: int = 4096):
        """
        Args:
            db_path: Path to SQLite db (defaults to ANDROID_PRIVATE/analytics.db)
            device_ram_mb: Total device RAM in MB (default 4GB)
        """
        if db_path is None:
            base = os.environ.get("ANDROID_PRIVATE", os.path.expanduser("~"))
            db_path = os.path.join(base, "analytics.db")

        self.db_path = db_path
        self.device_ram_mb = device_ram_mb
        self.session_start = datetime.now().isoformat()
        self.queries_total = 0
        self.cache_hits = 0
        self.peak_memory_mb = 0.0
        self._lock = threading.RLock()

        self._init_db()

    def _init_db(self):
        """Create analytics tables if missing."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS queries (
                    id INTEGER PRIMARY KEY,
                    query_text TEXT,
                    latency_ms REAL,
                    cache_hit INTEGER,
                    tokens_generated INTEGER,
                    device_temp_c REAL,
                    battery_drain_pct REAL,
                    timestamp TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY,
                    model_name TEXT,
                    model_size_mb REAL,
                    downloaded_mb REAL,
                    speed_mbps REAL,
                    eta_seconds INTEGER,
                    status TEXT,
                    timestamp TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_snapshots (
                    id INTEGER PRIMARY KEY,
                    rss_mb REAL,
                    vms_mb REAL,
                    available_mb REAL,
                    pressure TEXT,
                    timestamp TEXT
                )
            """)

            conn.commit()

    def record_query(self, metrics: QueryMetrics) -> None:
        """Record a query execution."""
        with self._lock:
            self.queries_total += 1
            if metrics.cache_hit:
                self.cache_hits += 1

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO queries
                (query_text, latency_ms, cache_hit, tokens_generated, device_temp_c, battery_drain_pct, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.query_text[:200],  # Truncate for storage
                metrics.latency_ms,
                1 if metrics.cache_hit else 0,
                metrics.tokens_generated,
                metrics.device_temp_c,
                metrics.battery_drain_pct,
                metrics.timestamp,
            ))
            conn.commit()

    def record_download(self, metrics: DownloadMetrics) -> None:
        """Record download progress."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO downloads
                (model_name, model_size_mb, downloaded_mb, speed_mbps, eta_seconds, status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.model_name,
                metrics.model_size_mb,
                metrics.downloaded_mb,
                metrics.speed_mbps,
                metrics.eta_seconds,
                metrics.status,
                metrics.timestamp,
            ))
            conn.commit()

    def record_memory_snapshot(self, mem: MemoryMetrics) -> None:
        """Record memory state snapshot."""
        with self._lock:
            self.peak_memory_mb = max(self.peak_memory_mb, mem.rss_mb)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO memory_snapshots
                (rss_mb, vms_mb, available_mb, pressure, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                mem.rss_mb,
                mem.vms_mb,
                mem.available_mb,
                mem.pressure.value,
                datetime.now().isoformat(),
            ))
            conn.commit()

    def get_session_metrics(self) -> SessionMetrics:
        """Get current session summary."""
        cache_misses = self.queries_total - self.cache_hits
        cache_hit_rate = self.cache_hits / max(1, self.queries_total)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT AVG(latency_ms) FROM queries WHERE timestamp > ?",
                                  (self.session_start,))
            avg_latency = cursor.fetchone()[0] or 0.0

        duration = (datetime.now() - datetime.fromisoformat(self.session_start)).total_seconds()

        return SessionMetrics(
            session_start=self.session_start,
            queries_total=self.queries_total,
            cache_hits=self.cache_hits,
            cache_misses=cache_misses,
            avg_latency_ms=avg_latency,
            peak_memory_mb=self.peak_memory_mb,
            documents_loaded=0,  # Updated by caller
            session_duration_seconds=int(duration),
        )

    def get_query_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get aggregated query statistics for last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(cache_hit) as hits,
                    AVG(latency_ms) as avg_latency,
                    MIN(latency_ms) as min_latency,
                    MAX(latency_ms) as max_latency
                FROM queries WHERE timestamp > ?
            """, (cutoff.isoformat(),))
            row = cursor.fetchone()

        if row[0] == 0:
            return {"total": 0, "cache_hit_rate": 0, "avg_latency_ms": 0}

        total, hits, avg_lat, min_lat, max_lat = row
        hit_rate = hits / total if total > 0 else 0

        return {
            "total_queries": total,
            "cache_hits": hits,
            "cache_misses": total - hits,
            "cache_hit_rate": f"{hit_rate:.1%}",
            "avg_latency_ms": f"{avg_lat:.1f}",
            "min_latency_ms": f"{min_lat:.1f}",
            "max_latency_ms": f"{max_lat:.1f}",
        }

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get aggregated memory statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    AVG(rss_mb) as avg,
                    MAX(rss_mb) as peak,
                    MIN(available_mb) as min_avail
                FROM memory_snapshots
            """)
            row = cursor.fetchone()

        if row[0] is None:
            return {}

        avg_rss, peak_rss, min_avail = row
        return {
            "avg_memory_mb": f"{avg_rss:.1f}",
            "peak_memory_mb": f"{peak_rss:.1f}",
            "min_available_mb": f"{min_avail:.1f}",
            "device_total_mb": self.device_ram_mb,
        }

    def export_csv(self, output_path: str) -> bool:
        """Export analytics data to CSV."""
        try:
            import csv
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM queries")
                rows = cursor.fetchall()

            with open(output_path, 'w', newline='') as f:
                if rows:
                    writer = csv.DictWriter(f, fieldnames=dict(rows[0]).keys())
                    writer.writeheader()
                    for row in rows:
                        writer.writerow(dict(row))
            return True
        except Exception as e:
            print(f"[analytics] CSV export failed: {e}")
            return False


# ─────────────────────────────────────────────────────────────────── #
#  HealthMonitor — Device constraint checking                         #
# ─────────────────────────────────────────────────────────────────── #

class HealthMonitor:
    """Monitor device health and enforce 4GB-device constraints."""

    def __init__(self, device_ram_mb: int = 4096, reserved_mb: int = 1024):
        """
        Args:
            device_ram_mb: Total device RAM (default 4GB)
            reserved_mb: Reserved for OS/other apps (default 1GB)
        """
        self.device_ram_mb = device_ram_mb
        self.reserved_mb = reserved_mb
        self.available_for_app_mb = device_ram_mb - reserved_mb
        self.memory_pressure_callbacks: List[Callable[[MemoryPressure], None]] = []

    def get_current_memory(self) -> MemoryMetrics:
        """Get current memory state."""
        if psutil is None:
            return self._mock_memory()

        try:
            proc = psutil.Process()
            mem_info = proc.memory_info()
            rss_mb = mem_info.rss / (1024 * 1024)
            vms_mb = mem_info.vms / (1024 * 1024)

            mem_avail = psutil.virtual_memory().available / (1024 * 1024)
            pressure = self._classify_pressure(mem_avail)

            return MemoryMetrics(
                rss_mb=rss_mb,
                vms_mb=vms_mb,
                peak_rss_mb=rss_mb,  # Track externally if needed
                available_mb=mem_avail,
                device_total_mb=self.device_ram_mb,
                pressure=pressure,
            )
        except Exception as e:
            print(f"[health] Memory read failed: {e}")
            return self._mock_memory()

    def _mock_memory(self) -> MemoryMetrics:
        """Fallback mock memory (for testing)."""
        return MemoryMetrics(
            rss_mb=300.0,
            vms_mb=500.0,
            peak_rss_mb=400.0,
            available_mb=2000.0,
            device_total_mb=self.device_ram_mb,
            pressure=MemoryPressure.NORMAL,
        )

    def _classify_pressure(self, available_mb: float) -> MemoryPressure:
        """Classify memory pressure based on available RAM."""
        if available_mb > self.available_for_app_mb * 0.5:
            return MemoryPressure.NORMAL
        elif available_mb > self.available_for_app_mb * 0.25:
            return MemoryPressure.CAUTION
        else:
            return MemoryPressure.CRITICAL

    def can_load_model(self, model_size_mb: float) -> tuple[bool, str]:
        """Check if device can load a model."""
        mem = self.get_current_memory()
        required = model_size_mb + 200  # 200MB buffer for working memory

        if mem.available_mb < required:
            return False, f"Not enough RAM: need {required:.0f}MB, have {mem.available_mb:.0f}MB"
        return True, "OK"

    def register_pressure_callback(self, callback: Callable[[MemoryPressure], None]):
        """Register callback for memory pressure changes."""
        self.memory_pressure_callbacks.append(callback)

    def check_and_notify(self):
        """Check current pressure and notify callbacks if changed."""
        mem = self.get_current_memory()
        for cb in self.memory_pressure_callbacks:
            try:
                cb(mem.pressure)
            except Exception as e:
                print(f"[health] Callback error: {e}")

    def get_full_report(self) -> Dict[str, Any]:
        """Get comprehensive device health report."""
        mem = self.get_current_memory()
        return {
            "device_total_mb": self.device_total_mb,
            "available_for_app_mb": self.available_for_app_mb,
            "current_app_usage_mb": f"{mem.rss_mb:.1f}",
            "system_available_mb": f"{mem.available_mb:.1f}",
            "memory_pressure": mem.pressure.value,
            "can_load_qwen": self.can_load_model(800)[0],
            "can_load_nomic": self.can_load_model(80)[0],
            "status": "✅ Healthy" if mem.pressure == MemoryPressure.NORMAL else (
                "⚠️  Caution" if mem.pressure == MemoryPressure.CAUTION else "🔴 Critical"
            ),
        }


# ─────────────────────────────────────────────────────────────────── #
#  Global instances (singleton pattern)                               #
# ─────────────────────────────────────────────────────────────────── #

_collector: Optional[AnalyticsCollector] = None
_health_monitor: Optional[HealthMonitor] = None


def get_analytics() -> AnalyticsCollector:
    """Get or create global analytics collector."""
    global _collector
    if _collector is None:
        device_ram = int(os.environ.get("DEVICE_RAM_MB", 4096))
        _collector = AnalyticsCollector(device_ram_mb=device_ram)
    return _collector


def get_health_monitor() -> HealthMonitor:
    """Get or create global health monitor."""
    global _health_monitor
    if _health_monitor is None:
        device_ram = int(os.environ.get("DEVICE_RAM_MB", 4096))
        _health_monitor = HealthMonitor(device_ram_mb=device_ram)
    return _health_monitor


# ─────────────────────────────────────────────────────────────────── #
#  Monitoring thread (optional continuous background monitoring)      #
# ─────────────────────────────────────────────────────────────────── #

_monitor_thread: Optional[threading.Thread] = None
_monitor_stop_flag = False


def start_continuous_monitoring(interval_seconds: float = 5.0) -> None:
    """Start background thread to monitor memory continuously."""
    global _monitor_thread, _monitor_stop_flag

    if _monitor_thread is not None:
        return  # Already running

    _monitor_stop_flag = False
    collector = get_analytics()
    health = get_health_monitor()

    def _monitor():
        while not _monitor_stop_flag:
            try:
                mem = health.get_current_memory()
                collector.record_memory_snapshot(mem)
                health.check_and_notify()
                time.sleep(interval_seconds)
            except Exception as e:
                print(f"[analytics] Monitor error: {e}")
                time.sleep(interval_seconds)

    _monitor_thread = threading.Thread(target=_monitor, daemon=True, name="AnalyticsMonitor")
    _monitor_thread.start()


def stop_continuous_monitoring() -> None:
    """Stop background monitoring thread."""
    global _monitor_stop_flag
    _monitor_stop_flag = True
