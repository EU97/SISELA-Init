"""
live — vista en vivo (matplotlib) del stream CSV que emite el firmware por serie.

Genérico y compartido entre prácticas: sirve para CUALQUIER práctica cuyo firmware,
sea MicroPython (`siglab.stream_csv()`) o C++ (`siglab::streamCsv()`/impresión
directa por `serialPrintf`), emita líneas `t_us,col1[,col2,...]` por el puerto
serie. No depende de qué lenguaje generó el firmware — solo del formato CSV, que
es idéntico en ambos (ver `dataio.py`).

Uso CLI:
    python -m sisela_signal live --port COM5 --menu 5 --cols duty_pct,adc_raw
    python -m sisela_signal live --port COM5 --menu 6 --cols dt_us --window 10
    python -m sisela_signal live --port COM5 --menu 9\\n2   # auto-detecta columnas

Uso programático:
    from sisela_signal.live import live_plot
    live_plot(port="COM5", menu="5", cols=["duty_pct", "adc_raw"])
"""

from __future__ import annotations

import sys
import time as _time
from collections import deque

from .capture import autodetect_port, HAVE_SERIAL, _looks_like_data

try:
    import serial
except ImportError:  # pragma: no cover
    serial = None

try:
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    HAVE_MPL = True
except ImportError:  # pragma: no cover
    HAVE_MPL = False


def _parse_row(raw: str, col_idx: list[int]) -> tuple[float, list[float]] | None:
    """Parsea una línea CSV `t_us,v0,v1,...` y extrae `t_us` + las columnas en
    `col_idx`. Devuelve None si la línea no es una fila de datos válida."""
    if not _looks_like_data(raw):
        return None
    parts = raw.split(",")
    try:
        t_us = float(parts[0])
        vals = [float(parts[i]) for i in col_idx]
    except (ValueError, IndexError):
        return None
    return t_us, vals


def _open_and_arm(port, baud, menu, no_reset, header_timeout=8.0):
    """Abre el puerto, envía el menú y bloquea brevemente hasta leer el
    encabezado CSV (o agota `header_timeout`). Devuelve (ser, header)."""
    ser = serial.Serial(port, baud, timeout=0.3)
    if no_reset:
        try:
            ser.dtr = False
            ser.rts = False
        except Exception:
            pass
    _time.sleep(2.0)
    try:
        ser.reset_input_buffer()
    except Exception:
        pass
    if menu:
        for token in menu.replace("\\n", "\n").split("\n"):
            ser.write((token + "\r\n").encode())
            ser.flush()
            _time.sleep(0.35)

    header = None
    t_end = _time.time() + header_timeout
    while _time.time() < t_end:
        raw = ser.readline().decode("utf-8", errors="ignore").strip()
        if not raw:
            continue
        if "," in raw and not _looks_like_data(raw):
            header = [p.strip() for p in raw.split(",")]
            break
    return ser, header


def live_plot(port: str | None = None, baud: int = 115200, menu: str | None = None,
              cols: list[str] | None = None, window: float = 20.0,
              save: str | None = None, no_reset: bool = False,
              max_points: int = 4000) -> None:
    """
    Grafica en tiempo real las columnas `cols` (o todas si no se especifica) del
    stream CSV `t_us,col1[,col2,...]` del puerto serie.

    port    : puerto serie (autodetecta si None)
    menu    : opción(es) de menú a enviar tras conectar (p.ej. "5" o "9\\n2")
    cols    : nombres de columnas a graficar (una gráfica por columna); si None,
              se usan todas las columnas del encabezado recibido
    window  : ventana de tiempo visible (s)
    save    : si se indica, guarda también el CSV recibido en este archivo
    no_reset: evita el reset DTR/RTS al conectar (algunas placas no lo necesitan)
    """
    if not HAVE_SERIAL:
        raise ImportError("pyserial no está instalado. pip install pyserial")
    if not HAVE_MPL:
        raise ImportError("matplotlib no está instalado. pip install matplotlib")

    port = port or autodetect_port()
    if not port:
        raise RuntimeError("No se detectó ningún puerto serie. Usa --port.")

    print(f"[live] {port} @ {baud}  menu={menu!r} — esperando encabezado CSV...",
          file=sys.stderr)
    ser, header = _open_and_arm(port, baud, menu, no_reset)
    if header is None:
        ser.close()
        raise RuntimeError(
            "No se recibió un encabezado CSV a tiempo. ¿El --menu selecciona un "
            "modo que emite CSV? ¿baudrate correcto?"
        )
    print(f"[live] encabezado: {header}", file=sys.stderr)

    names = [c for c in cols if c in header] if cols else header[1:]
    if not names:
        names = header[1:]
    col_idx = [header.index(c) for c in names]

    fcsv = open(save, "w", newline="") if save else None
    if fcsv:
        fcsv.write(",".join(header) + "\n")

    n = len(names)
    fig, axes = plt.subplots(n, 1, sharex=True, figsize=(9, 2.2 * n + 1))
    if n == 1:
        axes = [axes]
    lines = []
    for ax, name in zip(axes, names):
        ln, = ax.plot([], [])
        ax.set_ylabel(name)
        ax.grid(True)
        lines.append(ln)
    axes[-1].set_xlabel("Tiempo (s)")
    fig.suptitle(f"Vista en vivo — {port}  menu={menu!r}")
    fig.tight_layout()

    t_buf: deque = deque(maxlen=max_points)
    y_bufs = [deque(maxlen=max_points) for _ in names]
    state = {"t0": None}

    def _update(_frame):
        for _ in range(30):  # varias líneas por cuadro, para no quedar atrás
            raw = ser.readline().decode("utf-8", errors="ignore").strip()
            if not raw:
                break
            parsed = _parse_row(raw, col_idx)
            if parsed is None:
                continue
            t_us, vals = parsed
            if state["t0"] is None:
                state["t0"] = t_us
            t_s = (t_us - state["t0"]) / 1e6
            t_buf.append(t_s)
            for buf, v in zip(y_bufs, vals):
                buf.append(v)
            if fcsv:
                fcsv.write(raw + "\n")

        if t_buf:
            tmin = max(0.0, t_buf[-1] - window)
            for ln, buf, ax in zip(lines, y_bufs, axes):
                # recortar a la ventana visible
                xs = [t for t in t_buf if t >= tmin]
                ys = [v for t, v in zip(t_buf, buf) if t >= tmin]
                ln.set_data(xs, ys)
                ax.set_xlim(tmin, max(window, t_buf[-1]))
                if ys:
                    ymin, ymax = min(ys), max(ys)
                    pad = 0.1 * (ymax - ymin) if ymax > ymin else 1.0
                    ax.set_ylim(ymin - pad, ymax + pad)
        return lines

    ani = FuncAnimation(fig, _update, interval=100, cache_frame_data=False)
    try:
        plt.show()
    finally:
        try:
            ser.write(b"m\r\n")
            ser.flush()
        except Exception:
            pass
        ser.close()
        if fcsv:
            fcsv.close()
