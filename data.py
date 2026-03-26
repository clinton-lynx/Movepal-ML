from __future__ import annotations

import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATIONS_FILE = BASE_DIR / "stations_master.csv"
OBSERVATIONS_FILE = DATA_DIR / "observations.csv"
TRAINING_DATA_FILE = DATA_DIR / "training_dataset.csv"

load_dotenv(BASE_DIR / ".env")


@dataclass
class StationContext:
    station_id: str
    station_name: str
    lat: float
    lng: float
    corridor: str
    corridor_type: str
    station_role: str
    is_terminal: int
    is_interchange: int
    station_importance: int
    busy_factor: float
    route_overlap_count: int
    transfer_score: int
    land_use_type: str
    near_market: int
    near_business_district: int


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_stations(path: Path = STATIONS_FILE) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"stations_master.csv not found at {path}. Add your BRT station list before training.")
    stations = pd.read_csv(path)
    required = {
        "station_id", "station_name", "lat", "lng", "corridor", "is_terminal",
        "is_interchange", "station_importance", "near_market", "near_business_district"
    }
    missing = required.difference(stations.columns)
    if missing:
        raise ValueError(f"stations_master.csv is missing columns: {sorted(missing)}")
    if "busy_factor" not in stations.columns:
        stations["busy_factor"] = stations["station_importance"].astype(float) / 5.0
    if "corridor_type" not in stations.columns:
        stations["corridor_type"] = "local"
    if "station_role" not in stations.columns:
        stations["station_role"] = "standard"
    if "route_overlap_count" not in stations.columns:
        stations["route_overlap_count"] = 1
    if "transfer_score" not in stations.columns:
        stations["transfer_score"] = stations["is_interchange"].astype(int) * 3 + stations["is_terminal"].astype(int) * 2
    if "land_use_type" not in stations.columns:
        stations["land_use_type"] = "mixed"
    return stations


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_km = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_km * c


def nearest_station(lat: float, lng: float, stations: pd.DataFrame | None = None) -> StationContext:
    stations = stations if stations is not None else load_stations()
    candidates = stations.copy()
    candidates["distance_km"] = candidates.apply(
        lambda row: haversine_km(lat, lng, float(row["lat"]), float(row["lng"])),
        axis=1,
    )
    row = candidates.sort_values("distance_km").iloc[0]
    return StationContext(
        station_id=str(row["station_id"]),
        station_name=str(row["station_name"]),
        lat=float(row["lat"]),
        lng=float(row["lng"]),
        corridor=str(row["corridor"]),
        corridor_type=str(row.get("corridor_type", "local")),
        station_role=str(row.get("station_role", "standard")),
        is_terminal=int(row["is_terminal"]),
        is_interchange=int(row["is_interchange"]),
        station_importance=int(row["station_importance"]),
        busy_factor=float(row["busy_factor"]),
        route_overlap_count=int(row.get("route_overlap_count", 1)),
        transfer_score=int(row.get("transfer_score", 2)),
        land_use_type=str(row.get("land_use_type", "mixed")),
        near_market=int(row["near_market"]),
        near_business_district=int(row["near_business_district"]),
    )


def fetch_tomtom_flow(lat: float, lng: float) -> dict[str, Any]:
    api_key = os.getenv("TOMTOM_API_KEY")
    if not api_key:
        raise RuntimeError("TOMTOM_API_KEY is not set.")

    def neutral_flow() -> dict[str, Any]:
        return {
            "current_speed": 30.0,
            "free_flow_speed": 30.0,
            "current_travel_time": 0.0,
            "free_flow_travel_time": 0.0,
            "traffic_confidence": 0.0,
            "road_closure": False,
        }

    try:
        response = requests.get(
            "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json",
            params={"point": f"{lat},{lng}", "unit": "KMPH", "openLr": "false", "key": api_key},
            timeout=20,
        )
        if response.status_code == 400:
            return neutral_flow()
        response.raise_for_status()
        payload = response.json().get("flowSegmentData", {})
        return {
            "current_speed": float(payload.get("currentSpeed", 30.0)),
            "free_flow_speed": float(payload.get("freeFlowSpeed", 30.0)),
            "current_travel_time": float(payload.get("currentTravelTime", 0.0)),
            "free_flow_travel_time": float(payload.get("freeFlowTravelTime", 0.0)),
            "traffic_confidence": float(payload.get("confidence", 0.0)),
            "road_closure": bool(payload.get("roadClosure", False)),
        }
    except requests.RequestException:
        return neutral_flow()


