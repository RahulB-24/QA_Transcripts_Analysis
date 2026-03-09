"""
Contradiction Detector Module
==============================
Uses a zero-shot NLI model (``facebook/bart-large-mnli``) to compare a
speaker's later statements against their earlier ones and detect
self-contradictions.
"""

from typing import Any

import torch
from transformers import pipeline as hf_pipeline

from preprocessing.conversation_builder import Conversation

# Maximum number of premise–hypothesis pairs to evaluate per speaker
# to keep inference costs manageable on CPU.
_MAX_PAIRS_PER_SPEAKER: int = 50

# NLI contradiction probability threshold
_CONTRADICTION_THRESHOLD: float = 0.5


def _get_nli_pipeline() -> Any:
    """Lazily load the NLI classification pipeline (cached after first call)."""
    if not hasattr(_get_nli_pipeline, "_pipe"):
        print("[ContradictionDetector] Loading NLI model …")
        _get_nli_pipeline._pipe = hf_pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=-1,  # CPU
        )
    return _get_nli_pipeline._pipe


def detect_contradictions(
    conversation: Conversation,
) -> dict[str, dict[str, Any]]:
    """Detect self-contradictions per speaker using NLI inference.

    For each speaker the method compares a later statement (hypothesis)
    against an earlier statement (premise) and records the contradiction
    probability assigned by the model.

    Parameters
    ----------
    conversation : Conversation
        Structured conversation object.

    Returns
    -------
    dict[str, dict[str, Any]]
        Mapping ``speaker_id`` → dict with keys:

        * ``contradiction_count``  – number of detected contradictions
        * ``total_pairs_checked``  – pairs evaluated
        * ``contradiction_ratio``  – ``count / pairs_checked``
    """
    pipe = _get_nli_pipeline()

    # Group utterances by speaker, keeping chronological order
    speaker_utts: dict[str, list[str]] = {}
    for utt in conversation["utterances"]:
        speaker_utts.setdefault(utt["speaker"], []).append(utt["text"])

    results: dict[str, dict[str, Any]] = {}

    for spk, texts in speaker_utts.items():
        if len(texts) < 2:
            results[spk] = {
                "contradiction_count": 0,
                "total_pairs_checked": 0,
                "contradiction_ratio": 0.0,
            }
            continue

        # Build premise–hypothesis pairs (later vs earlier)
        pairs: list[tuple[str, str]] = []
        for j in range(1, len(texts)):
            for i in range(j):
                pairs.append((texts[i], texts[j]))
                if len(pairs) >= _MAX_PAIRS_PER_SPEAKER:
                    break
            if len(pairs) >= _MAX_PAIRS_PER_SPEAKER:
                break

        contradiction_count = 0
        for premise, hypothesis in pairs:
            # Skip very short utterances
            if len(premise.split()) < 3 or len(hypothesis.split()) < 3:
                continue
            try:
                result = pipe(
                    hypothesis,
                    candidate_labels=["entailment", "contradiction", "neutral"],
                    hypothesis_template="{}",
                    multi_label=False,
                )
                label_scores = dict(zip(result["labels"], result["scores"]))
                if label_scores.get("contradiction", 0.0) >= _CONTRADICTION_THRESHOLD:
                    contradiction_count += 1
            except Exception:
                # Gracefully skip problematic pairs
                continue

        total = len(pairs)
        results[spk] = {
            "contradiction_count": contradiction_count,
            "total_pairs_checked": total,
            "contradiction_ratio": contradiction_count / total if total > 0 else 0.0,
        }

    return results


def detect_all_contradictions(
    conversations: list[Conversation],
) -> dict[str, dict[str, dict[str, Any]]]:
    """Run contradiction detection across all meetings.

    Returns
    -------
    dict[str, dict[str, dict[str, Any]]]
        Mapping ``meeting_id`` → ``speaker_id`` → contradiction stats.
    """
    all_results: dict[str, dict[str, dict[str, Any]]] = {}
    for idx, conv in enumerate(conversations):
        mid = conv["meeting_id"]
        print(f"[ContradictionDetector] Processing meeting {idx + 1}/{len(conversations)}: {mid}")
        all_results[mid] = detect_contradictions(conv)
    return all_results
