# MovePal ML Service

## Setup

1. Create venv and activate:
   - Windows PowerShell:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - Windows CMD:
     ```cmd
     python -m venv venv
     .\venv\Scripts\activate.bat
     ```

2. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```

3. (Optional) Install test tools:
   ```bash
   python -m pip install pytest
   ```

## Train model (if `model.pkl` missing)

```bash
python train.py
```

## Run service

```bash
python main.py
```

## Quick end-to-end checks

- Health: `http://127.0.0.1:5001/health`
- Predict now:
  - Endpoint: `POST http://127.0.0.1:5001/predict/now`
  - JSON body: `{ "lat": 6.5244, "lng": 3.3792 }`

## Notes

- Use quotes around paths containing spaces (e.g., `"c:\Users\USER\Documents\Python Project\movepal-ml"`).
- If you want to run tests: `pytest -q` (ensure pytest installed).