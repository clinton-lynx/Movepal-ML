from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, learning_curve

from model import FEATURE_COLUMNS


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "data" / "training_dataset.csv"
OUTPUT_PATH = BASE_DIR / "data" / "learning_curve.png"


def main() -> None:
    dataset = pd.read_csv(DATASET_PATH)
    X = dataset[FEATURE_COLUMNS]
    y = dataset["label"]

    estimator = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    train_sizes, train_scores, validation_scores = learning_curve(
        estimator,
        X,
        y,
        cv=cv,
        scoring="accuracy",
        train_sizes=[0.1, 0.3, 0.5, 0.7, 1.0],
        n_jobs=-1,
    )

    train_mean = train_scores.mean(axis=1)
    train_std = train_scores.std(axis=1)
    validation_mean = validation_scores.mean(axis=1)
    validation_std = validation_scores.std(axis=1)

    plt.figure(figsize=(10, 6))
    plt.plot(train_sizes, train_mean, marker="o", label="Training Accuracy")
    plt.plot(train_sizes, validation_mean, marker="o", label="Validation Accuracy")
    plt.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.15)
    plt.fill_between(train_sizes, validation_mean - validation_std, validation_mean + validation_std, alpha=0.15)
    plt.title("MovePal ML Learning Curve")
    plt.xlabel("Training Examples")
    plt.ylabel("Accuracy")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=200)

    print(f"Saved learning curve to: {OUTPUT_PATH}")
    print("Train means:", [round(value, 4) for value in train_mean])
    print("Validation means:", [round(value, 4) for value in validation_mean])


if __name__ == "__main__":
    main()
