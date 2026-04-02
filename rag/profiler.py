"""
Phase 4: Performance Profiling Module

Comprehensive profiling of O-RAG system for mobile deployment:
- Memory usage patterns
- CPU/GPU utilization
- Battery impact estimation
- Latency analysis
- Resource constraint validation
"""

import time
import psutil
import threading
import statistics
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PerformanceMetrics:
    """Container for performance measurements"""
    timestamp: datetime
    memory_rss_mb: float  # Resident set size
    memory_vms_mb: float  # Virtual memory size
    cpu_percent: float    # CPU utilization %
    cpu_time_user: float  # User mode CPU time (seconds)
    cpu_time_system: float  # System mode CPU time (seconds)
    threads: int          # Thread count


class MemoryProfiler:
    """Monitor memory usage patterns"""
    
    def __init__(self, target_device_mb: int = 4096):
        """
        Args:
            target_device_mb: Total RAM on target device (default 4GB)
        """
        self.process = psutil.Process()
        self.target_device_mb = target_device_mb
        self.measurements: List[PerformanceMetrics] = []
        
    def start_measurement(self) -> None:
        """Begin measuring memory"""
        self.start_time = time.time()
        self.baseline_memory = self.process.memory_info().rss / 1024 / 1024
        
    def snapshot(self) -> PerformanceMetrics:
        """Take instantaneous snapshot"""
        mem_info = self.process.memory_info()
        cpu_times = self.process.cpu_times()
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            memory_rss_mb=mem_info.rss / 1024 / 1024,
            memory_vms_mb=mem_info.vms / 1024 / 1024,
            cpu_percent=self.process.cpu_percent(interval=0.1),
            cpu_time_user=cpu_times.user,
            cpu_time_system=cpu_times.system,
            threads=self.process.num_threads(),
        )
    
    def record_snapshot(self) -> PerformanceMetrics:
        """Record snapshot to history"""
        metrics = self.snapshot()
        self.measurements.append(metrics)
        return metrics
    
    def get_memory_increase(self) -> float:
        """Get total memory increase since start (MB)"""
        if not self.measurements:
            return 0
        return self.measurements[-1].memory_rss_mb - self.baseline_memory
    
    def get_peak_memory(self) -> float:
        """Get peak RSS memory during measurement (MB)"""
        if not self.measurements:
            return 0
        return max(m.memory_rss_mb for m in self.measurements)
    
    def get_average_memory(self) -> float:
        """Get average memory during measurement (MB)"""
        if not self.measurements:
            return 0
        return statistics.mean(m.memory_rss_mb for m in self.measurements)
    
    def check_device_fit(self, available_mb: int = 1024, margin_mb: int = 50) -> Tuple[bool, str]:
        """
        Check if memory usage fits within device constraints
        
        Args:
            available_mb: Available memory for RAG on device
            margin_mb: Safety margin to reserve
            
        Returns:
            (fits, message)
        """
        peak = self.get_peak_memory()
        total_used = peak + margin_mb
        fits = total_used < available_mb
        
        message = (
            f"Peak: {peak:.1f}MB, "
            f"With margin: {total_used:.1f}MB, "
            f"Budget: {available_mb}MB - "
            f"{'✅ FITS' if fits else '❌ EXCEEDS'}"
        )
        
        return fits, message
    
    def report(self) -> Dict:
        """Generate profiling report"""
        return {
            'measurements_count': len(self.measurements),
            'baseline_mb': self.baseline_memory,
            'peak_mb': self.get_peak_memory(),
            'average_mb': self.get_average_memory(),
            'increase_mb': self.get_memory_increase(),
            'device_fit': self.check_device_fit(),
        }


class LatencyProfiler:
    """Profile query latency"""
    
    def __init__(self):
        self.measurements: Dict[str, List[float]] = {}
        
    def measure(self, operation: str, func, *args, **kwargs) -> float:
        """
        Measure execution time of function
        
        Args:
            operation: Name of operation
            func: Callable to measure
            *args, **kwargs: Arguments to func
            
        Returns:
            Execution time in milliseconds
        """
        start = time.time()
        result = func(*args, **kwargs)
        elapsed_ms = (time.time() - start) * 1000
        
        if operation not in self.measurements:
            self.measurements[operation] = []
        self.measurements[operation].append(elapsed_ms)
        
        return elapsed_ms
    
    def get_stats(self, operation: str) -> Dict:
        """Get latency statistics for operation"""
        if operation not in self.measurements:
            return {}
        
        times = self.measurements[operation]
        return {
            'count': len(times),
            'min_ms': min(times),
            'max_ms': max(times),
            'mean_ms': statistics.mean(times),
            'median_ms': statistics.median(times),
            'stdev_ms': statistics.stdev(times) if len(times) > 1 else 0,
        }
    
    def report(self) -> Dict:
        """Generate latency report"""
        return {
            operation: self.get_stats(operation)
            for operation in self.measurements
        }


