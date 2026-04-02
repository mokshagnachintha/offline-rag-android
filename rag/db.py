"""
db.py — SQLite-backed document and chunk store.
Stores document metadata and text chunks with their TF-IDF vectors.
No external vector DB needed; everything lives in a single SQLite file.
"""
import sqlite3
import json
import os
import pickle
from pathlib import Path
from typing import List, Tuple, Optional


DB_PATH = os.path.join(
    os.environ.get("ANDROID_PRIVATE", os.path.expanduser("~")),
    "ragapp.db",
)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")   # faster concurrent writes
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")    # enable CASCADE deletes
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                name      TEXT NOT NULL,
                path      TEXT NOT NULL UNIQUE,
                added_at  TEXT DEFAULT (datetime('now')),
                num_chunks INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS chunks (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id    INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_idx INTEGER NOT NULL,
                text      TEXT NOT NULL,
                tokens    TEXT,          -- JSON list of lowercase tokens for BM25
                tfidf_vec BLOB           -- pickled dict {term: tf_idf_score}
            );

            CREATE TABLE IF NOT EXISTS images (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id    INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                image_idx INTEGER NOT NULL,
                data      BLOB NOT NULL,        -- JPEG image data (compressed)
                caption   TEXT,                 -- OCR/inferred caption
                page      INTEGER,              -- page number (for PDFs)
                bbox      TEXT,                 -- JSON {x, y, width, height} on page
                ocr_text  TEXT,                 -- extracted text from image
                embedding BLOB,                 -- pickled CLIP embedding vector
                added_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS chunk_images (
                chunk_id  INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
                image_id  INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
                relevance_score REAL DEFAULT 0.5,
                PRIMARY KEY (chunk_id, image_id)
            );

            CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);
            CREATE INDEX IF NOT EXISTS idx_images_doc ON images(doc_id);
            CREATE INDEX IF NOT EXISTS idx_chunk_images_chunk ON chunk_images(chunk_id);
            CREATE INDEX IF NOT EXISTS idx_chunk_images_image ON chunk_images(image_id);
            """
        )


# ---------- document helpers ----------

def insert_document(name: str, path: str) -> int:
    with get_conn() as conn:
        # Check if this path already exists — if so, delete its old chunks
        # so re-uploading the same file doesn't accumulate duplicates.
        existing = conn.execute(
            "SELECT id FROM documents WHERE path=?", (path,)
        ).fetchone()
        if existing:
            doc_id = existing[0]
            conn.execute("DELETE FROM chunks WHERE doc_id=?", (doc_id,))
            return doc_id
        cur = conn.execute(
            "INSERT INTO documents(name, path) VALUES (?, ?)", (name, path)
        )
        return cur.lastrowid


def update_doc_chunk_count(doc_id: int, count: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE documents SET num_chunks=? WHERE id=?", (count, doc_id)
        )


def list_documents() -> List[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name, path, added_at, num_chunks FROM documents ORDER BY added_at DESC"
        ).fetchall()
    return [
        {"id": r[0], "name": r[1], "path": r[2], "added_at": r[3], "num_chunks": r[4]}
        for r in rows
    ]


def delete_document(doc_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))


# ---------- chunk helpers ----------

def insert_chunks(doc_id: int, chunks: List[dict]) -> None:
    """
    chunks: list of dicts with keys:
        chunk_idx, text, tokens (list[str]), tfidf_vec (dict)
    """
    rows = [
        (
            doc_id,
            c["chunk_idx"],
            c["text"],
            json.dumps(c["tokens"]),
            pickle.dumps(c["tfidf_vec"]),
        )
        for c in chunks
    ]
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO chunks(doc_id, chunk_idx, text, tokens, tfidf_vec) "
            "VALUES (?,?,?,?,?)",
            rows,
        )


def load_all_chunks() -> List[dict]:
    """Load every chunk (text + tokens + tfidf_vec) for the retriever."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, doc_id, chunk_idx, text, tokens, tfidf_vec FROM chunks"
        ).fetchall()
    result = []
    for r in rows:
        result.append(
            {
                "id": r[0],
                "doc_id": r[1],
                "chunk_idx": r[2],
                "text": r[3],
                "tokens": json.loads(r[4]) if r[4] else [],
                "tfidf_vec": pickle.loads(r[5]) if r[5] else {},
            }
        )
    return result


