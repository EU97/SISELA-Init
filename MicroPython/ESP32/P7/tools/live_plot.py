#!/usr/bin/env python3
"""
Live plot P7 — Grafica raw vs MA vs EMA desde CSV:
  timestamp_ms,raw,ma,ema
"""
import argparse
import csv
import sys
import time
from collections import deque

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

try:
    import serial
    from serial.tools import list_ports
except Exception:
    print("[Error] Falta pyserial. Instalar con 'pip install pyserial'.")
    raise


def autodetect_port():
    ports = list(list_ports.comports())
    if not ports:
        return None
    # heurística simple
    for p in ports:
        desc = f"{p.device} {p.description} {p.hwid}"
        for key in ("USB", "UART", "CP210", "CH340", "FTDI"):
            if key in desc:
                return p.device
    return ports[0].device


def open_serial(port=None, baud=115200, timeout=1.0):
    if port is None:
        port = autodetect_port()
        if port:
            print(f"[Serie] Auto: {port}")
        else:
            print("[Serie] No detectado. Usa --port COMx")
            sys.exit(1)
    ser = serial.Serial(port=port, baudrate=baud, timeout=timeout)
    time.sleep(0.2)
    ser.reset_input_buffer()
    return ser


def parse_header(line):
    fields = [f.strip() for f in line.strip().split(',')]
    expected = {"timestamp_ms", "raw", "ma", "ema"}
    if not set(fields).issuperset(expected):
        raise ValueError(f"Encabezado inesperado: {fields}")
    idx = {name: fields.index(name) for name in expected}
    return fields, idx


def read_stream(ser):
    # leer encabezado
    header = ser.readline().decode(errors='ignore').strip()
    while header == '':
        header = ser.readline().decode(errors='ignore').strip()
    fields, idx = parse_header(header)
    print(f"[CSV] {fields}")

    while True:
        line = ser.readline().decode(errors='ignore').strip()
        if not line:
            continue
        parts = line.split(',')
        if len(parts) < 4:
            continue
        try:
            t_ms = float(parts[idx['timestamp_ms']])
            raw = float(parts[idx['raw']])
            ma = float(parts[idx['ma']])
            ema = float(parts[idx['ema']])
        except Exception:
            continue
        yield t_ms, raw, ma, ema


def main(argv=None):
    p = argparse.ArgumentParser(description="Plot P7 raw/MA/EMA")
    p.add_argument('--port')
    p.add_argument('--baud', type=int, default=115200)
    p.add_argument('--window', type=float, default=60)
    p.add_argument('--save')
    args = p.parse_args(argv)

    ser = open_serial(args.port, args.baud)

    maxlen = int(args.window * 10)
    tbuf = deque(maxlen=maxlen)
    rbuf = deque(maxlen=maxlen)
    mabuf = deque(maxlen=maxlen)
    emabuf = deque(maxlen=maxlen)

    writer = None
    fcsv = None
    if args.save:
        fcsv = open(args.save, 'w', newline='')
        writer = csv.writer(fcsv)
        writer.writerow(['timestamp_ms', 'raw', 'ma', 'ema'])

    fig, ax = plt.subplots(1, 1, figsize=(9, 4))
    lraw, = ax.plot([], [], label='raw', color='tab:gray', alpha=0.6)
    lma, = ax.plot([], [], label='MA', color='tab:blue')
    lema, = ax.plot([], [], label='EMA', color='tab:orange')
    ax.set_xlabel('Tiempo (s)')
    ax.set_ylabel('Valor')
    ax.grid(True)
    ax.legend(loc='upper right')

    start = None
    stream = read_stream(ser)

    def update(_):
        nonlocal start
        for _ in range(5):
            try:
                t_ms, raw, ma, ema = next(stream)
            except StopIteration:
                break
            except Exception:
                break
            if start is None:
                start = t_ms
            t_s = (t_ms - start) / 1000.0
            tbuf.append(t_s)
            rbuf.append(raw)
            mabuf.append(ma)
            emabuf.append(ema)
            if writer:
                writer.writerow([int(t_ms), f"{raw:.3f}", f"{ma:.3f}", f"{ema:.3f}"])
        if len(tbuf) >= 2:
            lraw.set_data(tbuf, rbuf)
            lma.set_data(tbuf, mabuf)
            lema.set_data(tbuf, emabuf)
            tmin = max(0.0, tbuf[-1] - args.window)
            ax.set_xlim(tmin, tmin + args.window)
            ymin = min(min(rbuf), min(mabuf), min(emabuf))
            ymax = max(max(rbuf), max(mabuf), max(emabuf))
            pad = 0.05 * (ymax - ymin or 1.0)
            ax.set_ylim(ymin - pad, ymax + pad)
        return lraw, lma, lema

    ani = FuncAnimation(fig, update, interval=100)
    plt.tight_layout()
    try:
        plt.show()
    finally:
        try:
            ser.close()
        except Exception:
            pass
        if fcsv:
            fcsv.close()

if __name__ == '__main__':
    main()