class BatteryEstimator:
    """Estimate battery impact of operations"""
    
    # Power consumption constants (mW)
    CPU_ACTIVE_MW = 200         # Cortex-A74
    CPU_IDLE_MW = 50            # Idle state
    GPU_ACTIVE_MW = 300         # Mali or Adreno
    GPU_IDLE_MW = 0
    RAM_PER_GB_MW = 10          # Per GB active
    LCD_ON_MW = 500             # Display on
    LCD_OFF_MW = 0
    
    def __init__(self, battery_mah: int = 5000):
        """
        Args:
            battery_mah: Battery capacity (default 5000mAh)
        """
        self.battery_mah = battery_mah
        
    def estimate_energy(
        self,
        cpu_active_ms: float,
        gpu_active_ms: float = 0,
        ram_gb: float = 1,
        lcd_on: bool = True,
    ) -> float:
        """
        Estimate energy consumption
        
        Returns:
            Energy in mWh
        """
        cpu_energy = (
            self.CPU_ACTIVE_MW * (cpu_active_ms / 1000) +
            self.CPU_IDLE_MW * max(0, 60 - cpu_active_ms/1000)  # 1 minute window
        ) / 60
        
        gpu_energy = self.GPU_ACTIVE_MW * (gpu_active_ms / 1000) / 60
        ram_energy = self.RAM_PER_GB_MW * ram_gb / 60
        lcd_energy = self.LCD_ON_MW / 60 if lcd_on else 0
        
        return cpu_energy + gpu_energy + ram_energy + lcd_energy
    
    def estimate_battery_life(
        self,
        energy_per_operation_mwh: float,
        operations_per_hour: int = 100,
    ) -> Tuple[float, float]:
        """
        Estimate battery life
        
        Returns:
            (hours, days)
        """
        energy_per_hour = energy_per_operation_mwh * operations_per_hour
        hours = self.battery_mah / energy_per_hour
        days = hours / 24
        return hours, days
    
    def compare_scenarios(
        self,
        with_cache_ms: float,
        without_cache_ms: float,
        cache_hit_rate: float = 0.7,
    ) -> Dict:
        """
        Compare battery usage with/without caching
        
        Args:
            with_cache_ms: Latency with cache hit
            without_cache_ms: Latency with cache miss
            cache_hit_rate: Expected cache hit rate
            
        Returns:
            Comparison report
        """
        hits_per_100 = int(cache_hit_rate * 100)
        misses_per_100 = 100 - hits_per_100
        
        # Energy per 100 operations
        energy_with_cache = (
            hits_per_100 * self.estimate_energy(with_cache_ms, gpu_active_ms=0) +
            misses_per_100 * self.estimate_energy(without_cache_ms, gpu_active_ms=50)
        ) / 100
        
        energy_without_cache = (
            100 * self.estimate_energy(without_cache_ms, gpu_active_ms=50)
        ) / 100
        
        savings_pct = ((energy_without_cache - energy_with_cache) / energy_without_cache) * 100
        
        hours_with, days_with = self.estimate_battery_life(energy_with_cache)
        hours_without, days_without = self.estimate_battery_life(energy_without_cache)
        
        return {
            'energy_per_op_with_cache_mwh': energy_with_cache,
            'energy_per_op_without_cache_mwh': energy_without_cache,
            'savings_pct': savings_pct,
            'battery_hours_with_cache': hours_with,
            'battery_days_with_cache': days_with,
            'battery_hours_without_cache': hours_without,
            'battery_days_without_cache': days_without,
            'additional_hours_per_charge': hours_with - hours_without,
        }


class DeviceConstraintValidator:
    """Validate system fits within device constraints"""
    
    def __init__(
        self,
        total_ram_mb: int = 4096,
        available_for_rag_mb: int = 1024,
        emergency_reserve_mb: int = 50,
        target_latency_ms: int = 500,
    ):
        self.total_ram_mb = total_ram_mb
        self.available_for_rag_mb = available_for_rag_mb
        self.emergency_reserve_mb = emergency_reserve_mb
        self.target_latency_ms = target_latency_ms
        self.working_memory_mb = available_for_rag_mb - emergency_reserve_mb
        
    def validate_memory(self, peak_memory_mb: float) -> Tuple[bool, str]:
        """Validate memory usage fits in device"""
        fits = peak_memory_mb < self.working_memory_mb
        pct = (peak_memory_mb / self.working_memory_mb) * 100
        
        return fits, (
            f"Memory: {peak_memory_mb:.1f}MB / {self.working_memory_mb}MB "
            f"({pct:.1f}%) - {'✅ OK' if fits else '❌ EXCEEDS'}"
        )
    
    def validate_latency(self, measured_latency_ms: float) -> Tuple[bool, str]:
        """Validate latency meets target"""
        meets = measured_latency_ms < self.target_latency_ms
        
        return meets, (
            f"Latency: {measured_latency_ms:.1f}ms / {self.target_latency_ms}ms - "
            f"{'✅ OK' if meets else '⚠️ EXCEEDS'}"
        )
    
    def full_report(
        self,
        peak_memory_mb: float,
        measured_latency_ms: float,
    ) -> Dict:
        """Generate full device constraint report"""
        mem_ok, mem_msg = self.validate_memory(peak_memory_mb)
        lat_ok, lat_msg = self.validate_latency(measured_latency_ms)
        
        return {
            'device': f"{self.total_ram_mb}MB device",
            'available_for_rag': f"{self.available_for_rag_mb}MB",
            'working_memory': f"{self.working_memory_mb}MB",
            'emergency_reserve': f"{self.emergency_reserve_mb}MB",
            'memory_validation': mem_msg,
            'latency_validation': lat_msg,
            'all_constraints_met': mem_ok and lat_ok,
        }


