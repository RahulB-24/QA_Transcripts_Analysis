"""
Speaker Feature Extraction Module
==================================
Computes behavioural features for every speaker in each meeting. These
features feed into the downstream trust-scoring model.
"""

import re
from typing import Any

from preprocessing.conversation_builder import Conversation

# ── Hesitation markers (filler words / sounds) ──────────────────────────
_HESITATION_PATTERN = re.compile(
    r"\b(uh|um|uhm|hmm|er|erm|ah|like|you know|I mean|sort of|kind of)\b",
    re.IGNORECASE,
)

# ── Low-confidence lexical cues ─────────────────────────────────────────
_LOW_CONFIDENCE_PATTERN = re.compile(
    r"\b(maybe|perhaps|possibly|I think|I guess|not sure|I don't know|probably|might)\b",
    re.IGNORECASE,
)

# ── Correction / self-repair cues ───────────────────────────────────────
_CORRECTION_PATTERN = re.compile(
    r"\b(I mean|sorry|correction|actually|wait|no no|let me rephrase)\b",
    re.IGNORECASE,
)


# ── Public dataclass-style dict for per-speaker features ────────────────
SpeakerFeatures = dict[str, Any]


def _count_pattern(text: str, pattern: re.Pattern) -> int:
    """Count non-overlapping matches of *pattern* in *text*."""
    return len(pattern.findall(text))


def _words(text: str) -> list[str]:
    """Tokenise *text* into whitespace-delimited words."""
    return text.split()


def compute_speaker_features(conversation: Conversation) -> dict[str, SpeakerFeatures]:
    """Compute behavioural features for each speaker in a conversation.

    Parameters
    ----------
    conversation : Conversation
        A structured conversation dict produced by
        :func:`preprocessing.conversation_builder.build_conversations`.

    Returns
    -------
    dict[str, SpeakerFeatures]
        Mapping from ``speaker_id`` → feature dict with keys:

        * ``total_statements``       – number of utterances
        * ``average_sentence_length`` – mean word count per utterance
        * ``hesitation_frequency``    – hesitation markers per utterance
        * ``lexical_confidence``      – 1 − (low-confidence markers / words)
        * ``interruptions``           – estimated interruptions (overlap count)
        * ``correction_events``       – self-repair / correction markers
    """
    utterances = conversation["utterances"]
    if not utterances:
        return {}

    # ── Accumulate per-speaker raw stats ────────────────────────────────
    raw: dict[str, dict[str, Any]] = {}
    for utt in utterances:
        spk = utt["speaker"]
        if spk not in raw:
            raw[spk] = {
                "total_statements": 0,
                "total_words": 0,
                "hesitation_count": 0,
                "low_confidence_count": 0,
                "correction_count": 0,
                "end_times": [],
                "start_times": [],
            }
        r = raw[spk]
        words = _words(utt["text"])
        r["total_statements"] += 1
        r["total_words"] += len(words)
        r["hesitation_count"] += _count_pattern(utt["text"], _HESITATION_PATTERN)
        r["low_confidence_count"] += _count_pattern(utt["text"], _LOW_CONFIDENCE_PATTERN)
        r["correction_count"] += _count_pattern(utt["text"], _CORRECTION_PATTERN)
        r["end_times"].append(utt["end"])
        r["start_times"].append(utt["start"])

    # ── Detect interruptions (start before prior speaker ends) ──────────
    sorted_utts = sorted(utterances, key=lambda u: u["start"])
    interruption_counts: dict[str, int] = {spk: 0 for spk in raw}
    for i in range(1, len(sorted_utts)):
        prev = sorted_utts[i - 1]
        curr = sorted_utts[i]
        if curr["speaker"] != prev["speaker"] and curr["start"] < prev["end"]:
            interruption_counts[curr["speaker"]] += 1

    # ── Compute final feature vectors ───────────────────────────────────
    features: dict[str, SpeakerFeatures] = {}
    for spk, r in raw.items():
        n = r["total_statements"]
        w = r["total_words"]
        features[spk] = {
            "total_statements": n,
            "average_sentence_length": w / n if n else 0.0,
            "hesitation_frequency": r["hesitation_count"] / n if n else 0.0,
            "lexical_confidence": 1.0 - (r["low_confidence_count"] / w if w else 0.0),
            "interruptions": interruption_counts.get(spk, 0),
            "correction_events": r["correction_count"],
        }

    return features


def compute_all_speaker_features(
    conversations: list[Conversation],
) -> dict[str, dict[str, SpeakerFeatures]]:
    """Compute features for every speaker in every meeting.

    Returns
    -------
    dict[str, dict[str, SpeakerFeatures]]
        Mapping ``meeting_id`` → ``speaker_id`` → feature dict.
    """
    all_features: dict[str, dict[str, SpeakerFeatures]] = {}
    for conv in conversations:
        mid = conv["meeting_id"]
        all_features[mid] = compute_speaker_features(conv)
    print(f"[SpeakerFeatures] Computed features for {len(all_features)} meetings")
    return all_features
