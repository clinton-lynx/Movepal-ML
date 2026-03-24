import numpy as np
import pandas as pd


# ── Known Lagos stations with base busyness factor ──────────────────────
STATIONS = [
    {"name": "Oshodi Terminal",    "lat": 6.5570, "lng": 3.3500, "busy_factor": 0.90},
    {"name": "Mile 2",             "lat": 6.4698, "lng": 3.3023, "busy_factor": 0.85},
    {"name": "Ojota",              "lat": 6.5952, "lng": 3.3831, "busy_factor": 0.70},
    {"name": "Yaba",               "lat": 6.5096, "lng": 3.3780, "busy_factor": 0.65},
    {"name": "Ikeja Under Bridge", "lat": 6.5958, "lng": 3.3403, "busy_factor": 0.60},
    {"name": "Berger",             "lat": 6.6349, "lng": 3.3782, "busy_factor": 0.55},
    {"name": "Surulere",           "lat": 6.4969, "lng": 3.3481, "busy_factor": 0.55},
    {"name": "CMS Marina",         "lat": 6.4505, "lng": 3.3958, "busy_factor": 0.40},
    {"name": "Victoria Island",    "lat": 6.4281, "lng": 3.4219, "busy_factor": 0.35},
    {"name": "Lekki",              "lat": 6.4306, "lng": 3.5217, "busy_factor": 0.30},
]


def generate_training_data(n_samples=8000, random_seed=42):
    """
    Generate n_samples synthetic Lagos traffic observations.
    Each row represents one traffic reading at a station at a specific
    hour and day of week. Labels are: heavy, moderate, flowing.
    """
    np.random.seed(random_seed)
    rows = []

    for _ in range(n_samples):
        station = STATIONS[np.random.randint(0, len(STATIONS))]
        lat = station["lat"] + np.random.uniform(-0.02, 0.02)
        lng = station["lng"] + np.random.uniform(-0.02, 0.02)

        hour = np.random.randint(0, 24)
        day_of_week = np.random.randint(0, 7)
        is_weekday = day_of_week < 5

        score = 0.0
        if is_weekday and 6 <= hour <= 9:
            score += 0.70
        if is_weekday and 16 <= hour <= 20:
            score += 0.75
        if day_of_week == 4 and 17 <= hour <= 20:
            score += 0.15
        if hour >= 23 or hour <= 4:
            score -= 0.60
        if day_of_week >= 5 and hour < 12:
            score -= 0.30

        score += station["busy_factor"] * 0.30
        score += np.random.uniform(-0.12, 0.12)
        score = float(np.clip(score, 0.0, 1.0))

        if score >= 0.60:
            label = "heavy"
        elif score >= 0.30:
            label = "moderate"
        else:
            label = "flowing"

        rows.append({
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "hour": hour,
            "day_of_week": day_of_week,
            "label": label
        })

    df = pd.DataFrame(rows)
    return df


if __name__ == "__main__":
    df = generate_training_data()
    print(f"Generated {len(df)} rows")
    print(df["label"].value_counts())
    print(df.head(5))