# Convenience functions

def profile_memory(func, *args, **kwargs) -> Tuple[float, float]:
    """
    Profile memory usage of a function
    
    Returns:
        (memory_increase_mb, peak_memory_mb)
    """
    profiler = MemoryProfiler()
    profiler.start_measurement()
    
    result = func(*args, **kwargs)
    
    profiler.record_snapshot()
    return profiler.get_memory_increase(), profiler.get_peak_memory()


def profile_latency(func, iterations: int = 10, *args, **kwargs) -> Dict:
    """
    Profile latency of a function
    
    Returns:
        Statistics dict
    """
    profiler = LatencyProfiler()
    
    for _ in range(iterations):
        profiler.measure('operation', func, *args, **kwargs)
    
    return profiler.get_stats('operation')


# ─────────────────────────────────────────────────────────────────── #
#  Analytics Integration (Phase 5 - Beautiful UI + Monitoring)        #
# ─────────────────────────────────────────────────────────────────── #

class ProfilerWithAnalytics:
    """Integrated profiler that reports metrics to analytics system."""

    def __init__(self, analytics_enabled: bool = True):
        """
        Args:
            analytics_enabled: Whether to send metrics to analytics
        """
        self.analytics_enabled = analytics_enabled
        self.analytics = None
        self.health = None

        if analytics_enabled:
            try:
                from analytics import get_analytics, get_health_monitor
                self.analytics = get_analytics()
                self.health = get_health_monitor()
            except ImportError:
                print("[profiler] analytics.py not available, metrics disabled")
                self.analytics_enabled = False

        self.mem_profiler = MemoryProfiler()
        self.lat_profiler = LatencyProfiler()
        self.battery = BatteryEstimator()

    def profile_query(
        self,
        query_text: str,
        func,
        *args,
        cache_hit: bool = False,
        tokens_generated: int = 0,
        **kwargs
    ) -> Tuple[float, Any]:
        """
        Profile a query operation and report to analytics.

        Returns:
            (latency_ms, result)
        """
        start = time.time()
        result = func(*args, **kwargs)
        latency_ms = (time.time() - start) * 1000

        if self.analytics_enabled and self.analytics:
            try:
                from analytics import QueryMetrics
                
                metrics = QueryMetrics(
                    query_text=query_text[:200],
                    latency_ms=latency_ms,
                    cache_hit=cache_hit,
                    tokens_generated=tokens_generated,
                    device_temp_c=None,
                    battery_drain_pct=None,
                    timestamp=datetime.now().isoformat(),
                )
                self.analytics.record_query(metrics)
            except Exception as e:
                print(f"[profiler] Failed to record query: {e}")

        return latency_ms, result

    def profile_download(
        self,
        model_name: str,
        model_size_mb: float,
        downloaded_mb: float,
        speed_mbps: float,
        eta_seconds: int,
        status: str = "downloading",
    ) -> None:
        """Record download progress."""
        if self.analytics_enabled and self.analytics:
            try:
                from analytics import DownloadMetrics
                
                metrics = DownloadMetrics(
                    model_name=model_name,
                    model_size_mb=model_size_mb,
                    downloaded_mb=downloaded_mb,
                    speed_mbps=speed_mbps,
                    eta_seconds=eta_seconds,
                    status=status,
                    timestamp=datetime.now().isoformat(),
                )
                self.analytics.record_download(metrics)
            except Exception as e:
                print(f"[profiler] Failed to record download: {e}")

    def get_health_status(self) -> Dict:
        """Get device health status."""
        if self.health:
            return self.health.get_full_report()
        return {"status": "unknown"}

    def check_memory_pressure(self) -> str:
        """Check current memory pressure level."""
        if self.health:
            mem = self.health.get_current_memory()
            return mem.pressure.value
        return "unknown"


if __name__ == '__main__':
    # Example usage
    print("Performance Profiling Module for O-RAG Phase 4")
    print("=" * 60)
    
    # Create profilers
    mem_profiler = MemoryProfiler()
    lat_profiler = LatencyProfiler()
    battery_est = BatteryEstimator()
    validator = DeviceConstraintValidator()
    
    # Create integrated profiler with analytics
    profiler = ProfilerWithAnalytics(analytics_enabled=True)
    
    print("\n✅ Profilers initialized")
    print("Use in your tests as shown in 12_phase4_integration_testing.ipynb")
    print("\nHealth status:")
    print(profiler.get_health_status())
