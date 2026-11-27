import json
from pathlib import Path

from app.main import DocumentStore


def evaluate(dataset_path: Path, k: int = 3) -> dict:
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    store = DocumentStore(":memory:")
    for document in dataset["documents"]:
        store.add(document["source"], document["text"])
    recalls, reciprocal_ranks = [], []
    for item in dataset["queries"]:
        ranked = store.retrieve(item["question"], k)
        positions = [
            index for index, candidate in enumerate(ranked, 1)
            if candidate["source"] == item["expected_source"]
        ]
        recalls.append(1.0 if positions else 0.0)
        reciprocal_ranks.append(1.0 / positions[0] if positions else 0.0)
    store.close()
    total = max(1, len(dataset["queries"]))
    return {
        f"recall_at_{k}": sum(recalls) / total,
        "mrr": sum(reciprocal_ranks) / total,
        "query_count": len(dataset["queries"]),
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    print(json.dumps(evaluate(root / "eval" / "queries.json"), indent=2))
