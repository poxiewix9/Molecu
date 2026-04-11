"""DeBERTa NLI Contradiction Verifier.

Uses cross-encoder/nli-deberta-v3-small to detect NLI contradictions
between agent claims. Inference runs in a thread-pool executor so it
does not block the async event loop.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

log = logging.getLogger(__name__)

_MODEL_NAME = "cross-encoder/nli-deberta-v3-small"
_tokenizer = None
_model = None

LABEL_MAP = {0: "contradiction", 1: "entailment", 2: "neutral"}

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="deberta")


def _load_model():
    global _tokenizer, _model
    if _tokenizer is None:
        log.info("Loading DeBERTa NLI model (%s)…", _MODEL_NAME)
        _tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
        _model = AutoModelForSequenceClassification.from_pretrained(_MODEL_NAME)
        _model.eval()
        log.info("DeBERTa model loaded successfully.")
    return _tokenizer, _model


def _evaluate_sync(claim_a: str, claim_b: str) -> dict:
    """Synchronous NLI inference (runs inside thread pool)."""
    tokenizer, model = _load_model()

    inputs = tokenizer(
        claim_a,
        claim_b,
        return_tensors="pt",
        truncation=True,
        max_length=512,
    )

    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=-1).squeeze().tolist()

    scores = {LABEL_MAP[i]: round(p, 4) for i, p in enumerate(probs)}
    contradiction_score = scores["contradiction"]

    result = {
        "claim_a": claim_a,
        "claim_b": claim_b,
        "scores": scores,
        "predicted_label": max(scores, key=scores.get),
        "conflict_detected": contradiction_score > 0.80,
    }

    if result["conflict_detected"]:
        result["explanation"] = (
            f"High contradiction ({contradiction_score:.0%}) between agent claims: "
            f"'{claim_a}' vs '{claim_b}'. Halting pipeline."
        )

    return result


def evaluate_claims(claim_a: str, claim_b: str) -> dict:
    """Synchronous entry point (backwards-compatible)."""
    return _evaluate_sync(claim_a, claim_b)


async def evaluate_claims_async(claim_a: str, claim_b: str) -> dict:
    """Async entry point — offloads inference to a thread pool executor."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, _evaluate_sync, claim_a, claim_b)
