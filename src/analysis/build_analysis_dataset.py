import json
import os
import sys
from datetime import datetime, timezone


def _iso_utc_from_epoch(epoch_seconds):
    try:
        return datetime.fromtimestamp(int(epoch_seconds), tz=timezone.utc).isoformat().replace("+00:00", "Z")
    except Exception:
        return None


def _build_post_index_from_collection(collection_path):
    """
    Build a minimal index: post_id -> {thread_id, post_position}
    from final_collection.json structure.
    """
    with open(collection_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    index = {}
    threads = data.get("threads", [])
    for thread in threads:
        thread_id = thread.get("thread_id")
        op_post = thread.get("op_post") or {}
        if op_post:
            pid = op_post.get("post_id")
            if pid is not None:
                index[pid] = {
                    "thread_id": thread_id,
                    "post_position": op_post.get("post_position")
                }
        for reply in thread.get("replies", []) or []:
            pid = reply.get("post_id")
            if pid is not None:
                index[pid] = {
                    "thread_id": thread_id,
                    "post_position": reply.get("post_position")
                }
    return index


def _iter_api_results(api_results_path):
    """
    Yield result items from api_results.json one by one (stream-friendly).
    Structure is a dict with key "results": [...].
    """
    with open(api_results_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for item in data.get("results", []) or []:
        yield item


def build_analysis_dataset(
    api_results_path: str,
    final_collection_path: str,
    output_path: str,
):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    post_index = _build_post_index_from_collection(final_collection_path)

    total = 0
    kept = 0
    missing_thread_meta = 0
    missing_openai = 0
    missing_google = 0

    with open(output_path, "w", encoding="utf-8") as out_f:
        for item in _iter_api_results(api_results_path):
            total += 1

            google = item.get("google_result") or {}
            openai = item.get("openai_result") or None

            google_ok = bool(google.get("success"))
            openai_ok = bool(openai.get("success")) if openai else False

            if not google_ok:
                missing_google += 1
            if not openai_ok:
                missing_openai += 1

            # Keep only posts where both APIs succeeded
            if not (google_ok and openai_ok):
                continue

            post_id = item.get("post_id")
            # Thread metadata (optional but preferred)
            idx = post_index.get(post_id)
            if idx is None:
                missing_thread_meta += 1
                thread_id = item.get("thread_id")
                post_position = None
            else:
                thread_id = idx.get("thread_id")
                post_position = idx.get("post_position")

            # Timestamp in ISO (UTC) from epoch if available
            timestamp_epoch = item.get("timestamp")
            timestamp_iso = _iso_utc_from_epoch(timestamp_epoch) if timestamp_epoch else None

            # Flatten Google
            record = {
                "post_id": post_id,
                "thread_id": thread_id,
                "post_position": post_position,
                "timestamp_iso": timestamp_iso,
                "content_length": item.get("content_length"),
                "google_toxicity": google.get("toxicity"),
                "google_severe_toxicity": google.get("severe_toxicity"),
                "google_threat": google.get("threat"),
                "google_insult": google.get("insult"),
                "google_profanity": google.get("profanity"),
                "google_identity_attack": google.get("identity_attack"),
                "openai_flagged": openai.get("flagged"),
                # Selected OpenAI category scores (extendable as needed)
                "openai_harassment": (openai.get("category_scores") or {}).get("harassment"),
                "openai_harassment_threatening": (openai.get("category_scores") or {}).get("harassment_threatening"),
                "openai_hate": (openai.get("category_scores") or {}).get("hate"),
                "openai_hate_threatening": (openai.get("category_scores") or {}).get("hate_threatening"),
                "openai_violence": (openai.get("category_scores") or {}).get("violence"),
                "openai_violence_graphic": (openai.get("category_scores") or {}).get("violence_graphic"),
                "openai_sexual": (openai.get("category_scores") or {}).get("sexual"),
                "openai_sexual_minors": (openai.get("category_scores") or {}).get("sexual_minors"),
                "provenance_google_success": google_ok,
                "provenance_openai_success": openai_ok,
            }

            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            kept += 1

    summary = {
        "input_api_results": api_results_path,
        "input_final_collection": final_collection_path,
        "output": output_path,
        "total_items_in_api_results": total,
        "kept_both_apis_success": kept,
        "excluded_missing_google_success": missing_google,
        "excluded_missing_openai_success": missing_openai,
        "missing_thread_metadata_count": missing_thread_meta,
    }

    sys.stdout.write(json.dumps({"build_summary": summary}, indent=2) + "\n")


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    api_results = os.path.join(project_root, "src", "data", "api_results.json")
    final_collection = os.path.join(project_root, "src", "data", "final_collection.json")
    output = os.path.join(project_root, "src", "data", "analysis_dataset.jsonl")

    build_analysis_dataset(api_results, final_collection, output)


