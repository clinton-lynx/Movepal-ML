import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from model import load_model, predict
 
 
# ── Create Flask app ─────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)  # Allow the MovePal mobile app to call this API
 
 
# ── Pre-load the model at startup ────────────────────────────────────
# This means the first request is fast — the model is already in memory.
_model = None
 
 
def get_model():
    global _model
    if _model is None:
        print("Loading model into memory...")
        _model = load_model()
        print("Model ready.")
    return _model


# ── Root endpoint ────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def root():
    """
    API information and available endpoints.
    """
    return jsonify({
        "service": "MovePal ML API",
        "version": "1.0.0",
        "description": "Traffic congestion prediction for Lagos, Nigeria",
        "endpoints": {
            "GET /health": "Service health check",
            "POST /predict/now": "Predict current traffic congestion",
            "POST /predict": "Predict traffic for specific time"
        },
        "documentation": "See README.md for usage examples"
    }), 200


# Pre-load when the server starts
with app.app_context():
    get_model()
 
 
# ── Endpoint 1: Health check ─────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":  "ok",
        "service": "movepal-ml"
    }), 200
 
 
# ── Endpoint 2: Predict NOW ──────────────────────────────────────────
@app.route("/predict/now", methods=["POST"])
def predict_now():
    """
    Predict congestion at a station right now.
    Automatically uses the current hour and weekday.
    Body: { lat: float, lng: float }
    """
    body = request.get_json(silent=True) or {}
 
    lat = body.get("lat")
    lng = body.get("lng")

    # Validate required fields
    if lat is None or lng is None:
        return jsonify({
            "success": False,
            "error":   "Missing required fields: lat and lng"
        }), 400

    # Type-check numeric values to avoid 500 on malformed input
    try:
        lat = float(lat); lng = float(lng)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "lat and lng must be numbers"}), 400

    # Use current Lagos time
    now         = datetime.now()
    hour        = now.hour
    day_of_week = now.weekday()  # 0=Monday … 6=Sunday
 
    result = predict(
        lat=float(lat),
        lng=float(lng),
        hour=hour,
        day_of_week=day_of_week
    )
 
    return jsonify({
        "success": True,
        "data":    result
    }), 200
 
 
# ── Endpoint 3: Custom Predict ───────────────────────────────────────
@app.route("/predict", methods=["POST"])
def predict_custom():
    """
    Predict for any specific time — useful for testing and demo.
    Body: { lat: float, lng: float, hour: int, day_of_week: int }
    """
    body = request.get_json(silent=True) or {}
 
    lat         = body.get("lat")
    lng         = body.get("lng")
    hour        = body.get("hour")
    day_of_week = body.get("day_of_week")
 
    # Validate all four required fields
    missing = [f for f, v in {
        "lat": lat, "lng": lng,
        "hour": hour, "day_of_week": day_of_week
    }.items() if v is None]
 
    if missing:
        return jsonify({
            "success": False,
            "error":   f"Missing required fields: {', '.join(missing)}"
        }), 400
 
    # Type-check numeric values to avoid 500 on malformed input
    try:
        lat = float(lat)
        lng = float(lng)
        hour = int(hour)
        day_of_week = int(day_of_week)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "lat,lng,hour,day_of_week must be numbers"}), 400
 
    result = predict(
        lat=lat,
        lng=lng,
        hour=hour,
        day_of_week=day_of_week
    )
 
    return jsonify({
        "success": True,
        "data":    result
    }), 200
 
 
# ── Start the server ─────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)