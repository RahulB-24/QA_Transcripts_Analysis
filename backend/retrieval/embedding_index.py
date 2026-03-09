"""
Embedding Index Module
=======================
Encodes meeting utterances using ``sentence-transformers/all-MiniLM-L6-v2``,
builds a FAISS index, and maintains an ID → metadata mapping for retrieval.
"""

import pickle
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from preprocessing.conversation_builder import Conversation

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_STORAGE_DIR = _BACKEND_ROOT / "storage"
_INDEX_PATH = _STORAGE_DIR / "embeddings.index"
_META_PATH = _STORAGE_DIR / "embedding_metadata.pkl"

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Module-level cache for the encoder
_encoder: SentenceTransformer | None = None


def _get_encoder() -> SentenceTransformer:
    """Return a cached SentenceTransformer encoder."""
    global _encoder
    if _encoder is None:
        print("[EmbeddingIndex] Loading sentence-transformer model …")
        _encoder = SentenceTransformer(_MODEL_NAME)
    return _encoder


# ── Metadata entry stored alongside each embedding ─────────────────────
EmbeddingMeta = dict[str, Any]  # meeting_id, speaker, text, start, end


def build_index(
    conversations: list[Conversation],
    meeting_id: str | None = None,
    persist: bool = True,
) -> tuple[faiss.IndexFlatIP, list[EmbeddingMeta]]:
    """Build a FAISS inner-product index from utterance embeddings.

    Parameters
    ----------
    conversations : list[Conversation]
        All structured conversation objects.
    meeting_id : str, optional
        If provided, index only utterances from this meeting. When *None*,
        index all meetings.
    persist : bool
        If *True*, write index and metadata to ``storage/``.

    Returns
    -------
    tuple[faiss.IndexFlatIP, list[EmbeddingMeta]]
        The FAISS index and the corresponding metadata list (same order as
        the index vectors).
    """
    encoder = _get_encoder()
    texts: list[str] = []
    metadata: list[EmbeddingMeta] = []

    for conv in conversations:
        if meeting_id is not None and conv["meeting_id"] != meeting_id:
            continue
        for utt in conv["utterances"]:
            texts.append(utt["text"])
            metadata.append(
                {
                    "meeting_id": conv["meeting_id"],
                    "speaker": utt["speaker"],
                    "text": utt["text"],
                    "start": utt["start"],
                    "end": utt["end"],
                }
            )

    if not texts:
        raise ValueError("No utterances to index.")

    print(f"[EmbeddingIndex] Encoding {len(texts)} utterances …")
    embeddings = encoder.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype=np.float32)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner product (cosine on normalised vecs)
    index.add(embeddings)

    if persist:
        _STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(_INDEX_PATH))
        with open(_META_PATH, "wb") as fh:
            pickle.dump(metadata, fh, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"[EmbeddingIndex] Saved index ({index.ntotal} vectors) → {_INDEX_PATH}")

    return index, metadata


def load_index() -> tuple[faiss.IndexFlatIP, list[EmbeddingMeta]] | None:
    """Load previously persisted FAISS index and metadata.

    Returns
    -------
    tuple or None
        ``(index, metadata)`` if cache exists, else *None*.
    """
    if _INDEX_PATH.exists() and _META_PATH.exists():
        index = faiss.read_index(str(_INDEX_PATH))
        with open(_META_PATH, "rb") as fh:
            metadata = pickle.load(fh)
        print(f"[EmbeddingIndex] Loaded index with {index.ntotal} vectors")
        return index, metadata
    return None


def encode_query(query: str) -> np.ndarray:
    """Encode a single query string into a normalised embedding vector.

    Parameters
    ----------
    query : str
        The user's question text.

    Returns
    -------
    np.ndarray
        1-D float32 vector suitable for FAISS search.
    """
    encoder = _get_encoder()
    vec = encoder.encode([query], normalize_embeddings=True)
    return np.array(vec, dtype=np.float32)