def fetch_open_meteo(lat: float, lng: float) -> dict[str, Any]:
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lng,
            "current": "temperature_2m,precipitation,rain,cloud_cover",
            "timezone": "Africa/Lagos",
            "forecast_days": 1,
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json().get("current", {})
    return {
        "temperature_2m": float(payload.get("temperature_2m", 0.0)),
        "precipitation": float(payload.get("precipitation", 0.0)),
        "rain": float(payload.get("rain", 0.0)),
        "cloud_cover": float(payload.get("cloud_cover", 0.0)),
    }


def compute_traffic_pressure(current_speed: float, free_flow_speed: float) -> float:
    if free_flow_speed <= 0:
        return 0.0
    speed_ratio = max(0.0, min(1.2, current_speed / free_flow_speed))
    return max(0.0, min(1.0, 1.0 - speed_ratio))


def is_peak(hour: int, day_of_week: int) -> int:
    weekday = day_of_week <= 4
    return int((weekday and 6 <= hour <= 9) or (weekday and 16 <= hour <= 20))


def is_friday_evening(hour: int, day_of_week: int) -> int:
    return int(day_of_week == 4 and 17 <= hour <= 20)


def is_weekend_morning(hour: int, day_of_week: int) -> int:
    return int(day_of_week >= 5 and 6 <= hour <= 11)


def is_late_night(hour: int) -> int:
    return int(hour >= 23 or hour <= 4)


def compute_people_congestion_score(*, traffic_pressure: float, busy_factor: float, transfer_score: int, route_overlap_count: int, is_terminal: int, is_interchange: int, near_market: int, near_business_district: int, hour: int, day_of_week: int, rain: float) -> float:
    score = 0.0
    score += 0.24 * traffic_pressure
    score += 0.22 * max(0.0, min(1.0, busy_factor))
    score += 0.10 * is_terminal
    score += 0.08 * is_interchange
    score += 0.08 * min(route_overlap_count / 5.0, 1.0)
    score += 0.08 * min(transfer_score / 5.0, 1.0)
    score += 0.06 * near_market
    score += 0.06 * near_business_district
    score += 0.12 * is_peak(hour, day_of_week)
    score += 0.04 * is_friday_evening(hour, day_of_week)
    score -= 0.10 * is_weekend_morning(hour, day_of_week)
    score -= 0.12 * is_late_night(hour)
    score += 0.06 * min(rain / 10.0, 1.0)
    return max(0.0, min(1.0, score))


def score_to_label(score: float) -> str:
    if score >= 0.67:
        return "heavy"
    if score >= 0.40:
        return "moderate"
    return "flowing"


def build_observation(station: StationContext, *, hour: int | None = None, day_of_week: int | None = None, observed_at: datetime | None = None) -> dict[str, Any]:
    moment = observed_at or datetime.now(timezone.utc)
    local_hour = moment.astimezone().hour if hour is None else hour
    local_day = moment.astimezone().weekday() if day_of_week is None else day_of_week
    traffic = fetch_tomtom_flow(station.lat, station.lng)
    weather = fetch_open_meteo(station.lat, station.lng)
    traffic_pressure = compute_traffic_pressure(traffic["current_speed"], traffic["free_flow_speed"])
    score = compute_people_congestion_score(
        traffic_pressure=traffic_pressure,
        busy_factor=station.busy_factor,
        transfer_score=station.transfer_score,
        route_overlap_count=station.route_overlap_count,
        is_terminal=station.is_terminal,
        is_interchange=station.is_interchange,
        near_market=station.near_market,
        near_business_district=station.near_business_district,
        hour=local_hour,
        day_of_week=local_day,
        rain=weather["rain"],
    )
    return {
        "station_id": station.station_id,
        "station_name": station.station_name,
        "lat": station.lat,
        "lng": station.lng,
        "corridor": station.corridor,
        "corridor_type": station.corridor_type,
        "station_role": station.station_role,
        "is_terminal": station.is_terminal,
        "is_interchange": station.is_interchange,
        "station_importance": station.station_importance,
        "busy_factor": station.busy_factor,
        "route_overlap_count": station.route_overlap_count,
        "transfer_score": station.transfer_score,
        "land_use_type": station.land_use_type,
        "near_market": station.near_market,
        "near_business_district": station.near_business_district,
        "timestamp_utc": moment.isoformat(),
        "hour": local_hour,
        "day_of_week": local_day,
        "is_weekend": int(local_day >= 5),
        "current_speed": traffic["current_speed"],
        "free_flow_speed": traffic["free_flow_speed"],
        "current_travel_time": traffic["current_travel_time"],
        "free_flow_travel_time": traffic["free_flow_travel_time"],
        "traffic_confidence": traffic["traffic_confidence"],
        "traffic_pressure": traffic_pressure,
        "temperature_2m": weather["temperature_2m"],
        "precipitation": weather["precipitation"],
        "rain": weather["rain"],
        "cloud_cover": weather["cloud_cover"],
        "crowd_score": score,
        "label": score_to_label(score),
    }


