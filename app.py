import os
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

from model import load_model, predict


app = Flask(__name__)
CORS(app)

_model_ready = False


def error_response(message: str, status_code: int = 400):
    return jsonify({'success': False, 'error': message}), status_code


def get_model():
    global _model_ready
    if not _model_ready:
        load_model()
        _model_ready = True


def validate_lat_lng(lat, lng):
    if lat is None:
        return 'lat is required'
    if lng is None:
        return 'lng is required'
    try:
        lat = float(lat)
        lng = float(lng)
    except (TypeError, ValueError):
        return 'lat and lng must be valid numbers'
    if not (-90 <= lat <= 90):
        return 'lat must be between -90 and 90'
    if not (-180 <= lng <= 180):
        return 'lng must be between -180 and 180'
    return None


def validate_hour_day(hour, day_of_week):
    if hour is None:
        return 'hour is required'
    if day_of_week is None:
        return 'day_of_week is required'
    try:
        hour = int(hour)
        day_of_week = int(day_of_week)
    except (TypeError, ValueError):
        return 'hour and day_of_week must be integers'
    if not (0 <= hour <= 23):
        return 'hour must be between 0 and 23'
    if not (0 <= day_of_week <= 6):
        return 'day_of_week must be between 0 and 6'
    return None


@app.before_request
def preload_model():
    get_model()


@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'service': 'MovePal ML API',
        'version': '2.0.0',
        'description': 'People congestion prediction for Lagos BRT stations',
        'data_sources': ['TomTom Traffic Flow', 'Open-Meteo', 'stations.csv'],
        'endpoints': {
            'GET /health': 'Service health check',
            'POST /predict/now': 'Predict current station congestion',
            'POST /predict': 'Predict station congestion for a specified time',
        },
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'movepal-ml',
        'model_ready': _model_ready,
        'tomtom_key_configured': bool(os.getenv('TOMTOM_API_KEY')),
    })


@app.route('/predict/now', methods=['POST'])
def predict_now():
    body = request.get_json(silent=True) or {}
    validation_error = validate_lat_lng(body.get('lat'), body.get('lng'))
    if validation_error:
        return error_response(validation_error)
    now = datetime.now()
    result = predict(
        lat=float(body['lat']),
        lng=float(body['lng']),
        hour=now.hour,
        day_of_week=now.weekday(),
    )
    return jsonify({'success': True, 'data': result})


@app.route('/predict', methods=['POST'])
def predict_custom():
    body = request.get_json(silent=True) or {}
    validation_error = validate_lat_lng(body.get('lat'), body.get('lng'))
    if validation_error:
        return error_response(validation_error)
    validation_error = validate_hour_day(body.get('hour'), body.get('day_of_week'))
    if validation_error:
        return error_response(validation_error)
    result = predict(
        lat=float(body['lat']),
        lng=float(body['lng']),
        hour=int(body['hour']),
        day_of_week=int(body['day_of_week']),
    )
    return jsonify({'success': True, 'data': result})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
