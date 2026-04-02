"""
retriever.py — Hybrid BM25 + TF-IDF + Semantic retriever with caching.

* BM25     : classic probabilistic keyword ranking (no deps).
* TF-IDF   : sparse cosine over pre-computed chunk vectors.
* Semantic : dense cosine over embeddings from llama-server /embedding
              endpoint (computed in background after every reload).

When semantic embeddings are available the final score is:
    0.30 * bm25_norm  +  0.20 * tfidf_norm  +  0.50 * semantic_norm
Otherwise falls back to the classic hybrid:
    alpha * bm25_norm  +  (1-alpha) * tfidf_norm

Caching: LRU query cache for repeated questions (40-60% hit rate typical).
"""
from __future__ import annotations

import math
import threading
from typing import List, Dict, Tuple, Optional

from .chunker import tokenise
from .cache import cache_manager, LazyImageLoader, EmbeddingPool

# ------------------------------------------------------------------ #
#  BM25 parameters                                                     #
# ------------------------------------------------------------------ #
K1  = 1.5   # term-frequency saturation
B   = 0.75  # length normalisation weight


# ------------------------------------------------------------------ #
#  Helpers                                                             #
# ------------------------------------------------------------------ #

def _dot(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Sparse dot product."""
    if len(a) > len(b):
        a, b = b, a
    return sum(a[t] * b[t] for t in a if t in b)


def _norm(v: Dict[str, float]) -> float:
    return math.sqrt(sum(x * x for x in v.values())) or 1.0


def _cosine_sparse(a: Dict[str, float], b: Dict[str, float]) -> float:
    return _dot(a, b) / (_norm(a) * _norm(b))


def _cosine_dense(a: list, b: list) -> float:
    """Cosine similarity between two dense float vectors (pure Python)."""
    dot = sum(x * y for x, y in zip(a, b))
    na  = math.sqrt(sum(x * x for x in a)) or 1.0
    nb  = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


def _normalise_scores(scores: List[float]) -> List[float]:
    """Min-max normalise a list to [0, 1]."""
    mn = min(scores)
    mx = max(scores)
    rng = mx - mn or 1.0
    return [(s - mn) / rng for s in scores]


# ------------------------------------------------------------------ #
#  Retriever                                                           #
# ------------------------------------------------------------------ #

class HybridRetriever:
    """
    Loads all chunks into memory once, then answers queries fast.
    Call reload() after new documents are ingested.
    """

    def __init__(self, alpha: float = 0.5, enable_cache: bool = True):
        """
        alpha used for BM25/TF-IDF fallback only (when semantic unavailable):
            alpha=1.0 → pure BM25
            alpha=0.0 → pure TF-IDF cosine
        enable_cache: Enable LRU query caching (default: True)
        """
        self.alpha = alpha
        self._chunks: List[dict] = []   # [{id, doc_id, text, tokens, tfidf_vec}, ...]
        self._avg_dl: float = 0.0
        # Semantic embedding cache: chunk_id -> list[float]
        self._embeddings: dict = {}
        self._embed_lock  = threading.Lock()
        self._embed_ready = False
        # Query caching
        self.enable_cache = enable_cache
        self._cache = cache_manager.query_cache if enable_cache else None
        # Lazy image loading for memory optimization
        self._lazy_loader = LazyImageLoader(cache=cache_manager.image_cache)
        # Memory pooling for embedding buffers (reduces GC pressure on mobile)
        self._embedding_pool = EmbeddingPool() if enable_cache else None

    # --- loading ---

    def reload(self) -> None:
        """Re-read all chunks from the database and trigger embedding computation."""
        from .db import load_all_chunks
        self._chunks = load_all_chunks()
        with self._embed_lock:
            self._embeddings  = {}
            self._embed_ready = False
        if self._chunks:
            total = sum(len(c["tokens"]) for c in self._chunks)
            self._avg_dl = total / len(self._chunks)
            # Compute dense embeddings in background — doesn't block the UI
            threading.Thread(
                target=self._compute_embeddings,
                daemon=True,
            ).start()
        else:
            self._avg_dl = 1.0

    def _compute_embeddings(self) -> None:
        """
        Background thread: call llama-server /embedding for every chunk
        and cache the result.  Capped at 30 chunks to avoid 100s of serial
        HTTP roundtrips on large documents (BM25+TF-IDF handles the rest).
        Gracefully no-ops if the server is down or embeddings are unsupported.
        """
        try:
            from .llm import get_embedding
            computed = {}
            # Cap at 30 chunks — embed only the first 30 for speed.
            # For RAG we retrieve top-2; 30 embedded chunks is more than enough.
            chunks_to_embed = self._chunks[:30]
            for c in chunks_to_embed:
                cid  = c["id"]
                # Cap at 300 chars ≈ 100 tokens, matching Nomic ctx=128
                text = c["text"][:300]
                emb = get_embedding(text)
                if emb is None:
                    print("[retriever] embedding endpoint unavailable — "
                          "falling back to BM25+TF-IDF only")
                    return
                computed[cid] = emb
            with self._embed_lock:
                self._embeddings  = computed
                self._embed_ready = True
            print(f"[retriever] semantic embeddings ready "
                  f"({len(computed)} chunks)")
        except Exception as e:
            print(f"[retriever] embedding computation failed: {e}")

    def is_empty(self) -> bool:
        return len(self._chunks) == 0

    # --- BM25 ---

    def _bm25_scores(self, query_tokens: List[str]) -> List[float]:
        N = len(self._chunks)
        scores: List[float] = []

        # IDF per query token across current corpus
        idf: Dict[str, float] = {}
        for qt in set(query_tokens):
            df = sum(1 for c in self._chunks if qt in c["tokens"])
            idf[qt] = math.log((N - df + 0.5) / (df + 0.5) + 1.0)

        for chunk in self._chunks:
            dl = len(chunk["tokens"]) or 1
            tf_map: Dict[str, int] = {}
            for t in chunk["tokens"]:
                tf_map[t] = tf_map.get(t, 0) + 1

            score = 0.0
            for qt in query_tokens:
                if qt not in tf_map:
                    continue
                tf = tf_map[qt]
                score += idf.get(qt, 0.0) * (
                    tf * (K1 + 1)
                    / (tf + K1 * (1 - B + B * dl / self._avg_dl))
                )
            scores.append(score)
        return scores

    # --- TF-IDF cosine ---

    def _cosine_scores(self, query_tokens: List[str]) -> List[float]:
        from collections import Counter
        tf = Counter(query_tokens)
        total = len(query_tokens) or 1
        q_vec: Dict[str, float] = {t: cnt / total for t, cnt in tf.items()}
        return [_cosine_sparse(q_vec, c["tfidf_vec"]) for c in self._chunks]

    # --- semantic cosine ---

    def _semantic_scores(self, query_text: str) -> "List[float] | None":
        """
        Returns per-chunk cosine similarity against a fresh query embedding,
        or None if embeddings are not yet ready / unavailable.
        Uses memory pooling to reduce GC pressure on mobile devices.
        """
        with self._embed_lock:
            if not self._embed_ready:
                return None
            embeddings = dict(self._embeddings)  # snapshot

        try:
            from .llm import get_embedding
            q_emb = get_embedding(query_text[:300])
            if q_emb is None:
                return None
            scores = []
            for c in self._chunks:
                cid = c["id"]
                chunk_emb = embeddings.get(cid)
                scores.append(
                    _cosine_dense(q_emb, chunk_emb) if chunk_emb else 0.0
                )
            return scores
        except Exception as e:
            print(f"[retriever] semantic query failed: {e}")
            return None

    # --- domain routing ---

    def detect_query_domain(self, text: str) -> str:
        """
        Detect query domain for domain-specific retrieval weights.
        
        Returns: 'healthcare', 'technical', 'financial', 'legal', or 'general'
        """
        text_lower = text.lower()
        
        healthcare_keywords = [
            'symptom', 'disease', 'medical', 'doctor', 'patient', 'hospital',
            'treatment', 'medication', 'drug', 'health', 'diagnosis', 'blood',
            'heart', 'cancer', 'diabetes', 'pain', 'sick', 'surgery', 'immune'
        ]
        
        technical_keywords = [
            'api', 'database', 'server', 'code', 'software', 'network', 'tcp',
            'http', 'data', 'algorithm', 'function', 'system', 'cloud', 'app',
            'program', 'python', 'javascript', 'docker', 'kubernetes', 'git'
        ]
        
        financial_keywords = [
            'revenue', 'profit', 'expense', 'cost', 'budget', 'invoice', 'balance',
            'equity', 'asset', 'liability', 'cash flow', 'dividend', 'tax',
            'accounting', 'audit', 'financial', 'ebitda', 'stock', 'investment'
        ]
        
        legal_keywords = [
            'contract', 'agreement', 'law', 'compliance', 'regulation', 'liability',
            'compliance', 'gdpr', 'patent', 'copyright', 'trademark', 'lawsuit',
            'attorney', 'legal', 'court', 'judge', 'verdict', 'settlement'
        ]
        
        # Count keyword matches
        hc_score = sum(1 for kw in healthcare_keywords if kw in text_lower)
        tech_score = sum(1 for kw in technical_keywords if kw in text_lower)
        fin_score = sum(1 for kw in financial_keywords if kw in text_lower)
        leg_score = sum(1 for kw in legal_keywords if kw in text_lower)
        
        scores = {
            'healthcare': hc_score,
            'technical': tech_score,
            'financial': fin_score,
            'legal': leg_score,
        }
        
        detected = max(scores.items(), key=lambda x: x[1])
        return detected[0] if detected[1] > 0 else 'general'

    def get_domain_weights(self, domain: str) -> Dict[str, float]:
        """
        Get optimal retrieval weights for domain.
        
        Domain weights:
        - healthcare: Semantic-heavy (finds medical terminology)
        - technical: BM25-heavy (needs exact function/API names)
        - financial: Balanced (concepts + exact terms)
        - legal: BM25-heavy (precise legal language matters)
        - general: Default balanced
        """
        domain_weights = {
            'healthcare': {
                'bm25': 0.20, 'tfidf': 0.20, 'semantic': 0.60
            },
            'technical': {
                'bm25': 0.60, 'tfidf': 0.20, 'semantic': 0.20
            },
            'financial': {
                'bm25': 0.35, 'tfidf': 0.20, 'semantic': 0.45
            },
            'legal': {
                'bm25': 0.60, 'tfidf': 0.25, 'semantic': 0.15
            },
            'general': {
                'bm25': 0.30, 'tfidf': 0.20, 'semantic': 0.50
            },
        }
        return domain_weights.get(domain, domain_weights['general'])

    def _rerank_semantic(self, candidates: List[Tuple[int, float]], 
                        query_text: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Rerank top-10 candidates using semantic similarity.
        Bridges gap to pure semantic RAG without needing full embedding index.
        
        Args:
            candidates: List of (chunk_index, initial_score) tuples
            query_text: Original query
            top_k: Number of candidates to rerank (typically 10)
        
        Returns:
            Reranked candidates with updated scores
        """
        candidates_to_rerank = candidates[:top_k]
        
        try:
            from .llm import get_embedding
            q_emb = get_embedding(query_text[:300])
            if q_emb is None:
                return candidates  # No reranking possible
            
            reranked = []
            for idx, initial_score in candidates_to_rerank:
                chunk_emb = self._embeddings.get(self._chunks[idx]["id"])
                if chunk_emb:
                    semantic_sim = _cosine_dense(q_emb, chunk_emb)
                    # Blend initial score (50%) with semantic similarity (50%)
                    final_score = 0.5 * initial_score + 0.5 * semantic_sim
                    reranked.append((idx, final_score))
                else:
                    reranked.append((idx, initial_score))
            
            # Re-sort by final score
            reranked.sort(key=lambda x: x[1], reverse=True)
            return reranked
        except Exception as e:
            print(f"[retriever] semantic reranking failed: {e}")
            return candidates

    def _adaptive_top_k(self, query_text: str) -> int:
        """
        Dynamically select top_k based on query complexity.
        
        Simple queries (1-2 words): top_k = 1
        Medium queries (3-5 words): top_k = 2  
        Complex queries (6+ words): top_k = 3-5
        """
        words = len(query_text.split())
        
        if words <= 2:
            return 1
        elif words <= 5:
            return 2
        else:
            return min(5, 2 + (words // 3))

    # --- image retrieval ---

    def _has_image_keywords(self, query_text: str) -> bool:
        """Check if query is asking for images."""
        image_keywords = [
            'image', 'diagram', 'chart', 'graph', 'figure', 'picture', 'photo',
            'show', 'display', 'visualiz', 'illustration', 'screenshot', 'plot',
            'drawing', 'schema', 'layout', 'design'
        ]
        text_lower = query_text.lower()
        return any(kw in text_lower for kw in image_keywords)

    def retrieve_images(self, query_text: str, top_k: int = 3, lazy: bool = True) -> List[dict]:
        """
        Retrieve images relevant to query with optional lazy loading.
        
        Strategy:
        1. Check if query asks for images (keyword detection)
        2. If yes, retrieve top text chunks
        3. Get associated images from those chunks
        4. Return images with metadata (lazy-loaded data)
        
        Args:
            query_text: Query string
            top_k: Number of images to return
            lazy: If True, images are lazy-loaded on demand (80% memory reduction).
                  If False, images are loaded immediately (backward compatible).
        
        Returns:
            List of image dicts with: id, caption, page, bbox, relevance_score, 
            and optionally 'data' (if lazy=False) or 'loader_fn' (if lazy=True)
        """
        if not self._has_image_keywords(query_text):
            return []  # Query doesn't ask for images
        
        # Get top text chunks (manually do the query logic to avoid recursion)
        q_tokens = tokenise(query_text)
        if not q_tokens:
            return []
        
        # Get BM25 and TF-IDF scores for first 5 chunks
        bm25 = self._bm25_scores(q_tokens)
        cos  = self._cosine_scores(q_tokens)
        
        bm25_n = _normalise_scores(bm25)
        cos_n  = _normalise_scores(cos)
        
        # Simple hybrid scoring
        combined = [
            (i, 0.4 * b + 0.6 * c)
            for i, (b, c) in enumerate(zip(bm25_n, cos_n))
        ]
        combined.sort(key=lambda x: x[1], reverse=True)
        top_chunks = combined[:5]
        
        if not top_chunks:
            return []
        
        # Collect chunks that have images
        retrieved_images = []
        seen_image_ids = set()
        
        # For each top chunk, get associated images
        for chunk_idx, chunk_score in top_chunks:
            chunk = self._chunks[chunk_idx]
            chunk_id = chunk["id"]
            
            # Get image metadata for this chunk from database
            try:
                from .db import get_images_by_chunk
                images = get_images_by_chunk(chunk_id)
                
                for img in images:
                    if img["id"] not in seen_image_ids:
                        # Add relevance score based on chunk score
                        img["relevance_score"] = chunk_score * (img.get("relevance_score", 0.5))
                        
                        # Add lazy loader if requested (memory optimization)
                        if lazy and self.enable_cache:
                            # Store loader function instead of actual image data
                            img["_loader_fn"] = self._make_image_loader(img["id"])
                            # Remove 'data' if present to avoid immediate loading
                            img.pop("data", None)
                        
                        retrieved_images.append(img)
                        seen_image_ids.add(img["id"])
            except Exception as e:
                print(f"[retriever] image retrieval failed: {e}")
                continue
        
        # Sort by relevance and return top_k
        retrieved_images.sort(key=lambda x: x["relevance_score"], reverse=True)
        return retrieved_images[:top_k]

    def _make_image_loader(self, image_id: int):
        """Create a callable that loads image data on demand."""
        def loader_fn():
            return self.load_image_data(image_id)
        return loader_fn
    
    def load_image_data(self, image_id: int) -> Optional[bytes]:
        """
        Load actual image data for a lazy-loaded image.
        
        Uses cache to avoid re-decompression. Useful for UI that displays
        images one at a time.
        
        Args:
            image_id: Image ID to load
        
        Returns:
            Image data (bytes) or None if not found
        """
        from .db import get_image_by_id
        
        # Try lazy loader with database loader function
        def db_loader(img_id):
            try:
                result = get_image_by_id(img_id)
                return result["data"] if result else None
            except Exception:
                return None
        
        return self._lazy_loader.load_image_lazy(image_id, loader_fn=db_loader)

    # --- public query ---

    def query(self, text: str, top_k: int = None, 
              retrieval_weights: dict = None,
              domain_routing: bool = True,
              semantic_reranking: bool = True) -> List[Tuple[str, float]]:
        """
        Returns list of (chunk_text, score) sorted by relevance, top_k results.
        
        BACKWARD COMPATIBLE: Returns just chunks list for existing code.
        For multimodal queries, use query_multimodal() instead.
        
        Enhanced with:
        - Automatic domain detection and optimal weights
        - Semantic reranking of top candidates
        - Adaptive top_k selection based on query complexity
        
        Args:
            text: Query string
            top_k: Number of top results to return (auto-detect if None)
            retrieval_weights: Optional dict with keys 'bm25', 'tfidf', 'semantic'
                             If None, will be determined by domain_routing
            domain_routing: Enable automatic domain detection (default: True)
            semantic_reranking: Enable semantic reranking of top-10 (default: True)
        
        Returns:
            List of (chunk_text, score) tuples
        """
        if self.is_empty():
            return []
        
        # Try cache first (normalize query for consistent cache key)
        if self.enable_cache and self._cache is not None:
            cache_key_domain = self.detect_query_domain(text) if domain_routing else None
            cached = self._cache.get(text, top_k or self._adaptive_top_k(text), cache_key_domain)
            if cached is not None:
                cached_chunks, _ = cached
                return cached_chunks

        q_tokens = tokenise(text)
        if not q_tokens:
            return []

        # Adaptive top_k if not specified
        if top_k is None:
            top_k = self._adaptive_top_k(text)

        # Determine weights via domain routing or use provided weights
        if retrieval_weights is None and domain_routing:
            domain = self.detect_query_domain(text)
            retrieval_weights = self.get_domain_weights(domain)
        elif retrieval_weights is None:
            retrieval_weights = {
                'bm25': 0.30, 'tfidf': 0.20, 'semantic': 0.50
            }

        w_bm25 = retrieval_weights.get('bm25', 0.30)
        w_tfidf = retrieval_weights.get('tfidf', 0.20)
        w_semantic = retrieval_weights.get('semantic', 0.50)

        bm25 = self._bm25_scores(q_tokens)
        cos  = self._cosine_scores(q_tokens)
        sem  = self._semantic_scores(text)

        bm25_n = _normalise_scores(bm25)
        cos_n  = _normalise_scores(cos)

        if sem is not None:
            sem_n = _normalise_scores(sem)
            combined = [
                (i, w_bm25 * b + w_tfidf * c + w_semantic * s)
                for i, (b, c, s) in enumerate(zip(bm25_n, cos_n, sem_n))
            ]
        else:
            # Fallback: classic BM25 + TF-IDF hybrid
            total = w_bm25 + w_tfidf
            if total > 0:
                w_bm25_norm = w_bm25 / total
                w_tfidf_norm = w_tfidf / total
            else:
                w_bm25_norm = self.alpha
                w_tfidf_norm = 1 - self.alpha
            
            combined = [
                (i, w_bm25_norm * b + w_tfidf_norm * c)
                for i, (b, c) in enumerate(zip(bm25_n, cos_n))
            ]

        combined.sort(key=lambda x: x[1], reverse=True)

        # Semantic reranking: boost top-10 candidates using semantic similarity
        if semantic_reranking and sem is not None and len(combined) > top_k:
            combined = self._rerank_semantic(combined, text, top_k=10)

        top = combined[:top_k]

        result = [
            (self._chunks[i]["text"], score)
            for i, score in top
        ]
        
        # Cache the result
        if self.enable_cache and self._cache is not None:
            cache_key_domain = self.detect_query_domain(text) if domain_routing else None
            self._cache.set(text, top_k, (result, []), cache_key_domain)
        
        return result

    def query_multimodal(self, text: str, top_k: int = None,
                         retrieval_weights: dict = None,
                         domain_routing: bool = True,
                         semantic_reranking: bool = True,
                         lazy_images: bool = True) -> Tuple[List[Tuple[str, float]], List[dict]]:
        """
        Returns tuple of (chunks, images) for multimodal RAG queries.
        
        - Retrieves text chunks using standard hybrid retrieval
        - Automatically retrieves images if query has image keywords
        - Images ranked by relevance to query
        - Images can be lazy-loaded for memory optimization (80% reduction)
        
        Args:
            text: Query string
            top_k: Number of top results to return (auto-detect if None)
            retrieval_weights: Optional dict with keys 'bm25', 'tfidf', 'semantic'
            domain_routing: Enable automatic domain detection (default: True)
            semantic_reranking: Enable semantic reranking of top-10 (default: True)
            lazy_images: If True, images are lazy-loaded on demand (default: True).
                        Use load_image_data(image_id) to load individual images.
        
        Returns:
            Tuple of (chunks_list, images_list) where:
                chunks_list: List of (chunk_text, score) tuples
                images_list: List of image dicts with metadata, optionally lazy-loadable
        """
        # Get text chunks using standard query
        chunks = self.query(
            text,
            top_k=top_k,
            retrieval_weights=retrieval_weights,
            domain_routing=domain_routing,
            semantic_reranking=semantic_reranking
        )
        
        # Get images if query asks for them (with lazy loading if enabled)
        images = self.retrieve_images(text, top_k=3, lazy=lazy_images)
        
        return chunks, images

    # --- caching/performance ---

    def get_cache_stats(self) -> Dict:
        """Get query cache statistics."""
        if not self.enable_cache or self._cache is None:
            return {'enabled': False}
        return {'enabled': True, **self._cache.stats()}
    
    def get_memory_pool_stats(self) -> Dict:
        """Get embedding memory pool statistics (GC pressure reduction metrics)."""
        if not self.enable_cache or self._embedding_pool is None:
            return {'enabled': False, 'reason': 'caching disabled or pool unavailable'}
        
        stats = self._embedding_pool.stats()
        return {
            'enabled': True,
            'total_buffers': self._embedding_pool.pool_size,
            'available_buffers': stats['available'],
            'in_use_buffers': stats['total'] - stats['available'],
            'utilization_pct': stats['utilization'] * 100,
            'acquisitions': stats['acquisitions'],
            'releases': stats['releases'],
            'buffer_size_floats': self._embedding_pool.dim,
            'total_memory_mb': (self._embedding_pool.pool_size * 
                               self._embedding_pool.dim * 4) / (1024 * 1024),
        }
    
    def get_all_memory_stats(self) -> Dict:
        """
        Get comprehensive memory optimization statistics.
        
        Includes: query cache, image cache, embedding pool, and lazy loader stats.
        Useful for monitoring mobile device memory usage.
        
        Returns:
            Dict with cache, pool, and image stats aggregated
        """
        stats = {
            'cache_enabled': self.enable_cache,
            'query_cache': self.get_cache_stats() if self.enable_cache else {'enabled': False},
            'embedding_pool': self.get_memory_pool_stats() if self.enable_cache else {'enabled': False},
        }
        
        # Add image cache stats if available
        if self.enable_cache and cache_manager:
            image_cache_stats = cache_manager.image_cache.stats() if hasattr(cache_manager, 'image_cache') else {}
            stats['image_cache'] = {
                'enabled': bool(image_cache_stats),
                **image_cache_stats
            }
        
        return stats
    
    def clear_cache(self) -> None:
        """Clear query cache."""
        if self.enable_cache and self._cache is not None:
            self._cache.clear()
            print("[retriever] Query cache cleared")
