"""
Retriever Module
=================
Given a user question, retrieves the most relevant utterances from the
FAISS index and re-ranks them using a combined score of semantic
similarity and speaker trust.
"""

from typing import Any

import faiss
import numpy as np

from retrieval.embedding_index import EmbeddingMeta, encode_query


# ── Result type ─────────────────────────────────────────────────────────
RetrievalResult = dict[str, Any]
# Keys: speaker, text, start, end, meeting_id, similarity, trust_score, final_score


def retrieve(
    question: str,
    index: faiss.IndexFlatIP,
    metadata: list[EmbeddingMeta],
    trust_scores: dict[str, float],
    meeting_id: str | None = None,
    top_k: int = 10,
) -> list[RetrievalResult]:
    """Retrieve and trust-weight the most relevant utterances.

    Parameters
    ----------
    question : str
        The user's question.
    index : faiss.IndexFlatIP
        Pre-built FAISS index.
    metadata : list[EmbeddingMeta]
        Metadata list aligned with the index vectors.
    trust_scores : dict[str, float]
        ``speaker_id`` → trust score for the target meeting.
    meeting_id : str, optional
        If provided, filter results to this meeting only.
    top_k : int
        Number of results to return (default 10).

    Returns
    -------
    list[RetrievalResult]
        Sorted by ``final_score`` descending.  Each entry contains::

            {
                "speaker": str,
                "text": str,
                "start": float,
                "end": float,
                "meeting_id": str,
                "similarity": float,
                "trust_score": float,
                "final_score": float,
            }
    """
    query_vec = encode_query(question)

    # When filtering by meeting_id, search the entire index since only
    # a fraction of vectors belong to the target meeting.
    if meeting_id is not None:
        search_k = index.ntotal
    else:
        search_k = min(top_k * 20, index.ntotal)
    distances, indices = index.search(query_vec, search_k)

    results: list[RetrievalResult] = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0:
            continue
        meta = metadata[idx]

        # Filter by meeting if necessary
        if meeting_id is not None and meta["meeting_id"] != meeting_id:
            continue

        similarity = float(dist)
        speaker = meta["speaker"]
        trust = trust_scores.get(speaker, 0.5)  # default neutral trust
        final_score = similarity * trust

        results.append(
            {
                "speaker": speaker,
                "text": meta["text"],
                "start": meta["start"],
                "end": meta["end"],
                "meeting_id": meta["meeting_id"],
                "similarity": round(similarity, 4),
                "trust_score": round(trust, 4),
                "final_score": round(final_score, 4),
            }
        )

    # Sort by final score, take top-k
    results.sort(key=lambda r: r["final_score"], reverse=True)
    return results[:top_k]
