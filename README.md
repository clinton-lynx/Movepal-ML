# MovePal ML Prediction Service v2

This version upgrades the original synthetic-data approach into a hackathon-friendly real-data pipeline:

- station intelligence in `stations_master.csv`
- live TomTom traffic flow
- live Open-Meteo weather
- a people-congestion scoring layer that bootstraps labels
- a Random Forest classifier behind a Flask API

## Project location

`C:\Users\USER\Documents\Python Project\movepal-ml-2`

## Files

- `app.py` - Flask API
- `data.py` - data fetching, dataset building, station logic
- `model.py` - training and prediction
- `train.py` - run model training
- `stations_master.csv` - station master data used for training and live predictions

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Set your TomTom API key:

```powershell
$env:TOMTOM_API_KEY="YOUR_KEY"
```

Or create a `.env` file in the project root:

```env
TOMTOM_API_KEY=YOUR_KEY
```

## Train

```powershell
python train.py
```

This will:

1. fetch a live observation for each station
2. save observations to `data/observations.csv`
3. expand them into a training dataset
4. train the model
5. save `model.pkl`

## Run

```powershell
python app.py
```

The API runs on port `5001`.


## Collect snapshots

One live snapshot for all stations:

```powershell
python collect.py
```

Collect every 30 minutes for 24 hours:

```powershell
python collect_loop.py --interval-minutes 30 --runs 48
```

Collect every 30 minutes for 12 hours:

```powershell
python collect_loop.py --interval-minutes 30 --runs 24
```

## Recommended workflow

1. Start collecting snapshots as early as possible.
2. Let the collector build `data/observations.csv` over time.
3. Retrain with `python train.py` after you have enough observations.
4. Run the API with `python app.py`.

The collector does not retrain automatically. This is intentional so you can control when the model is refreshed.
