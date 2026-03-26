import argparse
import time
from datetime import datetime

from data import collect_station_snapshot


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect station snapshots on a repeating interval.")
    parser.add_argument("--interval-minutes", type=int, default=30, help="Minutes to wait between snapshots")
    parser.add_argument("--runs", type=int, default=48, help="How many snapshots to collect before stopping")
    args = parser.parse_args()

    for run in range(1, args.runs + 1):
        now = datetime.now()
        frame = collect_station_snapshot()
        print(f"[{now:%Y-%m-%d %H:%M:%S}] Run {run}/{args.runs}: collected {len(frame)} station observations")
        if run < args.runs:
            time.sleep(args.interval_minutes * 60)
