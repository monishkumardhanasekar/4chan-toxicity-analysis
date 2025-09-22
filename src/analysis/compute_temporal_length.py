import json
import os
from datetime import datetime
from collections import defaultdict


def _load_dataset_lines(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _parse_hour(ts: str):
    if not ts:
        return None
    try:
        # Expecting ISO with Z
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.hour
    except Exception:
        return None


def compute_temporal_length(dataset_path: str, out_path: str) -> None:
    items = list(_load_dataset_lines(dataset_path))

    by_hour = defaultdict(lambda: {"n": 0, "tox_sum": 0.0})
    for it in items:
        hour = _parse_hour(it.get("timestamp_iso"))
        tox = it.get("google_toxicity") or 0.0
        if hour is not None:
            by_hour[hour]["n"] += 1
            by_hour[hour]["tox_sum"] += tox

    hour_summary = {}
    for h, agg in sorted(by_hour.items()):
        n = agg["n"]
        hour_summary[h] = {
            "n": n,
            "mean_google_toxicity": (agg["tox_sum"] / n) if n else 0.0,
        }

    # Length vs toxicity: simple binning like disagreements
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

    by_len = defaultdict(lambda: {"n": 0, "tox_sum": 0.0})
    for it in items:
        b = _length_bin(it.get("content_length"))
        by_len[b]["n"] += 1
        by_len[b]["tox_sum"] += (it.get("google_toxicity") or 0.0)

    len_summary = {}
    for b, agg in by_len.items():
        n = agg["n"]
        len_summary[b] = {
            "n": n,
            "mean_google_toxicity": (agg["tox_sum"] / n) if n else 0.0,
        }

    out = {
        "by_hour_mean_toxicity": hour_summary,
        "by_length_bin_mean_toxicity": len_summary,
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    dataset = os.path.join(project_root, "src", "data", "analysis_dataset.jsonl")
    out = os.path.join(project_root, "reports", "metrics", "temporal_length_summary.json")
    compute_temporal_length(dataset, out)


