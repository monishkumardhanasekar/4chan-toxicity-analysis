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


def _length_bin(n: int) -> str:
    if n is None:
        return "unknown"
    if n < 10:
        return "<10"
    if n < 50:
        return "10-49"
    if n < 100:
        return "50-99"
    if n < 200:
        return "100-199"
    return "200+"


def compute_disagreements(dataset_path: str, out_path: str) -> None:
    items = list(_load_dataset_lines(dataset_path))

    # Define binary views
    G_THR = 0.8
    y_true = [(it.get("google_toxicity") or 0.0) >= G_THR for it in items]
    y_pred = [bool(it.get("openai_flagged")) for it in items]

    total = len(items)
    mismatches = [t != p for t, p in zip(y_true, y_pred)]
    mismatch_rate = sum(1 for m in mismatches if m) / total if total else 0.0

    # Segment by content length bins
    by_len: Dict[str, Dict[str, Any]] = {}
    for it, t, p in zip(items, y_true, y_pred):
        lb = _length_bin(it.get("content_length"))
        seg = by_len.setdefault(lb, {"n": 0, "mismatches": 0})
        seg["n"] += 1
        if t != p:
            seg["mismatches"] += 1
    for k, v in by_len.items():
        v["mismatch_rate"] = (v["mismatches"] / v["n"]) if v["n"] else 0.0

    # Early vs later posts in thread (proxy using post_position)
    by_pos = {"early_<=5": {"n": 0, "mismatches": 0}, "later_>5": {"n": 0, "mismatches": 0}}
    for it, t, p in zip(items, y_true, y_pred):
        pos = it.get("post_position")
        key = "early_<=5" if (isinstance(pos, int) and pos <= 5) else "later_>5"
        by_pos[key]["n"] += 1
        if t != p:
            by_pos[key]["mismatches"] += 1
    for k, v in by_pos.items():
        v["mismatch_rate"] = (v["mismatches"] / v["n"]) if v["n"] else 0.0

    out = {
        "dataset": os.path.abspath(dataset_path),
        "definition": {
            "true": f"google_toxicity >= {G_THR}",
            "pred": "openai_flagged == True",
        },
        "overall": {"n": total, "mismatch_rate": mismatch_rate},
        "by_content_length": by_len,
        "by_post_position": by_pos,
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    dataset = os.path.join(project_root, "src", "data", "analysis_dataset.jsonl")
    out = os.path.join(project_root, "reports", "metrics", "disagreements_summary.json")
    compute_disagreements(dataset, out)


