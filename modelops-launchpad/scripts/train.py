from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import sklearn
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


def train_model(output_dir: str | Path) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    features, labels = make_classification(
        n_samples=900,
        n_features=4,
        n_informative=3,
        n_redundant=0,
        n_classes=3,
        n_clusters_per_class=1,
        class_sep=1.25,
        random_state=41,
    )
    x_train, x_test, y_train, y_test = train_test_split(
        features, labels, test_size=0.2, random_state=41, stratify=labels
    )
    model = RandomForestClassifier(
        n_estimators=120, max_depth=6, min_samples_leaf=2,
        random_state=41, n_jobs=1,
    )
    model.fit(x_train, y_train)
    accuracy = float(accuracy_score(y_test, model.predict(x_test)))
    bundle = {
        "model": model,
        "model_version": "0.1.0",
        "labels": ["class_0", "class_1", "class_2"],
        "feature_names": ["feature_1", "feature_2", "feature_3", "feature_4"],
        "sklearn_version": sklearn.__version__,
    }
    joblib.dump(bundle, output / "model.joblib")
    metadata = {
        "model_version": bundle["model_version"],
        "model_type": "RandomForestClassifier",
        "sklearn_version": sklearn.__version__,
        "random_state": 41,
        "test_accuracy": round(accuracy, 6),
        "n_samples": int(len(features)),
        "n_features": int(features.shape[1]),
        "labels": bundle["labels"],
        "feature_names": bundle["feature_names"],
    }
    (output / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a reproducible demo classifier.")
    parser.add_argument("--output-dir", default="artifacts")
    args = parser.parse_args()
    print(json.dumps(train_model(args.output_dir), indent=2))


if __name__ == "__main__":
    main()
