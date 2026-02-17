#!/usr/bin/env python3
"""
"""Live plotter for ESP32/RP2040 ADC CSV output (P2).

Reads CSV lines from the serial port and plots a selected column vs t_ms
in real time using matplotlib.

Supported CSV formats (auto-detected from header):
  Compact:  t_ms,raw,avg,voltage_v,angle_deg
  Extended: t_ms,raw,avg,voltage_v,angle_deg,flap_deg,ssm,arinc_hex

Usage (Windows PowerShell):
  python .\live_plot.py --port COM3 --baud 115200 --y voltage_v
  python .\live_plot.py --port COM3 --baud 115200 --y flap_deg

Install deps:
  python -m pip install -r requirements.txt
"""
from __future__ import annotations
import argparse
import threading
import time
from collections import deque
from typing import Deque, Dict, List, Optional

import matplotlib.pyplot as plt
import serial

# -------- Args --------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Live plot from ESP32 CSV over serial")
    p.add_argument("--port", required=True, help="Serial port (e.g., COM3)")
    p.add_argument("--baud", type=int, default=115200, help="Baudrate (default: 115200)")
    p.add_argument("--y", default="voltage_v",
                   choices=["raw", "avg", "voltage_v", "angle_deg", "flap_deg"],
                   help="Y variable to plot vs t_ms (flap_deg requires extended CSV)")
    p.add_argument("--window", type=int, default=1000, help="Plot window in ms (time range visible)")
    p.add_argument("--max-points", type=int, default=2000, help="Max points to keep in memory (ring buffer)")
    p.add_argument("--no-header", action="store_true", help="If set, do not expect a header line")
    p.add_argument("--timeout", type=float, default=0.05, help="Serial read timeout (s)")
    return p.parse_args()

# -------- Serial reader thread --------

class SerialReader(threading.Thread):
    def __init__(self, port: str, baud: int, expect_header: bool, timeout: float = 0.05) -> None:
        super().__init__(daemon=True)
        self.port = port
        self.baud = baud
        self.expect_header = expect_header
        self.timeout = timeout
        self.stop_flag = threading.Event()
        self.ser: Optional[serial.Serial] = None
        self.header_map: Dict[str, int] = {}
        self.buffer: Deque[Dict[str, float]] = deque(maxlen=5000)

    def run(self) -> None:
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
            # Small delay to allow device to reset (common on Windows)
            time.sleep(0.5)
        except Exception as e:
            print(f"[ERR] Cannot open serial port {self.port}: {e}")
            return

        # Try to synchronize with header
        if self.expect_header:
            self._read_header_blocking()

        while not self.stop_flag.is_set():
            try:
                line = self.ser.readline().decode(errors="ignore").strip()
                if not line:
                    continue
                # Accept header reprints gracefully
                if self._maybe_parse_header(line):
                    continue
                row = self._parse_row(line)
                if row:
                    self.buffer.append(row)
            except Exception:
                # Avoid crashing on transient decode/parse errors
                continue

        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass

    def _read_header_blocking(self) -> None:
        # Wait for a header; ignore empty lines
        deadline = time.time() + 3.0
        while time.time() < deadline and not self.stop_flag.is_set():
            line = self.ser.readline().decode(errors="ignore").strip()
            if not line:
                continue
            if self._maybe_parse_header(line):
                return
        # If no header, leave header_map empty; will try parse rows anyway

    def _maybe_parse_header(self, line: str) -> bool:
        # Expected: t_ms,raw,avg,voltage_v,angle_deg
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2 and parts[0] == "t_ms":
            self.header_map = {name: idx for idx, name in enumerate(parts)}
            return True
        return False

    def _parse_row(self, line: str) -> Optional[Dict[str, float]]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 5:
            return None
        try:
            if self.header_map:
                row: Dict[str, float] = {}
                for name, idx in self.header_map.items():
                    if idx < len(parts):
                        val = parts[idx]
                        # Skip non-numeric columns (ssm, arinc_hex)
                        if name in ("ssm", "arinc_hex"):
                            continue
                        row[name] = float(val)
                return row if "t_ms" in row else None
            else:
                # Fallback fixed order (compact format)
                return {
                    "t_ms": float(parts[0]),
                    "raw": float(parts[1]),
                    "avg": float(parts[2]),
                    "voltage_v": float(parts[3]),
                    "angle_deg": float(parts[4]),
                }
        except Exception:
            return None

    def stop(self) -> None:
        self.stop_flag.set()

# -------- Plotting --------

def main() -> None:
    args = parse_args()

    reader = SerialReader(args.port, args.baud, expect_header=(not args.no_header), timeout=args.timeout)
    reader.start()

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.set_title(f"ADC Live: {args.y} vs t_ms @ {args.baud}baud")
    ax.set_xlabel("t (ms)")
    ax.set_ylabel(args.y)

    xdata: Deque[float] = deque(maxlen=args.max_points)
    ydata: Deque[float] = deque(maxlen=args.max_points)
    (line,) = ax.plot([], [], lw=1.5)

    y_key = args.y
    t_window = max(100, int(args.window))

    def update_plot(_frame: int):
        # Drain buffer efficiently
        while reader.buffer:
            row = reader.buffer.popleft()
            t_val = row.get("t_ms")
            y_val = row.get(y_key)
            if t_val is not None and y_val is not None:
                xdata.append(t_val)
                ydata.append(y_val)

        if not xdata:
            return line,

        t_max = xdata[-1]
        t_min = max(0, t_max - t_window)

        # Drop old points out of window for speed
        while xdata and xdata[0] < t_min:
            xdata.popleft()
            ydata.popleft()

        line.set_data(list(xdata), list(ydata))
        ax.set_xlim(t_min, t_min + t_window)

        # Auto-scale Y to recent window (with small margin)
        if ydata:
            y_min = min(ydata); y_max = max(ydata)
            if y_min == y_max:
                y_min -= 0.5; y_max += 0.5
            margin = 0.05 * (y_max - y_min)
            ax.set_ylim(y_min - margin, y_max + margin)
        return line,

    timer = fig.canvas.new_timer(interval=30)  # ~33 FPS
    timer.add_callback(lambda: update_plot(0))
    timer.start()

    try:
        plt.show()
    finally:
        reader.stop()
        reader.join(timeout=1.0)


if __name__ == "__main__":
    main()
