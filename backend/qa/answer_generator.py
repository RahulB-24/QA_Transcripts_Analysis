"""
Answer Generator Module
========================
Uses ``google/flan-t5-base`` to generate grounded answers from retrieved
transcript evidence segments.
"""

from typing import Any

from transformers import T5ForConditionalGeneration, T5Tokenizer

from retrieval.retriever import RetrievalResult

# Module-level model cache
_model: T5ForConditionalGeneration | None = None
_tokenizer: T5Tokenizer | None = None

_MODEL_NAME = "google/flan-t5-base"

# Number of evidence segments to include in the prompt
# (fewer = more room for the model to generate a good answer)
_TOP_K_FOR_PROMPT = 5


def _load_model() -> tuple[T5ForConditionalGeneration, T5Tokenizer]:
    """Lazily load and cache the T5 model and tokenizer."""
    global _model, _tokenizer
    if _model is None or _tokenizer is None:
        print("[AnswerGenerator] Loading flan-t5-base model …")
        _tokenizer = T5Tokenizer.from_pretrained(_MODEL_NAME)
        _model = T5ForConditionalGeneration.from_pretrained(_MODEL_NAME)
    return _model, _tokenizer


def _normalize_text(text: str) -> str:
    """Convert ALL CAPS transcript text to readable sentence case.

    The AMI corpus stores text in uppercase, which hurts model quality.
    """
    if text.isupper():
        # Capitalize only the first character of each sentence
        text = text.capitalize()
    return text


def _format_timestamp(seconds: float) -> str:
    """Format seconds into mm:ss."""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}:{s:02d}"


def _build_prompt(question: str, evidence: list[RetrievalResult]) -> str:
    """Construct a text prompt from the question and transcript evidence.

    Parameters
    ----------
    question : str
        The user's question.
    evidence : list[RetrievalResult]
        Top-ranked retrieval results with speaker attribution.

    Returns
    -------
    str
        A prompt string ready for the T5 encoder.
    """
    # Use only top-K to fit within context window
    top_evidence = evidence[:_TOP_K_FOR_PROMPT]

    context_parts: list[str] = []
    for i, ev in enumerate(top_evidence, 1):
        clean_text = _normalize_text(ev["text"])
        speaker = ev["speaker"]
        timestamp = _format_timestamp(ev["start"])
        context_parts.append(
            f"Speaker {speaker} at {timestamp}: \"{clean_text}\""
        )
    context_block = "\n".join(context_parts)

    prompt = (
        f"You are an expert meeting analyst. Read the following transcript "
        f"excerpts from a meeting and provide a detailed, complete answer "
        f"to the question. Mention specific speakers by name when relevant. "
        f"If the excerpts don't contain enough information, say so.\n\n"
        f"Meeting transcript excerpts:\n{context_block}\n\n"
        f"Question: {question}\n\n"
        f"Detailed answer:"
    )
    return prompt


def generate_answer(
    question: str,
    evidence: list[RetrievalResult],
    max_new_tokens: int = 256,
) -> dict[str, Any]:
    """Generate a grounded answer given a question and transcript evidence.

    Parameters
    ----------
    question : str
        The user's question.
    evidence : list[RetrievalResult]
        Top retrieved segments.
    max_new_tokens : int
        Maximum tokens in the generated answer.

    Returns
    -------
    dict[str, Any]
        Response dict with keys:

        * ``answer``   – generated text answer
        * ``evidence`` – list of evidence dicts, each containing:
            * ``speaker``
            * ``text``
            * ``timestamp`` (start time)
            * ``trust_score``
    """
    model, tokenizer = _load_model()

    prompt = _build_prompt(question, evidence)

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        max_length=1024,
        truncation=True,
    )

    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        num_beams=5,
        early_stopping=True,
        no_repeat_ngram_size=3,
        length_penalty=1.2,
    )

    answer_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Build structured evidence list for the API response
    evidence_output: list[dict[str, Any]] = []
    for ev in evidence:
        evidence_output.append(
            {
                "speaker": ev["speaker"],
                "text": _normalize_text(ev["text"]),
                "timestamp": ev["start"],
                "trust_score": ev["trust_score"],
            }
        )

    return {
        "answer": answer_text,
        "evidence": evidence_output,
    }

