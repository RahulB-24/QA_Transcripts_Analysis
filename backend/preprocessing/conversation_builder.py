"""
Conversation Builder Module
============================
Groups raw utterance rows by meeting, sorts them chronologically, and
produces structured conversation objects suitable for downstream analysis.
"""

from typing import Any

import pandas as pd


# ── Type alias for a single conversation ────────────────────────────────
Utterance = dict[str, Any]          # speaker, text, start, end
Conversation = dict[str, Any]       # meeting_id, utterances


def build_conversations(df: pd.DataFrame) -> list[Conversation]:
    """Group utterances by meeting and build structured conversation objects.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with columns ``meeting_id``, ``speaker_id``, ``text``,
        ``begin_time``, ``end_time``.

    Returns
    -------
    list[Conversation]
        Each element is a dict::

            {
                "meeting_id": str,
                "utterances": [
                    {
                        "speaker": str,
                        "text": str,
                        "start": float,
                        "end": float,
                    },
                    ...
                ]
            }

        Utterances within each meeting are sorted by ``begin_time``.
    """
    conversations: list[Conversation] = []

    grouped = df.groupby("meeting_id", sort=True)

    for meeting_id, group in grouped:
        # Sort chronologically
        group_sorted = group.sort_values("begin_time").reset_index(drop=True)

        utterances: list[Utterance] = []
        for _, row in group_sorted.iterrows():
            utterances.append(
                {
                    "speaker": str(row["speaker_id"]),
                    "text": str(row["text"]),
                    "start": float(row["begin_time"]),
                    "end": float(row["end_time"]),
                }
            )

        conversations.append(
            {
                "meeting_id": str(meeting_id),
                "utterances": utterances,
            }
        )

    print(f"[ConversationBuilder] Built {len(conversations)} conversations")
    return conversations


def get_conversation_by_id(
    conversations: list[Conversation],
    meeting_id: str,
) -> Conversation | None:
    """Look up a single conversation by its meeting ID.

    Parameters
    ----------
    conversations : list[Conversation]
        Full list of conversation objects.
    meeting_id : str
        Target meeting identifier.

    Returns
    -------
    Conversation | None
        The matching conversation, or *None* if not found.
    """
    for conv in conversations:
        if conv["meeting_id"] == meeting_id:
            return conv
    return None
