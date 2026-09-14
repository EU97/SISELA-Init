"""
scopeio — carga de exportaciones CSV de osciloscopios de banco.

Formatos soportados (autodetección):
  * Rigol DS1000Z / MSO5000  — cabeceras 'X,CH1,CH2...' + fila 'Second,Volt,Volt' +
    a veces bloque 'Start,Increment,...'
  * Siglent SDS               — metadatos 'Sampling Rate,...', 'Time,CH1'
  * Tektronix TDS/TBS         — pares de columnas '<params>,,<t>,<v>' o 'TIME,CH1'
  * Genérico                  — 2 columnas numéricas (t, v) o (v) con --fs

Devuelve un `sisela_signal.dataio.Capture`.
"""

from __future__ import annotations

import csv
import io

import numpy as np

from .dataio import Capture, estimate_fs


def load_scope_csv(path: str, fs_hint: float | None = None) -> Capture:
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        text = fh.read()
    return parse_scope_text(text, fs_hint=fs_hint, source=path)


def parse_scope_text(text: str, fs_hint: float | None = None,
                     source: str = "<text>") -> Capture:
    low = text[:2000].lower()
    if "increment" in low and ("rigol" in low or "x,ch" in low or "second,volt" in low):
        return _parse_rigol(text, fs_hint)
    if "sampling rate" in low or "siglent" in low:
        return _parse_siglent(text, fs_hint)
    if "record length" in low or "sample interval" in low or "tektronix" in low:
        return _parse_tek(text, fs_hint)
    return _parse_generic(text, fs_hint)


# ---------------------------------------------------------------------------
def _numeric_rows(lines):
    rows = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        parts = next(csv.reader([s]))
        try:
            vals = [float(p) for p in parts if p != ""]
        except ValueError:
            continue
        if len(vals) >= 1:
            rows.append(vals)
    return rows


def _finish(t, chans, fs_hint):
    t = np.asarray(t, dtype=float)
    if t.size:
        t = t - t[0]
    fs, jitter, drop = estimate_fs(t) if t.size > 1 else (fs_hint or 0.0, 0.0, 0)
    if not fs:
        fs = fs_hint or 1.0
        t = np.arange(len(next(iter(chans.values())))) / fs
    return Capture(t=t, channels={k: np.asarray(v, float) for k, v in chans.items()},
                   fs=fs, jitter_s=jitter, dropouts=drop, meta={"source": "scope"})


def _parse_generic(text, fs_hint):
    lines = text.splitlines()
    # detectar encabezado (primera línea no numérica con comas)
    header = None
    body = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        parts = next(csv.reader([s]))
        numeric = True
        for p in parts:
            try:
                float(p)
            except ValueError:
                numeric = False
                break
        if header is None and not numeric and len(parts) >= 1:
            header = [p.strip() for p in parts]
            continue
        if numeric:
            body.append([float(p) for p in parts if p != ""])
    rows = np.array([r for r in body if len(r) == len(body[0])]) if body else np.empty((0, 0))
    if rows.size == 0:
        raise ValueError(f"No se hallaron datos numéricos en {source_hint(text)}")
    if rows.shape[1] == 1:
        v = rows[:, 0]
        fs = fs_hint or 1.0
        t = np.arange(v.size) / fs
        return _finish(t, {"ch0": v}, fs)
    t = rows[:, 0]
    chans = {}
    names = header[1:] if header and len(header) - 1 == rows.shape[1] - 1 else None
    for i in range(1, rows.shape[1]):
        nm = names[i - 1].strip() if names else f"ch{i-1}"
        chans[nm or f"ch{i-1}"] = rows[:, i]
    return _finish(t, chans, fs_hint)


def _parse_rigol(text, fs_hint):
    lines = text.splitlines()
    # Rigol: a veces trae "Start,Increment,..." con el paso temporal
    increment = None
    start = 0.0
    for ln in lines[:20]:
        cells = [c.strip() for c in ln.split(",")]
        if len(cells) >= 2 and cells[0].lower() in ("increment", "sample interval"):
            try:
                increment = float(cells[1])
            except ValueError:
                pass
        if len(cells) >= 2 and cells[0].lower() == "start":
            try:
                start = float(cells[1])
            except ValueError:
                pass
    rows = _numeric_rows(lines)
    rows = [r for r in rows if len(r) == len(rows[0])]
    arr = np.asarray(rows)
    if increment is not None and arr.shape[1] >= 1:
        # columnas = solo canales
        n = arr.shape[0]
        t = start + np.arange(n) * increment
        chans = {f"CH{i+1}": arr[:, i] for i in range(arr.shape[1])}
        return _finish(t, chans, fs_hint)
    # formato X,CH1,...
    t = arr[:, 0]
    chans = {f"CH{i}": arr[:, i] for i in range(1, arr.shape[1])}
    return _finish(t, chans, fs_hint)


def _parse_siglent(text, fs_hint):
    lines = text.splitlines()
    fs = fs_hint
    for ln in lines[:30]:
        cells = [c.strip() for c in ln.split(",")]
        if cells and "sampling rate" in cells[0].lower():
            for c in cells[1:]:
                v = _si_to_float(c)
                if v:
                    fs = v
                    break
    rows = _numeric_rows(lines)
    rows = [r for r in rows if len(r) == len(rows[0])]
    arr = np.asarray(rows)
    if arr.shape[1] >= 2:
        t = arr[:, 0]
        chans = {f"CH{i}": arr[:, i] for i in range(1, arr.shape[1])}
        return _finish(t, chans, fs)
    v = arr[:, 0]
    fs = fs or 1.0
    return _finish(np.arange(v.size) / fs, {"ch0": v}, fs)


def _parse_tek(text, fs_hint):
    lines = text.splitlines()
    dt = None
    for ln in lines[:25]:
        cells = [c.strip() for c in ln.split(",")]
        if len(cells) >= 2 and cells[0].lower() in ("sample interval", "horizontal interval"):
            try:
                dt = float(cells[1])
            except ValueError:
                pass
    rows = _numeric_rows(lines)
    rows = [r for r in rows if len(r) == len(rows[0])]
    arr = np.asarray(rows)
    # Tek clásico: columnas [p1, p2, t, v]
    if arr.shape[1] == 4:
        t, v = arr[:, 2], arr[:, 3]
        return _finish(t, {"CH1": v}, fs_hint)
    if arr.shape[1] >= 2:
        return _finish(arr[:, 0], {f"CH{i}": arr[:, i] for i in range(1, arr.shape[1])}, fs_hint)
    v = arr[:, 0]
    fs = (1.0 / dt) if dt else (fs_hint or 1.0)
    return _finish(np.arange(v.size) / fs, {"CH1": v}, fs)


def _si_to_float(s: str):
    s = s.strip().replace("Sa/s", "").replace("S/s", "").strip()
    mult = {"k": 1e3, "M": 1e6, "G": 1e9, "m": 1e-3, "u": 1e-6, "µ": 1e-6, "n": 1e-9}
    try:
        if s and s[-1] in mult:
            return float(s[:-1]) * mult[s[-1]]
        return float(s)
    except ValueError:
        return None


def source_hint(text: str) -> str:
    return io.StringIO(text).readline().strip()[:60] or "<csv>"
