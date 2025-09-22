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


def _deciles(values: List[float]) -> List[float]:
    vals = sorted(v for v in values if isinstance(v, (int, float)))
    n = len(vals)
    if n == 0:
        return [None]*11
    qs = []
    for i in range(11):
        q = i/10
        idx = q*(n-1)
        lo = int(idx)
        hi = min(lo+1, n-1)
        frac = idx-lo
        qs.append(vals[lo]*(1-frac)+vals[hi]*frac)
    return qs


def _binned_positive_rate(x: List[float], y_bool: List[bool], bins: List[float]) -> List[Dict[str, Any]]:
    # bins length 11 (deciles), create 10 intervals [b[i], b[i+1]]
    out = []
    for i in range(10):
        lo, hi = bins[i], bins[i+1]
        num = den = 0
        for xv, yv in zip(x, y_bool):
            if isinstance(xv, (int, float)) and lo is not None and hi is not None:
                # include right edge on last bin
                cond = (xv >= lo and (xv < hi or (i == 9 and xv <= hi)))
                if cond:
                    den += 1
                    if bool(yv):
                        num += 1
        rate = num/den if den else 0.0
        out.append({"bin": i+1, "lo": lo, "hi": hi, "n": den, "positive_rate": rate})
    return out


def compute_sensitivity(dataset_path: str, out_path: str) -> None:
    items = list(_load_dataset_lines(dataset_path))
    # series
    g_tox = [it.get("google_toxicity") for it in items]
    g_id = [it.get("google_identity_attack") for it in items]
    o_flag = [bool(it.get("openai_flagged")) for it in items]
    o_hate = [it.get("openai_hate") for it in items]

    # Deciles for google signals
    d_tox = _deciles(g_tox)
    d_id = _deciles(g_id)

    # Positive rate of OpenAI flagged across Google deciles
    tox_curve = _binned_positive_rate(g_tox, o_flag, d_tox)
    id_curve = _binned_positive_rate(g_id, o_flag, d_id)

    # Also positive rate of Google high (>=0.8) across OpenAI hate deciles
    d_ohate = _deciles([v for v in o_hate if isinstance(v, (int, float))] or [0.0])
    # Map back: need aligned lists for google high given openai hate bin
    def google_high_rate_across_openai(openai_vals: List[float], google_vals: List[float], high_thr: float = 0.8):
        out = []
        for i in range(10):
            lo, hi = d_ohate[i], d_ohate[i+1]
            num = den = 0
            for ov, gv in zip(openai_vals, google_vals):
                if isinstance(ov, (int, float)) and isinstance(gv, (int, float)):
                    cond = (ov >= lo and (ov < hi or (i == 9 and ov <= hi)))
                    if cond:
                        den += 1
                        if gv >= high_thr:
                            num += 1
            rate = num/den if den else 0.0
            out.append({"bin": i+1, "lo": d_ohate[i], "hi": d_ohate[i+1], "n": den, "positive_rate": rate})
        return out

    tox_given_ohate = google_high_rate_across_openai(o_hate, g_tox)

    out = {
        "dataset": os.path.abspath(dataset_path),
        "openai_flagged_rate_across_google_toxicity_deciles": tox_curve,
        "openai_flagged_rate_across_google_identity_attack_deciles": id_curve,
        "google_toxicity_ge_0_8_rate_across_openai_hate_deciles": tox_given_ohate,
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    dataset = os.path.join(project_root, "src", "data", "analysis_dataset.jsonl")
    out = os.path.join(project_root, "reports", "metrics", "sensitivity_summary.json")
    compute_sensitivity(dataset, out)


