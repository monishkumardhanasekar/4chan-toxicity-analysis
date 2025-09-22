import json
import os
from typing import List, Dict, Any


def _load_dataset_lines(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _median(vals: List[float]) -> float:
    vals = sorted(v for v in vals if isinstance(v, (int, float)))
    n = len(vals)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2 == 1:
        return float(vals[mid])
    return float((vals[mid - 1] + vals[mid]) / 2)


def compute_fp_fn(dataset_path: str, out_path: str) -> None:
    items = list(_load_dataset_lines(dataset_path))

    # High-confidence references
    # Ref A (Google-strong): google_toxicity >= 0.9 considered positive
    #   FN-like for OpenAI: ref positive but openai_flagged == False
    #   FP-like for OpenAI: ref negative but openai_flagged == True
    refA_pos = [it for it in items if (it.get("google_toxicity") or 0.0) >= 0.9]
    refA_neg = [it for it in items if (it.get("google_toxicity") or 0.0) < 0.5]

    openai_fn_like = [it for it in refA_pos if not bool(it.get("openai_flagged"))]
    openai_fp_like = [it for it in refA_neg if bool(it.get("openai_flagged"))]

    # Ref B (OpenAI-strong): openai_hate >= 0.9 considered positive (identity/hate signal)
    #   FN-like for Google: ref positive but google_toxicity < 0.5
    #   FP-like for Google: ref negative (openai_hate < 0.2) but google_toxicity >= 0.8
    refB_pos = [it for it in items if (it.get("openai_hate") or 0.0) >= 0.9]
    refB_neg = [it for it in items if (it.get("openai_hate") or 0.0) < 0.2]

    google_fn_like = [it for it in refB_pos if (it.get("google_toxicity") or 0.0) < 0.5]
    google_fp_like = [it for it in refB_neg if (it.get("google_toxicity") or 0.0) >= 0.8]

    def summarize(group: List[Dict[str, Any]]):
        return {
            "n": len(group),
            "median_content_length": _median([it.get("content_length") for it in group]),
            "median_google_toxicity": _median([it.get("google_toxicity") for it in group]),
            "median_openai_hate": _median([it.get("openai_hate") for it in group]),
        }

    out = {
        "dataset": os.path.abspath(dataset_path),
        "definitions": {
            "refA": "google_toxicity >= 0.9 (positive), <0.5 (negative)",
            "refB": "openai_hate >= 0.9 (positive), <0.2 (negative)",
        },
        "openai_relative_to_google": {
            "fn_like": summarize(openai_fn_like),
            "fp_like": summarize(openai_fp_like),
        },
        "google_relative_to_openai": {
            "fn_like": summarize(google_fn_like),
            "fp_like": summarize(google_fp_like),
        },
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    dataset = os.path.join(project_root, "src", "data", "analysis_dataset.jsonl")
    out = os.path.join(project_root, "reports", "metrics", "fp_fn_summary.json")
    compute_fp_fn(dataset, out)


