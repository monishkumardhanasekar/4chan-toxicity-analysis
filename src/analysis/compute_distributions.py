import json
import os
from typing import Dict, Any, List


FIELDS_GOOGLE = [
    "google_toxicity",
    "google_severe_toxicity",
    "google_threat",
    "google_insult",
    "google_profanity",
    "google_identity_attack",
]

FIELDS_OPENAI = [
    "openai_harassment",
    "openai_harassment_threatening",
    "openai_hate",
    "openai_hate_threatening",
    "openai_violence",
    "openai_violence_graphic",
    "openai_sexual",
    "openai_sexual_minors",
]


def _load_dataset_lines(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _quantiles(values: List[float], qs: List[float]):
    vals = sorted(v for v in values if v is not None)
    n = len(vals)
    if n == 0:
        return {q: None for q in qs}
    out = {}
    for q in qs:
        if q <= 0:
            out[q] = vals[0]
            continue
        if q >= 1:
            out[q] = vals[-1]
            continue
        idx = q * (n - 1)
        lo = int(idx)
        hi = min(lo + 1, n - 1)
        frac = idx - lo
        out[q] = vals[lo] * (1 - frac) + vals[hi] * frac
    return out


def compute_distributions(dataset_path: str, out_path: str) -> None:
    items = list(_load_dataset_lines(dataset_path))
    n = len(items)

    result: Dict[str, Any] = {
        "dataset": os.path.abspath(dataset_path),
        "num_rows": n,
        "google": {},
        "openai": {},
        "openai_flagged_prevalence": None,
    }

    # Google fields: summary + prevalence at 0.5 and 0.8
    for field in FIELDS_GOOGLE:
        vals = [it.get(field) for it in items]
        finite = [v for v in vals if isinstance(v, (int, float))]
        q = _quantiles(finite, [0.0, 0.25, 0.5, 0.75, 0.9, 0.95, 1.0])
        prev_05 = sum(1 for v in finite if v >= 0.5) / len(finite) if finite else 0.0
        prev_08 = sum(1 for v in finite if v >= 0.8) / len(finite) if finite else 0.0
        result["google"][field] = {
            "count": len(finite),
            "quantiles": {str(k): v for k, v in q.items()},
            "prevalence_ge_0_5": prev_05,
            "prevalence_ge_0_8": prev_08,
        }

    # OpenAI scores: summary; flagged prevalence
    flagged = [bool(it.get("openai_flagged")) for it in items]
    result["openai_flagged_prevalence"] = sum(1 for b in flagged if b) / len(flagged) if flagged else 0.0

    for field in FIELDS_OPENAI:
        vals = [it.get(field) for it in items]
        finite = [v for v in vals if isinstance(v, (int, float))]
        q = _quantiles(finite, [0.0, 0.25, 0.5, 0.75, 0.9, 0.95, 1.0])
        prev_05 = sum(1 for v in finite if v >= 0.5) / len(finite) if finite else 0.0
        prev_08 = sum(1 for v in finite if v >= 0.8) / len(finite) if finite else 0.0
        result["openai"][field] = {
            "count": len(finite),
            "quantiles": {str(k): v for k, v in q.items()},
            "prevalence_ge_0_5": prev_05,
            "prevalence_ge_0_8": prev_08,
        }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    dataset = os.path.join(project_root, "src", "data", "analysis_dataset.jsonl")
    out = os.path.join(project_root, "reports", "metrics", "distributions_summary.json")
    compute_distributions(dataset, out)


