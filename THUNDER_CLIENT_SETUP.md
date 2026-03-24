# Thunder Client Setup for MovePal ML API

## Installation
1. In VS Code, press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type: `Extensions: Install Extensions`
3. Search for: `Thunder Client`
4. Click `Install` on the extension by `Rangav`

## Create These Requests

### Request 1: API Info
- **Method**: GET
- **URL**: `http://127.0.0.1:5001/`
- **Headers**: (none)

### Request 2: Health Check
- **Method**: GET
- **URL**: `http://127.0.0.1:5001/health`
- **Headers**: (none)

### Request 3: Predict Current Traffic
- **Method**: POST
- **URL**: `http://127.0.0.1:5001/predict/now`
- **Headers**:
  - `Content-Type: application/json`
- **Body** (JSON):
  ```json
  {
    "lat": 6.5244,
    "lng": 3.3792
  }
  ```

### Request 4: Predict Custom Time
- **Method**: POST
- **URL**: `http://127.0.0.1:5001/predict`
- **Headers**:
  - `Content-Type: application/json`
- **Body** (JSON):
  ```json
  {
    "lat": 6.5244,
    "lng": 3.3792,
    "hour": 14,
    "day_of_week": 2
  }
  ```

## Expected Responses

- **API Info**: Service overview with available endpoints
- **Health**: `{"status": "ok", "service": "movepal-ml"}`
- **Predictions**: `{"success": true, "data": {"status": "flowing", "confidence": 52}}`

## How to Use Thunder Client

1. After installation, look for the Thunder Client icon in the VS Code sidebar
2. Click the "+" button to create a new request
3. Fill in the details as shown above
4. Click "Send" to test the endpoint
5. Save requests to a collection for reuse

## Quick Test

Once set up, you should see:
- GET requests work immediately in browser
- POST requests return traffic predictions with confidence scores