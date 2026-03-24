import joblib
import numpy as np
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from data import generate_training_data
 
 
# ── File path where the trained model is saved ───────────────────────
MODEL_PATH = "model.pkl"
 
 
def train_model():
    """
    Generates training data, trains a Random Forest classifier,
    prints an accuracy report, and saves the model to model.pkl.
    Call this once before starting the API.
    """
    print("Generating training data...")
    df = generate_training_data(n_samples=8000)
 
    # Features the model learns from
    FEATURES = ["lat", "lng", "hour", "day_of_week"]
    TARGET   = "label"
 
    X = df[FEATURES].values
    y = df[TARGET].values
 
    # 80% training, 20% testing
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
 
    print(f"Training on {len(X_train)} rows, testing on {len(X_test)} rows...")
 
    model = RandomForestClassifier(
        n_estimators=100,       # 100 decision trees
        max_depth=12,           # limit depth to avoid overfitting
        class_weight="balanced",# handle class imbalance automatically
        random_state=42,        # reproducible results
        n_jobs=-1               # use all CPU cores for speed
    )
    model.fit(X_train, y_train)
 
    # ── Evaluate on test set ─────────────────────────────────────────
    y_pred   = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
 
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Accuracy: {accuracy * 100:.1f}%")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(classification_report(y_test, y_pred))
 
    # ── Save the trained model ───────────────────────────────────────
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")
    return model
 
 
def load_model():
    """
    Loads the model from disk if it exists.
    Trains a new one if model.pkl is missing.
    """
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    else:
        print("model.pkl not found — training now...")
        return train_model()
 
 
def predict(lat, lng, hour, day_of_week):
    """
    Make a congestion prediction for the given location and time.
 
    Parameters:
        lat         (float) : Station latitude
        lng         (float) : Station longitude
        hour        (int)   : Hour of day, 0–23
        day_of_week (int)   : Day of week, 0=Monday … 6=Sunday
 
    Returns:
        dict: { status: str, confidence: int }
    """
    model = load_model()
 
    # Build the feature array in the same order as training
    features = np.array([[lat, lng, hour, day_of_week]])
 
    # Get the predicted class
    status = model.predict(features)[0]
 
    # Get the highest probability across all classes (as a percentage)
    proba      = model.predict_proba(features)[0]
    confidence = int(round(max(proba) * 100))
 
    return {
        "status":     status,      # "heavy" | "moderate" | "flowing"
        "confidence": confidence   # 0 – 100
    }
