"""
memory_manager.py — Automatic Memory Optimization for 4GB Devices.

Monitors device memory in real-time and makes automatic decisions:
  • Dynamic context window sizing (768 → 512 → 256 tokens on pressure)
  • Chunk size optimization (80 → 64 → 48 words on pressure)
  • Emergency cache clearing on memory pressure (CAUTION/CRITICAL)
  • Token buffer adjustment for streaming
  • Database query optimization on low memory
  • Automatic model offloading recommendations

Integration points:
  • HealthMonitor callbacks for memory pressure changes
  • Pipeline context configuration
  • Retriever chunk queries
  • LLM token streaming buffer
  • Database cleanup triggers
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional
from datetime import datetime, timedelta


class MemoryPressure(Enum):
    """Memory pressure levels matching HealthMonitor classification."""
    NORMAL = "NORMAL"          # >400MB available
    CAUTION = "CAUTION"        # 200-400MB available
    CRITICAL = "CRITICAL"      # <200MB available


@dataclass
class MemoryConfig:
    """Memory-based configuration parameters."""
    # Context window sizes (tokens)
    context_window_normal: int = 768          # Full context on normal memory
    context_window_caution: int = 512         # Reduced on caution
    context_window_critical: int = 256        # Emergency on critical
    
    # Chunk sizing (words per chunk)
    chunk_size_normal: int = 80
    chunk_size_caution: int = 64
    chunk_size_critical: int = 48
    
    # Token buffer (for streaming)
    token_buffer_normal: int = 100
    token_buffer_caution: int = 50
    token_buffer_critical: int = 25
    
    # Query limits
    max_chunks_normal: int = 10
    max_chunks_caution: int = 5
    max_chunks_critical: int = 3
    
    # Cache behavior
    cache_ttl_seconds_normal: int = 3600        # 1 hour on normal
    cache_ttl_seconds_caution: int = 300        # 5 min on caution
    cache_ttl_seconds_critical: int = 60        # 1 min on critical
    
    # Optimization flags
    enable_query_batching: bool = True
    enable_aggressive_cleanup: bool = False
    offload_recommendation: bool = False
    
    def get_context_window(self, pressure: MemoryPressure) -> int:
        """Get context window size for current pressure level."""
        return {
            MemoryPressure.NORMAL: self.context_window_normal,
            MemoryPressure.CAUTION: self.context_window_caution,
            MemoryPressure.CRITICAL: self.context_window_critical,
        }.get(pressure, self.context_window_normal)
    
    def get_chunk_size(self, pressure: MemoryPressure) -> int:
        """Get chunk size (words) for current pressure level."""
        return {
            MemoryPressure.NORMAL: self.chunk_size_normal,
            MemoryPressure.CAUTION: self.chunk_size_caution,
            MemoryPressure.CRITICAL: self.chunk_size_critical,
        }.get(pressure, self.chunk_size_normal)
    
    def get_max_chunks(self, pressure: MemoryPressure) -> int:
        """Get max retrieval chunks for current pressure level."""
        return {
            MemoryPressure.NORMAL: self.max_chunks_normal,
            MemoryPressure.CAUTION: self.max_chunks_caution,
            MemoryPressure.CRITICAL: self.max_chunks_critical,
        }.get(pressure, self.max_chunks_normal)
    
    def get_cache_ttl(self, pressure: MemoryPressure) -> int:
        """Get cache TTL (seconds) for current pressure level."""
        return {
            MemoryPressure.NORMAL: self.cache_ttl_seconds_normal,
            MemoryPressure.CAUTION: self.cache_ttl_seconds_caution,
            MemoryPressure.CRITICAL: self.cache_ttl_seconds_critical,
        }.get(pressure, self.cache_ttl_seconds_normal)


# ================================================================== #
#  Memory Manager Singleton                                           #
# ================================================================== #

class MemoryManager:
    """
    Monitors device memory and makes automatic optimization decisions.
    
    Singleton pattern - use get_memory_manager() to access.
    """
    
    _instance: Optional[MemoryManager] = None
    _lock = threading.RLock()
    
    def __init__(self):
        """Initialize memory manager."""
        self.config = MemoryConfig()
        self.current_pressure = MemoryPressure.NORMAL
        self.last_pressure_check = datetime.now()
        self.pressure_callbacks: list[Callable[[MemoryPressure], None]] = []
        self._emergency_cleanup_scheduled = False
        self._monitoring_active = False
        
        # Hook into HealthMonitor if available
        self._register_health_callbacks()
    
    def _register_health_callbacks(self):
        """Register callbacks with HealthMonitor for memory pressure changes."""
        try:
            from analytics import get_health_monitor
            health = get_health_monitor()
            
            # Register callback for when HealthMonitor detects pressure changes
            if hasattr(health, 'memory_pressure_callbacks'):
                def on_pressure_change(new_pressure: str):
                    try:
                        pressure = MemoryPressure[new_pressure]
                        self.on_memory_pressure_change(pressure)
                    except (KeyError, ValueError):
                        pass
                
                health.memory_pressure_callbacks.append(on_pressure_change)
                print("[memory_mgr] Registered with HealthMonitor for pressure callbacks")
        except Exception as e:
            print(f"[memory_mgr] Could not register health callbacks: {e}")
    
    def on_memory_pressure_change(self, new_pressure: MemoryPressure):
        """Called when memory pressure changes. Triggers optimizations."""
        if new_pressure == self.current_pressure:
            return  # No change
        
        old_pressure = self.current_pressure
        self.current_pressure = new_pressure
        self.last_pressure_check = datetime.now()
        
        print(f"[memory_mgr] Memory pressure changed: {old_pressure.value} → {new_pressure.value}")
        
        # Trigger emergency cleanup on CRITICAL pressure
        if new_pressure == MemoryPressure.CRITICAL:
            self._trigger_emergency_cleanup()
        
        # Notify all registered callbacks
        for callback in self.pressure_callbacks:
            try:
                callback(new_pressure)
            except Exception as e:
                print(f"[memory_mgr] Error in pressure callback: {e}")
    
    def _trigger_emergency_cleanup(self):
        """Perform emergency memory cleanup when CRITICAL pressure detected."""
        if self._emergency_cleanup_scheduled:
            return  # Already scheduled
        
        self._emergency_cleanup_scheduled = True
        print("[memory_mgr] 🚨 CRITICAL memory pressure - initiating emergency cleanup")
        
        def cleanup():
            try:
                # Clear QueryCache if available
                self._clear_query_cache()
                
                # Clear conversation history (keep only last 2 turns)
                self._trim_conversation_history(max_turns=2)
                
                # Force garbage collection
                import gc
                gc.collect()
                
                print("[memory_mgr] Emergency cleanup complete")
            except Exception as e:
                print(f"[memory_mgr] Error during emergency cleanup: {e}")
            finally:
                self._emergency_cleanup_scheduled = False
        
        # Run cleanup in background thread to avoid blocking UI
        threading.Thread(target=cleanup, daemon=True).start()
    
    def _clear_query_cache(self):
        """Clear the QueryCache to free memory."""
        try:
            from rag.db import QueryCache
            cache = QueryCache()
            deleted = cache.clear()
            print(f"[memory_mgr] Cleared query cache ({deleted} entries)")
        except Exception as e:
            print(f"[memory_mgr] Could not clear query cache: {e}")
    
    def _trim_conversation_history(self, max_turns: int = 2):
        """Trim conversation history to save memory. Keeps only last N turns."""
        try:
            from rag.db import get_db
            db = get_db()
            
            # Get conversation ID
            cursor = db.cursor()
            cursor.execute(
                "SELECT id FROM conversations ORDER BY created_at DESC LIMIT 1"
            )
            result = cursor.fetchone()
            if not result:
                return
            
            conv_id = result[0]
            
            # Get total number of messages
            cursor.execute(
                "SELECT COUNT(*) FROM messages WHERE conversation_id = ?",
                (conv_id,)
            )
            total_msgs = cursor.fetchone()[0]
            
            # Delete old messages, keeping only last (max_turns * 2) messages
            keep_count = max_turns * 2
            if total_msgs > keep_count:
                cursor.execute(
                    """
                    DELETE FROM messages 
                    WHERE conversation_id = ?
                    AND id NOT IN (
                        SELECT id FROM messages 
                        WHERE conversation_id = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    )
                    """,
                    (conv_id, conv_id, keep_count)
                )
                deleted = total_msgs - cursor.rowcount
                db.commit()
                print(f"[memory_mgr] Trimmed conversation history ({deleted} messages removed)")
        except Exception as e:
            print(f"[memory_mgr] Could not trim conversation: {e}")
    
    # ── Configuration access ─────────────────────────────────────── #
    
    def get_active_config(self) -> MemoryConfig:
        """Get current configuration based on memory pressure."""
        return self.config
    
    def get_context_window(self) -> int:
        """Get current context window size (auto-adjusted by pressure)."""
        size = self.config.get_context_window(self.current_pressure)
        print(f"[memory_mgr] Using context window: {size} tokens ({self.current_pressure.value})")
        return size
    
    def get_chunk_size(self) -> int:
        """Get current chunk size in words (auto-adjusted by pressure)."""
        size = self.config.get_chunk_size(self.current_pressure)
        print(f"[memory_mgr] Using chunk size: {size} words ({self.current_pressure.value})")
        return size
    
    def get_max_retrieval_chunks(self) -> int:
        """Get max number of chunks to retrieve (auto-adjusted by pressure)."""
        max_chunks = self.config.get_max_chunks(self.current_pressure)
        print(f"[memory_mgr] Max retrieval chunks: {max_chunks} ({self.current_pressure.value})")
        return max_chunks
    
    def get_token_buffer_size(self) -> int:
        """Get token buffer for streaming (auto-adjusted by pressure)."""
        buffer = {
            MemoryPressure.NORMAL: self.config.token_buffer_normal,
            MemoryPressure.CAUTION: self.config.token_buffer_caution,
            MemoryPressure.CRITICAL: self.config.token_buffer_critical,
        }.get(self.current_pressure, self.config.token_buffer_normal)
        return buffer
    
    def should_batch_queries(self) -> bool:
        """Whether to batch queries to reduce memory usage."""
        return self.config.enable_query_batching and self.current_pressure != MemoryPressure.NORMAL
    
    def should_offload_model(self) -> bool:
        """Whether to recommend model offloading (CRITICAL only)."""
        return self.current_pressure == MemoryPressure.CRITICAL
    
    # ── Callbacks ────────────────────────────────────────────────── #
    
    def register_pressure_callback(self, callback: Callable[[MemoryPressure], None]):
        """Register a callback to be called when memory pressure changes."""
        self.pressure_callbacks.append(callback)
    
    def unregister_pressure_callback(self, callback: Callable[[MemoryPressure], None]):
        """Unregister a pressure change callback."""
        if callback in self.pressure_callbacks:
            self.pressure_callbacks.remove(callback)
    
    # ── Status/Debug ─────────────────────────────────────────────── #
    
    def get_status(self) -> dict:
        """Get current memory management status."""
        return {
            "current_pressure": self.current_pressure.value,
            "context_window": self.get_context_window(),
            "chunk_size": self.get_chunk_size(),
            "max_retrieval_chunks": self.get_max_retrieval_chunks(),
            "token_buffer": self.get_token_buffer_size(),
            "batch_queries": self.should_batch_queries(),
            "should_offload": self.should_offload_model(),
            "last_check": self.last_pressure_check.isoformat(),
        }


# ================================================================== #
#  Singleton Access                                                   #
# ================================================================== #

def get_memory_manager() -> MemoryManager:
    """Get or create the MemoryManager singleton."""
    if MemoryManager._instance is None:
        with MemoryManager._lock:
            if MemoryManager._instance is None:
                MemoryManager._instance = MemoryManager()
    return MemoryManager._instance


def start_memory_optimization():
    """Initialize memory optimization system."""
    mgr = get_memory_manager()
    print(f"[memory_mgr] Memory optimization system started")
    print(f"[memory_mgr] Initial config: {mgr.get_status()}")
    return mgr


# ================================================================== #
#  Integration Helpers                                                #
# ================================================================== #

class MemoryAwareRetriever:
    """
    Wrapper for retriever that applies memory-based optimizations.
    Use this instead of raw retriever.retrieve() calls.
    """
    
    def __init__(self, retriever):
        """Initialize with a base retriever instance."""
        self.retriever = retriever
        self.mgr = get_memory_manager()
    
    def retrieve_optimized(self, query: str, top_k: int | None = None) -> list[dict]:
        """
        Retrieve documents with memory-aware optimizations:
        - Limits number of chunks based on memory pressure
        - Adjusts chunk size based on memory pressure
        """
        # Override top_k if memory pressure requires it
        effective_k = top_k or self.mgr.get_max_retrieval_chunks()
        
        # If CRITICAL pressure, also suggest batch queries
        if self.mgr.should_batch_queries():
            print(
                f"[retriever] Memory optimization: reducing retrieval from "
                f"{top_k or 10} to {effective_k} chunks"
            )
        
        # Retrieve with optimized limit
        return self.retriever.retrieve(query, top_k=effective_k)


class MemoryAwareLLM:
    """
    Wrapper for LLM that applies memory-based optimizations.
    Automatically adjusts context window and token buffer based on memory pressure.
    """
    
    def __init__(self, llm):
        """Initialize with a base LLM instance."""
        self.llm = llm
        self.mgr = get_memory_manager()
    
    def generate_optimized(
        self, 
        prompt: str, 
        max_tokens: int | None = None,
        context_window: int | None = None,
    ) -> str:
        """
        Generate with memory-aware optimizations:
        - Adjusts context window based on memory pressure
        - Reduces token generation on caution/critical
        """
        # Get memory-optimized context window
        optimized_context = context_window or self.mgr.get_context_window()
        
        # Limit token generation on caution/critical
        max_tokens_limit = self.mgr.get_token_buffer_size()
        effective_max = min(max_tokens or 256, max_tokens_limit)
        
        if self.mgr.current_pressure != MemoryPressure.NORMAL:
            print(
                f"[llm] Memory optimization: "
                f"context={optimized_context}tokens, "
                f"max_output={effective_max}tokens "
                f"({self.mgr.current_pressure.value})"
            )
        
        # Generate with optimized parameters
        return self.llm.generate(
            prompt,
            max_tokens=effective_max,
            context_window=optimized_context,
        )
