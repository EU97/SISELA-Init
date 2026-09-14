"""
capture — adquisición del stream CSV del microcontrolador por puerto serie.

Reutiliza el patrón de arranque de MicroPython/ESP32/P4/tools/altimeter_gui.py:
abre el puerto, opcionalmente envía la opción de menú para entrar en un modo de
análisis, y recolecta las líneas CSV que emite `siglab.stream_csv()` en el firmware.

Uso programático:
    from sisela_signal.capture import capture_serial
    cap = capture_serial("/dev/ttyUSB0", menu="6", seconds=5)
    print(cap.summary())

Uso CLI:
    python -m sisela_signal capture --port /dev/ttyUSB0 --menu 6 --seconds 5 --out cap.csv
"""

from __future__ import annotations

import sys
import time

from .dataio import Capture, from_rows

try:
    import serial
    import serial.tools.list_ports
    HAVE_SERIAL = True
except ImportError:  # pragma: no cover
    serial = None
    HAVE_SERIAL = False


def autodetect_port() -> str | None:
    if not HAVE_SERIAL:
        return None
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        d = (p.description or "").lower()
        if any(k in d for k in ("cp210", "ch340", "ch910", "uart", "usb serial", "pico", "usbmodem")):
            return p.device
    return ports[0].device if ports else None


def _looks_like_data(line: str) -> bool:
    s = line.strip()
    if not s or s[0] in "#=[-":
        return False
    head = s.split(",")[0]
    try:
        float(head)
        return True
    except ValueError:
        return False


def capture_serial(port: str | None = None, baud: int = 115200, menu: str | None = None,
                   seconds: float = 5.0, max_lines: int | None = None,
                   fs_nominal: float | None = None, no_reset: bool = False,
                   quiet: bool = False) -> Capture:
    """
    Captura un bloque CSV del MCU.

    port       : puerto serie (autodetecta si None)
    menu       : opción(es) de menú a enviar tras conectar para entrar al modo
                 (p.ej. "6" o "6\\n30000\\n" para modo + parámetros)
    seconds    : duración de la captura
    max_lines  : detiene la captura tras N filas de datos
    fs_nominal : Fs solicitada al firmware (para reportar error de Fs)
    """
    if not HAVE_SERIAL:  # pragma: no cover
        raise ImportError("pyserial no está instalado. pip install pyserial")

    port = port or autodetect_port()
    if not port:
        raise RuntimeError("No se detectó ningún puerto serie. Usa --port.")

    ser = serial.Serial(port, baud, timeout=0.3)
    try:
        if no_reset:
            try:
                ser.dtr = False
                ser.rts = False
            except Exception:
                pass
        time.sleep(2.0)
        try:
            ser.reset_input_buffer()
        except Exception:
            pass

        if menu:
            for token in menu.replace("\\n", "\n").split("\n"):
                ser.write((token + "\r\n").encode())
                ser.flush()
                time.sleep(0.35)

        header = None
        rows: list[list[str]] = []
        t_end = time.time() + seconds
        if not quiet:
            print(f"[capture] {port} @ {baud}  menu={menu!r}  ({seconds:g} s)...", file=sys.stderr)

        while time.time() < t_end:
            raw = ser.readline().decode("utf-8", errors="ignore").strip()
            if not raw:
                continue
            if header is None and "," in raw and not _looks_like_data(raw):
                # posible encabezado: >=2 campos y no numérico
                parts = [p.strip() for p in raw.split(",")]
                if len(parts) >= 2 and any(not _isfloat(p) for p in parts):
                    header = parts
                    continue
            if _looks_like_data(raw):
                if header is None:
                    n = len(raw.split(","))
                    header = ["t_us"] + [f"ch{i}" for i in range(n - 1)]
                rows.append([p.strip() for p in raw.split(",")])
                if max_lines and len(rows) >= max_lines:
                    break

        # devolver el firmware al menú
        try:
            ser.write(b"m\r\n")
            ser.flush()
        except Exception:
            pass
    finally:
        ser.close()

    if not rows:
        raise RuntimeError("No se recibió ninguna fila CSV. ¿Modo correcto? ¿baudrate?")
    if not quiet:
        print(f"[capture] {len(rows)} filas, columnas={header}", file=sys.stderr)
    return from_rows(header, rows, fs_nominal=fs_nominal)


def _isfloat(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False
