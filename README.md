# MovePal ML Prediction Service v2

Predicts congestion levels at BRT stations using live traffic and weather data with a Random Forest classifier.

## How the Prediction Model Works

1. **Data Sources**:
   - Station master data from `stations_master.csv` (location, importance, type)
   - Live traffic flow from TomTom API (current/free flow speeds, confidence)
   - Live weather from Open-Meteo API (rain, precipitation, temperature, cloud cover)

2. **Feature Engineering**:
   - Station features: lat/lng, terminal/interchange status, busy factor, transfer score, land use
   - Time features: hour, day of week, weekend flag
   - Traffic features: speed ratios, pressure metrics
   - Weather features: precipitation, temperature

3. **Label Bootstrapping**:
   - Congestion labels (low/medium/high) generated from traffic pressure and station busy factors
   - No manual labeling required

4. **Model Training**:
   - Random Forest classifier with balanced class weights
   - Trained on expanded dataset from collected observations

5. **Prediction**:
   - Input: latitude, longitude, hour, day of week
   - Finds nearest station
   - Fetches live traffic/weather data
   - Outputs congestion status with confidence and class probabilities

## Setup

1. Create virtual environment:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate  # PowerShell
   # or .venv\Scripts\activate.bat  # cmd
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. Set TomTom API key in `.env`:
   ```
   TOMTOM_API_KEY=your_api_key_here
   ```

## Train Model

```powershell
python train.py
```

Fetches live observations, builds training dataset, trains and saves model.

## Run API

```powershell
python app.py
```

Starts Flask API on port 5001.

### Endpoints

- `GET /predict/now`: Predict congestion for current time at all stations
- `POST /predict/custom`: Predict for specific location/time (JSON body: `{"lat": float, "lng": float, "hour": int, "day_of_week": int}`)

## Collect Data (Optional)

```powershell
python collect.py  # One snapshot
python collect_loop.py --interval-minutes 30 --runs 24  # Continuous
```

Builds `data/observations.csv` for training.
