"""
Trust Scorer Module
====================
Combines speaker behavioural features and contradiction statistics into
a single trust score per speaker per meeting, normalised to [0, 1].

Weighted formula
~~~~~~~~~~~~~~~~
::

    trust_score = (consistency  × 0.35)
               + (confidence   × 0.25)
               + (low_contra   × 0.25)
               + (stability    × 0.15)
"""

import pickle
from pathlib import Path
from typing import Any

import numpy as np

from trust_model.speaker_features import SpeakerFeatures

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_STORAGE_DIR = _BACKEND_ROOT / "storage"
_TRUST_CACHE = _STORAGE_DIR / "trust_scores.pkl"

# ── Weight configuration ────────────────────────────────────────────────
W_CONSISTENCY: float = 0.35
W_CONFIDENCE: float = 0.25
W_LOW_CONTRADICTION: float = 0.25
W_STABILITY: float = 0.15


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp *value* to the range [lo, hi]."""
    return max(lo, min(hi, value))


def compute_trust_scores(
    speaker_features: dict[str, SpeakerFeatures],
    contradiction_stats: dict[str, dict[str, Any]],
) -> dict[str, float]:
    """Compute a trust score for every speaker in a single meeting.

    Parameters
    ----------
    speaker_features : dict[str, SpeakerFeatures]
        ``speaker_id`` → feature dict (from :mod:`trust_model.speaker_features`).
    contradiction_stats : dict[str, dict[str, Any]]
        ``speaker_id`` → contradiction dict (from
        :mod:`trust_model.contradiction_detector`).

    Returns
    -------
    dict[str, float]
        ``speaker_id`` → trust score in [0, 1].
    """
    scores: dict[str, float] = {}

    for spk, feats in speaker_features.items():
        # ── Consistency (inverse of correction frequency) ───────────
        corrections_per_stmt = (
            feats["correction_events"] / feats["total_statements"]
            if feats["total_statements"] > 0
            else 0.0
        )
        consistency = _clamp(1.0 - corrections_per_stmt)

        # ── Confidence (lexical confidence minus hesitation penalty) ─
        hesitation_penalty = min(feats["hesitation_frequency"] * 0.15, 0.5)
        confidence = _clamp(feats["lexical_confidence"] - hesitation_penalty)

        # ── Low contradiction score ─────────────────────────────────
        contra = contradiction_stats.get(spk, {})
        contradiction_ratio = contra.get("contradiction_ratio", 0.0)
        low_contradiction = _clamp(1.0 - contradiction_ratio)

        # ── Stability (based on statement count & low interruptions) ─
        stmt_score = _clamp(min(feats["total_statements"] / 20.0, 1.0))
        interrupt_penalty = min(feats["interruptions"] * 0.05, 0.5)
        stability = _clamp(stmt_score - interrupt_penalty)

        trust = (
            W_CONSISTENCY * consistency
            + W_CONFIDENCE * confidence
            + W_LOW_CONTRADICTION * low_contradiction
            + W_STABILITY * stability
        )
        scores[spk] = round(_clamp(trust), 4)

    return scores


def compute_all_trust_scores(
    all_features: dict[str, dict[str, SpeakerFeatures]],
    all_contradictions: dict[str, dict[str, dict[str, Any]]],
    persist: bool = True,
) -> dict[str, dict[str, float]]:
    """Compute and optionally persist trust scores for all meetings.

    Parameters
    ----------
    all_features : dict
        ``meeting_id`` → ``speaker_id`` → feature dict.
    all_contradictions : dict
        ``meeting_id`` → ``speaker_id`` → contradiction stats.
    persist : bool
        If *True*, write scores to ``storage/trust_scores.pkl``.

    Returns
    -------
    dict[str, dict[str, float]]
        ``meeting_id`` → ``speaker_id`` → trust score.
    """
    all_scores: dict[str, dict[str, float]] = {}

    for mid, feats in all_features.items():
        contras = all_contradictions.get(mid, {})
        all_scores[mid] = compute_trust_scores(feats, contras)

    if persist:
        _STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        with open(_TRUST_CACHE, "wb") as fh:
            pickle.dump(all_scores, fh, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"[TrustScorer] Persisted scores for {len(all_scores)} meetings → {_TRUST_CACHE}")

    return all_scores


def load_trust_scores() -> dict[str, dict[str, float]] | None:
    """Load trust scores from cache if available.

    Returns
    -------
    dict or None
        Cached trust scores, or *None* if no cache exists.
    """
    if _TRUST_CACHE.exists():
        with open(_TRUST_CACHE, "rb") as fh:
            return pickle.load(fh)
    return None
