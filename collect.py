import argparse

from data import collect_station_snapshot


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect one live snapshot for all stations.")
    parser.add_argument("--hour", type=int, default=None, help="Override hour for label expansion context")
    parser.add_argument("--day-of-week", type=int, default=None, help="Override day of week (0=Mon ... 6=Sun)")
    args = parser.parse_args()

    frame = collect_station_snapshot(hour=args.hour, day_of_week=args.day_of_week)
    print(f"Collected {len(frame)} station observations")
    print(frame[["station_name", "hour", "day_of_week", "traffic_pressure", "label"]].head(10).to_string(index=False))
