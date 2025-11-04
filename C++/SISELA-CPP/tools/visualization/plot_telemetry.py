#!/usr/bin/env python3
"""
Plot telemetry CSV (timestamp, altitude, speed, attitude, light, ...)
Usage:
  python plot_telemetry.py path/to/log_telemetry.csv
"""
import sys
import csv
from pathlib import Path

try:
    import matplotlib.pyplot as plt
except Exception as e:
    print("matplotlib requerido: pip install matplotlib", file=sys.stderr)
    raise


def main(path: Path):
    t, altitude, speed, attitude, light = [], [], [], [], []
    with path.open() as f:
        r = csv.DictReader(f)
        for row in r:
            t.append(float(row.get("timestamp", len(t))))
            altitude.append(float(row.get("altitude", 0)))
            speed.append(float(row.get("speed", 0)))
            attitude.append(float(row.get("attitude", 0)))
            light.append(float(row.get("light", 0)))

    fig, axs = plt.subplots(4, 1, sharex=True, figsize=(9, 8))
    axs[0].plot(t, altitude); axs[0].set_ylabel("Altitude")
    axs[1].plot(t, speed);    axs[1].set_ylabel("Speed")
    axs[2].plot(t, attitude); axs[2].set_ylabel("Attitude")
    axs[3].plot(t, light);    axs[3].set_ylabel("Light"); axs[3].set_xlabel("Time (s)")
    fig.suptitle("SISELA Telemetry")
    plt.tight_layout(); plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python plot_telemetry.py path/to/log_telemetry.csv", file=sys.stderr)
        sys.exit(2)
    main(Path(sys.argv[1]))
