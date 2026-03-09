"""
Pipeline Module
================
Orchestrates the full processing pipeline: data loading → conversation
building → speaker features → contradiction detection → trust scoring →
embedding index construction.  All heavy computations are cached.
"""

import pickle
import sys
from pathlib import Path
from typing import Any

import faiss

# Make sure backend root is importable
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from data.dataset_loader import load_ami_dataset, get_meeting_ids
from preprocessing.conversation_builder import build_conversations, Conversation
from trust_model.speaker_features import compute_all_speaker_features
from trust_model.contradiction_detector import detect_all_contradictions
from trust_model.trust_scorer import (
    compute_all_trust_scores,
    load_trust_scores,
)
from retrieval.embedding_index import build_index, load_index, EmbeddingMeta
from retrieval.retriever import retrieve, RetrievalResult
from qa.answer_generator import generate_answer

_STORAGE_DIR = _BACKEND_ROOT / "storage"


class QAPipeline:
    """End-to-end question-answering pipeline over meeting transcripts.

    On first instantiation the pipeline runs the full compute graph (dataset
    loading, feature extraction, contradiction detection, trust scoring, and
    FAISS index construction).  Subsequent instantiations load from cache
    unless ``force_rebuild=True``.
    """

    def __init__(self, force_rebuild: bool = False) -> None:
        self._conversations: list[Conversation] = []
        self._trust_scores: dict[str, dict[str, float]] = {}
        self._index: faiss.IndexFlatIP | None = None
        self._metadata: list[EmbeddingMeta] = []

        self._initialise(force_rebuild=force_rebuild)

    # ── Initialisation / caching ────────────────────────────────────────

    def _initialise(self, force_rebuild: bool) -> None:
        """Run or load the full processing pipeline."""
        # 1. Load dataset
        print("━" * 60)
        print("STEP 1/6 — Loading dataset")
        print("━" * 60)
        df = load_ami_dataset(force_reload=force_rebuild)

        # 2. Build conversations
        print("━" * 60)
        print("STEP 2/6 — Building conversations")
        print("━" * 60)
        self._conversations = build_conversations(df)

        # 3. Speaker features
        print("━" * 60)
        print("STEP 3/6 — Computing speaker features")
        print("━" * 60)
        all_features = compute_all_speaker_features(self._conversations)

        # 4. Contradiction detection (expensive — skip if trust cache exists)
        cached_trust = load_trust_scores()
        if cached_trust is not None and not force_rebuild:
            print("━" * 60)
            print("STEP 4/6 — Contradiction detection (using cached trust scores)")
            print("━" * 60)
            self._trust_scores = cached_trust
        else:
            print("━" * 60)
            print("STEP 4/6 — Detecting contradictions (this may take a while) …")
            print("━" * 60)
            all_contradictions = detect_all_contradictions(self._conversations)

            # 5. Trust scores
            print("━" * 60)
            print("STEP 5/6 — Computing trust scores")
            print("━" * 60)
            self._trust_scores = compute_all_trust_scores(
                all_features, all_contradictions, persist=True
            )

        # 6. Embedding index
        cached_index = load_index()
        if cached_index is not None and not force_rebuild:
            print("━" * 60)
            print("STEP 6/6 — Loading cached embedding index")
            print("━" * 60)
            self._index, self._metadata = cached_index
        else:
            print("━" * 60)
            print("STEP 6/6 — Building embedding index")
            print("━" * 60)
            self._index, self._metadata = build_index(
                self._conversations, persist=True
            )

        print("━" * 60)
        print("✓ Pipeline ready")
        print("━" * 60)

    # ── Public API ──────────────────────────────────────────────────────

    def get_meeting_ids(self) -> list[str]:
        """Return sorted list of available meeting IDs."""
        return sorted({c["meeting_id"] for c in self._conversations})

    def ask(
        self,
        meeting_id: str,
        question: str,
        top_k: int = 10,
    ) -> dict[str, Any]:
        """Answer a question about a specific meeting.

        Parameters
        ----------
        meeting_id : str
            Target meeting identifier.
        question : str
            User's natural-language question.
        top_k : int
            Number of evidence segments to retrieve.

        Returns
        -------
        dict[str, Any]
            Response with keys ``answer`` and ``evidence``.
        """
        if self._index is None:
            raise RuntimeError("Embedding index not initialised.")

        trust = self._trust_scores.get(meeting_id, {})

        # Retrieve trust-weighted evidence
        evidence: list[RetrievalResult] = retrieve(
            question=question,
            index=self._index,
            metadata=self._metadata,
            trust_scores=trust,
            meeting_id=meeting_id,
            top_k=top_k,
        )

        if not evidence:
            return {
                "answer": "No relevant evidence found for this question in the selected meeting.",
                "evidence": [],
            }

        # Generate answer
        result = generate_answer(question=question, evidence=evidence)
        return result
