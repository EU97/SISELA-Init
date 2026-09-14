"""
dataio — utilidades comunes de carga de datos y detección de frecuencia de muestreo.

Formato CSV canónico producido por el firmware SISELA (lib/siglab.py, common/siglab.h):

    t_us,ch0[,ch1,...]
    0,32768
    200,32790
    ...

`t_us` es una marca de tiempo monótona en microsegundos. A partir de ella se estima
la frecuencia de muestreo real (Fs) y el jitter de muestreo, sin asumir que el
microcontrolador respetó exactamente la Fs solicitada.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field

import numpy as np

# Nombres de columna de tiempo reconocidos (en cualquier caso), en orden de preferencia.
_TIME_KEYS = ("t_us", "t_ms", "timestamp_us", "timestamp_ms", "time_us", "time_ms", "t", "time")


@dataclass
class Capture:
    """Contenedor de una captura multicanal con base de tiempo uniforme estimada."""

    t: np.ndarray                      # tiempo en segundos (relativo, empieza en 0)
    channels: dict[str, np.ndarray]    # nombre -> muestras (float)
    fs: float                          # frecuencia de muestreo estimada [Hz]
    fs_nominal: float | None = None    # Fs solicitada al firmware, si se conoce
    jitter_s: float = 0.0              # desviación estándar de dt [s]
    dropouts: int = 0                  # nº de intervalos > 2x mediana (muestras perdidas)
    meta: dict = field(default_factory=dict)

    @property
    def n(self) -> int:
        first = next(iter(self.channels.values()))
        return len(first)

    def col(self, name: str | None = None) -> np.ndarray:
        """Devuelve un canal por nombre; si name es None, el primero disponible."""
        if name is None:
            return next(iter(self.channels.values()))
        if name in self.channels:
            return self.channels[name]
        # tolerancia: índice numérico o coincidencia parcial
        keys = list(self.channels)
        if name.isdigit() and int(name) < len(keys):
            return self.channels[keys[int(name)]]
        for k in keys:
            if name.lower() in k.lower():
                return self.channels[k]
        raise KeyError(f"Canal '{name}' no encontrado. Disponibles: {keys}")

    def summary(self) -> str:
        lines = [
            f"muestras     : {self.n}",
            f"duración      : {self.t[-1] - self.t[0]:.4f} s" if self.n > 1 else "duración      : 0 s",
            f"Fs estimada   : {self.fs:.2f} Hz",
        ]
        if self.fs_nominal:
            err = 100.0 * (self.fs - self.fs_nominal) / self.fs_nominal
            lines.append(f"Fs nominal    : {self.fs_nominal:.2f} Hz  (error {err:+.2f} %)")
        lines.append(f"jitter (σ dt) : {self.jitter_s * 1e6:.2f} µs")
        if self.dropouts:
            lines.append(f"dropouts      : {self.dropouts}")
        lines.append(f"canales       : {', '.join(self.channels)}")
        return "\n".join(lines)


def _time_scale(key: str) -> float:
    """Factor para pasar la columna de tiempo a segundos."""
    k = key.lower()
    if k.endswith("_ms") or k == "t_ms" or k.endswith("ms"):
        return 1e-3
    if k.endswith("_us") or k == "t_us" or k.endswith("us"):
        return 1e-6
    return 1.0  # se asume segundos


def estimate_fs(t_seconds: np.ndarray) -> tuple[float, float, int]:
    """
    Estima Fs, jitter (σ de dt) y nº de dropouts a partir de un vector de tiempo.

    Returns: (fs_hz, jitter_s, dropouts)
    """
    t = np.asarray(t_seconds, dtype=float)
    if t.size < 2:
        return (0.0, 0.0, 0)
    dt = np.diff(t)
    dt = dt[dt > 0]
    if dt.size == 0:
        return (0.0, 0.0, 0)
    med = float(np.median(dt))
    fs = 1.0 / med if med > 0 else 0.0
    jitter = float(np.std(dt))
    dropouts = int(np.count_nonzero(dt > 1.5 * med))
    return (fs, jitter, dropouts)


def from_rows(header: list[str], rows: list[list[str]], fs_nominal: float | None = None) -> Capture:
    """Construye un Capture a partir de encabezado + filas ya parseadas."""
    header = [h.strip() for h in header]
    cols = {name: [] for name in header}
    for row in rows:
        if len(row) != len(header):
            continue
        ok = True
        parsed = []
        for cell in row:
            try:
                parsed.append(float(cell))
            except ValueError:
                ok = False
                break
        if not ok:
            continue
        for name, val in zip(header, parsed):
            cols[name].append(val)

    arr = {name: np.asarray(v, dtype=float) for name, v in cols.items()}

    # localizar columna de tiempo
    time_key = None
    for cand in _TIME_KEYS:
        for name in header:
            if name.lower() == cand:
                time_key = name
                break
        if time_key:
            break
    if time_key is None:
        # sin tiempo explícito: usar índice y Fs nominal (o 1 Hz)
        n = len(next(iter(arr.values()))) if arr else 0
        fs = fs_nominal or 1.0
        t = np.arange(n) / fs
        data = {k: v for k, v in arr.items()}
        return Capture(t=t, channels=data, fs=fs, fs_nominal=fs_nominal)

    t_raw = arr.pop(time_key)
    t = (t_raw - t_raw[0]) * _time_scale(time_key) if t_raw.size else t_raw
    fs, jitter, dropouts = estimate_fs(t)
    if fs == 0.0 and fs_nominal:
        fs = fs_nominal
    return Capture(
        t=t,
        channels=arr,
        fs=fs,
        fs_nominal=fs_nominal,
        jitter_s=jitter,
        dropouts=dropouts,
        meta={"time_column": time_key},
    )


def load_csv(path_or_text: str, fs_nominal: float | None = None, is_text: bool = False) -> Capture:
    """
    Carga un CSV canónico SISELA (con encabezado). Ignora líneas de comentario
    ('#', '=', '-', '[') y filas no numéricas (banners del menú del firmware).
    """
    if is_text:
        fh = io.StringIO(path_or_text)
    else:
        fh = open(path_or_text, "r", encoding="utf-8", errors="ignore")
    try:
        raw_lines = [ln.rstrip("\n") for ln in fh]
    finally:
        fh.close()

    header = None
    rows = []
    for ln in raw_lines:
        s = ln.strip()
        if not s or s[0] in "#=[-":
            continue
        parts = next(csv.reader([s]))
        parts = [p.strip() for p in parts]
        # ¿es encabezado? -> primera fila con >=2 campos donde no todos son numéricos
        if header is None:
            numeric = all(_is_float(p) for p in parts)
            if not numeric and len(parts) >= 2:
                header = parts
                continue
            # CSV sin encabezado: generar nombres
            header = ["t_us"] + [f"ch{i}" for i in range(len(parts) - 1)] if len(parts) > 1 else ["ch0"]
        rows.append(parts)

    if header is None:
        raise ValueError("CSV vacío o sin datos numéricos.")
    return from_rows(header, rows, fs_nominal=fs_nominal)


def _is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def save_npz(cap: Capture, path: str) -> None:
    """Guarda una captura en formato .npz (t + canales + metadatos)."""
    np.savez(
        path,
        t=cap.t,
        fs=cap.fs,
        fs_nominal=cap.fs_nominal if cap.fs_nominal is not None else np.nan,
        jitter_s=cap.jitter_s,
        **cap.channels,
    )