def append_observations(frame: pd.DataFrame) -> None:
    ensure_data_dir()
    frame.to_csv(OBSERVATIONS_FILE, mode="a", index=False, header=not OBSERVATIONS_FILE.exists())


def collect_station_snapshot(hour: int | None = None, day_of_week: int | None = None) -> pd.DataFrame:
    stations = load_stations()
    rows: list[dict[str, Any]] = []
    for station_row in stations.to_dict("records"):
        station = StationContext(
            station_id=str(station_row["station_id"]),
            station_name=str(station_row["station_name"]),
            lat=float(station_row["lat"]),
            lng=float(station_row["lng"]),
            corridor=str(station_row["corridor"]),
            corridor_type=str(station_row.get("corridor_type", "local")),
            station_role=str(station_row.get("station_role", "standard")),
            is_terminal=int(station_row["is_terminal"]),
            is_interchange=int(station_row["is_interchange"]),
            station_importance=int(station_row["station_importance"]),
            busy_factor=float(station_row.get("busy_factor", station_row["station_importance"] / 5)),
            route_overlap_count=int(station_row.get("route_overlap_count", 1)),
            transfer_score=int(station_row.get("transfer_score", 2)),
            land_use_type=str(station_row.get("land_use_type", "mixed")),
            near_market=int(station_row["near_market"]),
            near_business_district=int(station_row["near_business_district"]),
        )
        rows.append(build_observation(station, hour=hour, day_of_week=day_of_week))
    frame = pd.DataFrame(rows)
    append_observations(frame)
    return frame


def load_observations() -> pd.DataFrame:
    if not OBSERVATIONS_FILE.exists():
        return pd.DataFrame()
    return pd.read_csv(OBSERVATIONS_FILE)


def build_training_dataset(min_rows: int = 200) -> pd.DataFrame:
    observations = load_observations()
    if observations.empty:
        observations = collect_station_snapshot()
    dataset = observations.copy()
    if len(dataset) < min_rows:
        expanded_rows: list[dict[str, Any]] = []
        hours = [6, 8, 12, 15, 17, 20, 23]
        day_bands = [0, 2, 4, 5, 6]
        for row in dataset.to_dict("records"):
            for sample_hour in hours:
                for sample_day in day_bands:
                    clone = dict(row)
                    clone["hour"] = sample_hour
                    clone["day_of_week"] = sample_day
                    clone["is_weekend"] = int(sample_day >= 5)
                    score = compute_people_congestion_score(
                        traffic_pressure=float(clone["traffic_pressure"]),
                        busy_factor=float(clone["busy_factor"]),
                        transfer_score=int(clone["transfer_score"]),
                        route_overlap_count=int(clone["route_overlap_count"]),
                        is_terminal=int(clone["is_terminal"]),
                        is_interchange=int(clone["is_interchange"]),
                        near_market=int(clone["near_market"]),
                        near_business_district=int(clone["near_business_district"]),
                        hour=sample_hour,
                        day_of_week=sample_day,
                        rain=float(clone["rain"]),
                    )
                    clone["crowd_score"] = score
                    clone["label"] = score_to_label(score)
                    expanded_rows.append(clone)
        dataset = pd.concat([dataset, pd.DataFrame(expanded_rows)], ignore_index=True)
    ensure_data_dir()
    dataset.to_csv(TRAINING_DATA_FILE, index=False)
    return dataset
