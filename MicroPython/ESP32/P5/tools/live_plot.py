#!/usr/bin/env python3
"""
Live plot para Práctica 5 (BMP280)

Lee por puerto serie un flujo CSV con encabezado:
    timestamp_ms,temp_C,press_hPa,press_kPa,altitude_m

y grafica en tiempo real temperatura (°C), presión (hPa) y altitud (m).

Requisitos: pyserial, matplotlib
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
except Exception as e:
    print("[Error] Falta pyserial. Instala dependencias con 'pip install -r requirements.txt'.")
    raise


def autodetect_port(prefer_substrings=("USB", "UART", "Silicon", "CP210", "CH340", "FTDI")):
    ports = list(list_ports.comports())
    if not ports:
        return None
    # Preferir puertos con ciertas palabras clave
    for p in ports:
        desc = f"{p.device} {p.description} {p.hwid}"
        if any(s in desc for s in prefer_substrings):
            return p.device
    # Si no hubo coincidencia, devolver el primero
    return ports[0].device


def open_serial(port=None, baud=115200, timeout=1.0):
    if port is None:
        port = autodetect_port()
        if port:
            print(f"[Serie] Puerto auto-detectado: {port}")
        else:
            print("[Serie] No se pudo detectar el puerto. Indica uno con --port.")
            sys.exit(1)
    ser = serial.Serial(port=port, baudrate=baud, timeout=timeout)
    # Pequeña espera para estabilizar
    time.sleep(0.2)
    # Limpiar buffer inicial
    ser.reset_input_buffer()
    return ser


def parse_header(line):
    # Normalizar y dividir encabezado
    fields = [f.strip() for f in line.strip().split(',')]
    expected = {"timestamp_ms", "temp_C", "press_hPa", "press_kPa", "altitude_m"}
    if not set(fields).issuperset(expected):
        raise ValueError(f"Encabezado inesperado: {fields}")
    # Posiciones por nombre (permite reorden)
    idx = {name: fields.index(name) for name in expected}
    return fields, idx


def read_csv_stream(ser, alt_zero=False):
    """Generador que rinde tuplas (t_ms, temp_C, press_hPa, altitude_m)."""
    # Leer encabezado
    header = ser.readline().decode(errors='ignore').strip()
    while header == '':
        header = ser.readline().decode(errors='ignore').strip()
    fields, idx = parse_header(header)
    print(f"[CSV] Encabezado: {fields}")

    alt_offset = None

    while True:
        line = ser.readline().decode(errors='ignore').strip()
        if not line:
            continue
        parts = line.split(',')
        if len(parts) < 5:
            # a veces llega basura; ignorar
            continue
        try:
            t_ms = float(parts[idx['timestamp_ms']])
            temp_C = float(parts[idx['temp_C']])
            press_hPa = float(parts[idx['press_hPa']])
            altitude_m = float(parts[idx['altitude_m']])
        except Exception:
            continue

        if alt_zero:
            if alt_offset is None:
                alt_offset = altitude_m
            altitude_m = altitude_m - alt_offset

        yield t_ms, temp_C, press_hPa, altitude_m


def main(argv=None):
    parser = argparse.ArgumentParser(description="Live plot BMP280 (P5)")
    parser.add_argument("--port", help="Puerto serie (e.g., COM5 o /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200, help="Baudrate (default 115200)")
    parser.add_argument("--window", type=float, default=60.0, help="Ventana de tiempo (s) para la gráfica")
    parser.add_argument("--save", help="Guardar CSV recibido en un archivo")
    parser.add_argument("--alt-zero", action="store_true", help="Tomar la primera altitud como cero relativo")
    args = parser.parse_args(argv)

    ser = open_serial(args.port, args.baud)

    # Buffers deslizantes
    maxlen = int(args.window * 10)  # ~10 muestras/s a 500 ms — tamaño aproximado
    t_buf = deque(maxlen=maxlen)
    temp_buf = deque(maxlen=maxlen)
    press_buf = deque(maxlen=maxlen)
    alt_buf = deque(maxlen=maxlen)

    # Guardado opcional
    writer = None
    fcsv = None
    if args.save:
        fcsv = open(args.save, 'w', newline='')
        writer = csv.writer(fcsv)
        writer.writerow(["timestamp_ms", "temp_C", "press_hPa", "altitude_m"])  # sin kPa (redundante)

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(9, 7), sharex=True)
    ax1.set_ylabel('Temp (°C)'); ax1.grid(True)
    ax2.set_ylabel('Presión (hPa)'); ax2.grid(True)
    ax3.set_ylabel('Altitud (m)'); ax3.set_xlabel('Tiempo (s)'); ax3.grid(True)

    line1, = ax1.plot([], [], color='tab:blue')
    line2, = ax2.plot([], [], color='tab:orange')
    line3, = ax3.plot([], [], color='tab:green')

    start_t = None

    stream = read_csv_stream(ser, alt_zero=args.alt_zero)

    def update(_):
        nonlocal start_t
        # Leer algunas muestras por cuadro para fluidez
        for _ in range(5):
            try:
                t_ms, temp_C, press_hPa, alt_m = next(stream)
            except StopIteration:
                break
            except Exception:
                break

            if start_t is None:
                start_t = t_ms
            t_s = (t_ms - start_t) / 1000.0

            t_buf.append(t_s)
            temp_buf.append(temp_C)
            press_buf.append(press_hPa)
            alt_buf.append(alt_m)

            if writer:
                writer.writerow([int(t_ms), f"{temp_C:.2f}", f"{press_hPa:.2f}", f"{alt_m:.2f}"])

        if len(t_buf) >= 2:
            # Actualizar datos
            line1.set_data(t_buf, temp_buf)
            line2.set_data(t_buf, press_buf)
            line3.set_data(t_buf, alt_buf)

            # Ajustar ejes a la ventana
            tmin = max(0.0, t_buf[-1] - args.window)
            ax1.set_xlim(tmin, tmin + args.window)
            for ax in (ax1, ax2, ax3):
                ymin, ymax = None, None
                buf = temp_buf if ax is ax1 else press_buf if ax is ax2 else alt_buf
                if buf:
                    ymin = min(buf)
                    ymax = max(buf)
                    if ymax - ymin < 1e-6:
                        ymin -= 1.0
                        ymax += 1.0
                    pad = 0.05 * (ymax - ymin)
                    ax.set_ylim(ymin - pad, ymax + pad)

        return line1, line2, line3

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


if __name__ == "__main__":
    main()
