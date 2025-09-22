import json
import os
from typing import Dict, Any, List, Tuple


def _load_dataset_lines(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _confusion_and_metrics(y_true: List[bool], y_pred: List[bool]) -> Dict[str, Any]:
    assert len(y_true) == len(y_pred)
    tp = fp = tn = fn = 0
    for t, p in zip(y_true, y_pred):
        if t and p:
            tp += 1
        elif not t and p:
            fp += 1
        elif t and not p:
            fn += 1
        else:
            tn += 1
    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    # Matthews correlation coefficient
    import math
    denom = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = ((tp * tn - fp * fn) / denom) if denom else 0.0

    # Cohen's kappa
    po = accuracy
    p_yes_true = (tp + fn) / total if total else 0.0
    p_yes_pred = (tp + fp) / total if total else 0.0
    p_no_true = 1 - p_yes_true
    p_no_pred = 1 - p_yes_pred
    pe = p_yes_true * p_yes_pred + p_no_true * p_no_pred
    kappa = (po - pe) / (1 - pe) if (1 - pe) else 0.0

    return {
        "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "total": total},
        "metrics": {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "mcc": mcc,
            "cohen_kappa": kappa,
        },
    }


def _binary_from_threshold(values: List[float], threshold: float) -> List[bool]:
    return [v is not None and v >= threshold for v in values]


def _extract_series(items, field: str) -> List[Any]:
    return [itm.get(field) for itm in items]


def compute_agreement(dataset_path: str, out_path: str) -> None:
    items = list(_load_dataset_lines(dataset_path))

    # Define primary thresholds
    google_high = 0.8
    google_med = 0.5
    openai_med = 0.5
    openai_high = 0.8

    # Build comparisons: (name, y_true_expr, y_pred_expr)
    # y_true from Google, y_pred from OpenAI
    pairs: List[Tuple[str, str, str]] = [
        ("toxicity_vs_openai_flagged", "google_toxicity", "openai_flagged"),
        ("toxicity_vs_openai_harassment", "google_toxicity", "openai_harassment"),
        ("identity_attack_vs_openai_hate", "google_identity_attack", "openai_hate"),
        ("threat_vs_openai_violence", "google_threat", "openai_violence"),
    ]

    results: Dict[str, Any] = {
        "dataset": os.path.abspath(dataset_path),
        "thresholds": {
            "google_high": google_high,
            "google_med": google_med,
            "openai_med": openai_med,
            "openai_high": openai_high,
        },
        "comparisons": {},
    }

    for name, g_field, o_field in pairs:
        g_vals = _extract_series(items, g_field)
        if o_field == "openai_flagged":
            o_vals = _extract_series(items, o_field)
            # Use boolean directly
            y_pred = [bool(v) for v in o_vals]
            # Evaluate at both google thresholds
            for g_thr in (google_med, google_high):
                y_true = _binary_from_threshold(g_vals, g_thr)
                key = f"{name}__g>={g_thr}"
                results["comparisons"][key] = _confusion_and_metrics(y_true, y_pred)
        else:
            o_vals = _extract_series(items, o_field)
            # Evaluate grid of thresholds
            for g_thr in (google_med, google_high):
                y_true = _binary_from_threshold(g_vals, g_thr)
                for o_thr in (openai_med, openai_high):
                    y_pred = _binary_from_threshold(o_vals, o_thr)
                    key = f"{name}__g>={g_thr}__o>={o_thr}"
                    results["comparisons"][key] = _confusion_and_metrics(y_true, y_pred)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    dataset = os.path.join(project_root, "src", "data", "analysis_dataset.jsonl")
    out = os.path.join(project_root, "reports", "metrics", "agreement_summary.json")
    compute_agreement(dataset, out)


