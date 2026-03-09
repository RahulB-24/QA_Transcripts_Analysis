"""
Dataset Loader Module
=====================
Loads the AMI meeting corpus from Hugging Face using **streaming mode**
to avoid downloading the full ~10 GB of audio-embedded parquet files.
Only the text-based columns are extracted and persisted locally.
"""

import pickle
from pathlib import Path
from typing import Optional

import pandas as pd
from datasets import load_dataset
from tqdm import tqdm

# Resolve paths relative to the backend root
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_STORAGE_DIR = _BACKEND_ROOT / "storage"
_CACHE_PATH = _STORAGE_DIR / "cached_dataset.pkl"

# Fields we retain from the raw dataset
_KEEP_FIELDS = ["meeting_id", "speaker_id", "text", "begin_time", "end_time"]


def _ensure_storage_dir() -> None:
    """Create the storage directory if it does not exist."""
    _STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def load_ami_dataset(
    subset: str = "ihm",
    split: str = "train",
    force_reload: bool = False,
    max_rows: int = 20000,
) -> pd.DataFrame:
    """Load the AMI meeting dataset and return a cleaned DataFrame.

    Uses **streaming mode** to avoid downloading the full dataset
    (which includes large audio blobs). Only text-based fields are
    extracted, making the download fast and lightweight.

    Parameters
    ----------
    subset : str
        AMI subset identifier (default ``"ihm"``).
    split : str
        Dataset split to load (default ``"train"``).
    force_reload : bool
        When *True*, re-download and re-process even if a cached copy exists.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: ``meeting_id``, ``speaker_id``, ``text``,
        ``begin_time``, ``end_time``.
    """
    if not force_reload and _CACHE_PATH.exists():
        print(f"[DatasetLoader] Loading cached dataset from {_CACHE_PATH}")
        with open(_CACHE_PATH, "rb") as fh:
            return pickle.load(fh)

    print("[DatasetLoader] Streaming AMI dataset from Hugging Face (text only) …")
    ds_stream = load_dataset(
        "edinburghcstr/ami",
        subset,
        split=split,
        streaming=True,
        trust_remote_code=True,
    )

    # Drop the audio column to avoid needing soundfile/librosa
    ds_stream = ds_stream.select_columns(_KEEP_FIELDS)

    # Stream through and extract only the columns we need
    rows: list[dict] = []
    for example in tqdm(ds_stream, desc="[DatasetLoader] Reading rows"):
        row = {}
        for field in _KEEP_FIELDS:
            if field in example:
                row[field] = example[field]
        if row.get("text"):
            rows.append(row)
        if max_rows and len(rows) >= max_rows:
            print(f"[DatasetLoader] Reached {max_rows} row limit — stopping early")
            break

    print(f"[DatasetLoader] Collected {len(rows)} rows from stream")
    df = pd.DataFrame(rows)

    # Basic cleaning
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"].str.len() > 0].reset_index(drop=True)

    # Persist
    _ensure_storage_dir()
    with open(_CACHE_PATH, "wb") as fh:
        pickle.dump(df, fh, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"[DatasetLoader] Cached {len(df)} rows → {_CACHE_PATH}")

    return df


def get_meeting_ids(df: Optional[pd.DataFrame] = None) -> list[str]:
    """Return sorted list of unique meeting IDs.

    Parameters
    ----------
    df : pd.DataFrame, optional
        Pre-loaded DataFrame. If *None*, loads from cache or downloads.

    Returns
    -------
    list[str]
        Sorted meeting identifiers.
    """
    if df is None:
        df = load_ami_dataset()
    return sorted(df["meeting_id"].unique().tolist())