def get_chunk_texts_by_ids(ids: List[int]) -> List[str]:
    placeholders = ",".join("?" * len(ids))
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT id, text FROM chunks WHERE id IN ({placeholders})", ids
        ).fetchall()
    id_to_text = {r[0]: r[1] for r in rows}
    return [id_to_text[i] for i in ids if i in id_to_text]


# ---------- image helpers ----------

def insert_images(doc_id: int, images: List[dict]) -> List[int]:
    """
    images: list of dicts with keys:
        image_idx, data (bytes), caption (str), page (int), bbox (dict),
        ocr_text (str), embedding (list[float])
    Returns: list of inserted image IDs.
    """
    image_ids = []
    for img in images:
        # Prepare values, using None for optional fields
        bbox_json = json.dumps(img.get("bbox", {})) if img.get("bbox") else None
        embedding_blob = pickle.dumps(img["embedding"]) if img.get("embedding") else None
        
        row = (
            doc_id,
            img["image_idx"],
            img["data"],
            img.get("caption"),
            img.get("page"),
            bbox_json,
            img.get("ocr_text"),
            embedding_blob,
        )
        
        with get_conn() as conn:
            cur = conn.execute(
                """INSERT INTO images(doc_id, image_idx, data, caption, page, bbox, ocr_text, embedding)
                   VALUES (?,?,?,?,?,?,?,?)""",
                row,
            )
            image_ids.append(cur.lastrowid)
    return image_ids


def associate_chunks_images(chunk_image_pairs: List[Tuple[int, int, float]]) -> None:
    """
    chunk_image_pairs: list of (chunk_id, image_id, relevance_score) tuples.
    Associates chunks with images (for retrieval).
    """
    with get_conn() as conn:
        conn.executemany(
            """INSERT OR REPLACE INTO chunk_images(chunk_id, image_id, relevance_score)
               VALUES (?,?,?)""",
            chunk_image_pairs,
        )


def get_images_by_doc(doc_id: int) -> List[dict]:
    """Load all images for a document."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT id, image_idx, data, caption, page, bbox, ocr_text, embedding
               FROM images WHERE doc_id=? ORDER BY image_idx""",
            (doc_id,),
        ).fetchall()
    result = []
    for r in rows:
        result.append(
            {
                "id": r[0],
                "image_idx": r[1],
                "data": r[2],
                "caption": r[3],
                "page": r[4],
                "bbox": json.loads(r[5]) if r[5] else {},
                "ocr_text": r[6],
                "embedding": pickle.loads(r[7]) if r[7] else [],
            }
        )
    return result


def get_images_by_chunk(chunk_id: int) -> List[dict]:
    """Get all images associated with a chunk, ranked by relevance."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT i.id, i.image_idx, i.data, i.caption, i.page, i.bbox, i.ocr_text, i.embedding, ci.relevance_score
               FROM images i
               JOIN chunk_images ci ON i.id = ci.image_id
               WHERE ci.chunk_id = ?
               ORDER BY ci.relevance_score DESC""",
            (chunk_id,),
        ).fetchall()
    result = []
    for r in rows:
        result.append(
            {
                "id": r[0],
                "image_idx": r[1],
                "data": r[2],
                "caption": r[3],
                "page": r[4],
                "bbox": json.loads(r[5]) if r[5] else {},
                "ocr_text": r[6],
                "embedding": pickle.loads(r[7]) if r[7] else [],
                "relevance_score": r[8],
            }
        )
    return result


def get_image_by_id(image_id: int) -> dict:
    """Get a single image by ID for lazy loading."""
    with get_conn() as conn:
        row = conn.execute(
            """SELECT id, image_idx, data, caption, page, bbox, ocr_text, embedding
               FROM images
               WHERE id = ?""",
            (image_id,),
        ).fetchone()
    
    if not row:
        return None
    
    return {
        "id": row[0],
        "image_idx": row[1],
        "data": row[2],
        "caption": row[3],
        "page": row[4],
        "bbox": json.loads(row[5]) if row[5] else {},
        "ocr_text": row[6],
        "embedding": pickle.loads(row[7]) if row[7] else [],
    }
