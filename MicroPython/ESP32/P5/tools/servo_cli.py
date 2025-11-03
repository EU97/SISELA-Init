#!/usr/bin/env python3
"""
CLI sencillo para enviar ángulos o pulsos al modo 2/3 del firmware
por el puerto serie (REPL). Requiere que el ESP32 esté ejecutando
el modo correspondiente y esperando números por stdin.

Ejemplos:
  python servo_cli.py --port COM5 angle 90
  python servo_cli.py --port COM5 sweep --min 0 --max 180 --step 5 --delay 0.05
  python servo_cli.py --port COM5 pulse 1500
"""
import argparse
import sys
import time

try:
    import serial  # pyserial
except ImportError:
    print("Este script requiere pyserial: pip install pyserial")
    sys.exit(1)


def send_line(ser, s):
    if not s.endswith("\n"):
        s += "\n"
    ser.write(s.encode("ascii"))
    ser.flush()


def main():
    parser = argparse.ArgumentParser(description="CLI para control de servo por serie")
    parser.add_argument("--port", required=True, help="Puerto serie (ej. COM5, /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200, help="Baudrate (115200 por defecto)")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_angle = sub.add_parser("angle", help="Enviar ángulo único (0–180)")
    p_angle.add_argument("value", type=int)

    p_pulse = sub.add_parser("pulse", help="Enviar pulso único (us)")
    p_pulse.add_argument("micros", type=int)

    p_sweep = sub.add_parser("sweep", help="Barrido de ángulos")
    p_sweep.add_argument("--min", type=int, default=0)
    p_sweep.add_argument("--max", type=int, default=180)
    p_sweep.add_argument("--step", type=int, default=5)
    p_sweep.add_argument("--delay", type=float, default=0.05)

    args = parser.parse_args()

    with serial.Serial(args.port, args.baud, timeout=0.2) as ser:
        time.sleep(0.2)  # estabilizar
        if args.cmd == "angle":
            send_line(ser, str(args.value))
        elif args.cmd == "pulse":
            send_line(ser, str(args.micros))
        elif args.cmd == "sweep":
            rng = range(args.min, args.max + 1, args.step)
            for a in list(rng) + list(reversed(list(rng))):
                send_line(ser, str(a))
                time.sleep(args.delay)
        else:
            parser.error("Comando no reconocido")


if __name__ == "__main__":
    main()
