from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from data import build_observation, build_training_dataset, nearest_station


MODEL_PATH = Path(__file__).resolve().parent / "model.pkl"
FEATURE_COLUMNS = [
    "lat", "lng", "hour", "day_of_week", "is_weekend", "is_terminal",
    "is_interchange", "station_importance", "busy_factor", "route_overlap_count",
    "transfer_score", "near_market", "near_business_district", "traffic_pressure",
    "current_speed", "free_flow_speed", "traffic_confidence", "rain",
    "precipitation", "temperature_2m", "cloud_cover"
]


def train_model() -> dict[str, Any]:
    dataset = build_training_dataset()
    X = dataset[FEATURE_COLUMNS]
    y = dataset["label"]
    label_counts = y.value_counts()
    stratify_target = y if int(label_counts.min()) >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=stratify_target,
    )
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    report = classification_report(y_test, predictions, zero_division=0)
    joblib.dump({"model": model, "feature_columns": FEATURE_COLUMNS}, MODEL_PATH)
    return {"accuracy": accuracy, "report": report, "rows": len(dataset)}


def load_model() -> dict[str, Any]:
    if MODEL_PATH.exists():
        return joblib.load(MODEL_PATH)
    train_model()
    return joblib.load(MODEL_PATH)


def prepare_features(lat: float, lng: float, hour: int, day_of_week: int) -> pd.DataFrame:
    station = nearest_station(lat, lng)
    row = build_observation(station, hour=hour, day_of_week=day_of_week)
    row["lat"] = lat
    row["lng"] = lng
    row["is_weekend"] = int(day_of_week >= 5)
    return pd.DataFrame([row])[FEATURE_COLUMNS]


def predict(lat: float, lng: float, hour: int, day_of_week: int) -> dict[str, Any]:
    payload = load_model()
    model = payload["model"]
    features = prepare_features(lat, lng, hour, day_of_week)
    status = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]
    classes = model.classes_
    confidence = round(float(max(probabilities) * 100.0), 2)
    station = nearest_station(lat, lng)
    return {
        "status": str(status),
        "confidence": confidence,
        "station_context": {
            "station_id": station.station_id,
            "station_name": station.station_name,
            "corridor": station.corridor,
            "corridor_type": station.corridor_type,
            "station_role": station.station_role,
            "busy_factor": station.busy_factor,
            "transfer_score": station.transfer_score,
            "land_use_type": station.land_use_type,
        },
        "class_probabilities": {
            str(label): round(float(probability) * 100.0, 2)
            for label, probability in zip(classes, probabilities)
        },
    }
