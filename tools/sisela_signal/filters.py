"""
filters — filtrado digital y su análisis en frecuencia.

Filtros disponibles:
  * moving_average(x, N)          media móvil (FIR de coeficientes iguales)
  * median_filter(x, N)           mediana deslizante (no lineal, quita "spikes")
  * ema(x, alpha)                 exponencial de 1er orden (IIR)
  * butter(x, fs, cutoff, ...)    Butterworth LP/HP/BP (scipy, filtfilt sin fase)
  * fir_lowpass(x, fs, cutoff, N) FIR de fase lineal (ventana)

Análisis:
  * response(kind, ...)           (w, H) respuesta compleja en frecuencia
  * plot_compare(...)             tiempo + espectro antes/después
  * group_delay(...)              retardo de grupo

Todos operan sobre arrays 1-D reales. `butter`/FIR requieren scipy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

try:
    from scipy import signal as _sig
    HAVE_SCIPY = True
except ImportError:  # pragma: no cover
    _sig = None
    HAVE_SCIPY = False


# ----------------------------------------------------------------------------
# Filtros
# ----------------------------------------------------------------------------
def moving_average(x: np.ndarray, n: int) -> np.ndarray:
    """Media móvil de n muestras (mismo tamaño de salida, borde 'reflect')."""
    x = np.asarray(x, dtype=float)
    n = max(1, int(n))
    if n == 1:
        return x.copy()
    pad = n // 2
    xp = np.pad(x, (pad, n - 1 - pad), mode="edge")
    k = np.ones(n) / n
    return np.convolve(xp, k, mode="valid")


def median_filter(x: np.ndarray, n: int = 5) -> np.ndarray:
    """Mediana deslizante de ventana impar n."""
    x = np.asarray(x, dtype=float)
    n = int(n) | 1
    pad = n // 2
    xp = np.pad(x, pad, mode="edge")
    out = np.empty_like(x)
    for i in range(x.size):
        out[i] = np.median(xp[i:i + n])
    return out


def ema(x: np.ndarray, alpha: float) -> np.ndarray:
    """Filtro exponencial de 1er orden: y[k] = y[k-1] + alpha*(x[k]-y[k-1])."""
    x = np.asarray(x, dtype=float)
    a = float(np.clip(alpha, 0.0, 1.0))
    y = np.empty_like(x)
    acc = x[0] if x.size else 0.0
    for i, xi in enumerate(x):
        acc += a * (xi - acc)
        y[i] = acc
    return y


def ema_alpha_for_cutoff(fc: float, fs: float) -> float:
    """alpha equivalente a un RC de frecuencia de corte fc a una Fs dada."""
    dt = 1.0 / fs
    rc = 1.0 / (2.0 * np.pi * fc)
    return dt / (rc + dt)


def butter(x: np.ndarray, fs: float, cutoff, order: int = 4, btype: str = "low",
           zero_phase: bool = True) -> np.ndarray:
    """Butterworth vía scipy. cutoff: escalar (low/high) o (lo,hi) para band."""
    _require_scipy()
    wn = np.atleast_1d(np.asarray(cutoff, dtype=float)) / (fs / 2.0)
    wn = wn if wn.size > 1 else wn[0]
    sos = _sig.butter(order, wn, btype=btype, output="sos")
    if zero_phase:
        return _sig.sosfiltfilt(sos, x)
    return _sig.sosfilt(sos, x)


def fir_lowpass(x: np.ndarray, fs: float, cutoff: float, numtaps: int = 63,
                window: str = "hamming", zero_phase: bool = False) -> np.ndarray:
    """FIR pasa-bajos de fase lineal (diseño por ventana)."""
    _require_scipy()
    taps = _sig.firwin(numtaps | 1, cutoff / (fs / 2.0), window=window)
    if zero_phase:
        return _sig.filtfilt(taps, [1.0], x)
    return _sig.lfilter(taps, [1.0], x)


# ----------------------------------------------------------------------------
# Respuesta en frecuencia
# ----------------------------------------------------------------------------
@dataclass
class FreqResponse:
    f: np.ndarray        # Hz
    H: np.ndarray        # ganancia compleja
    fs: float
    label: str

    @property
    def mag_db(self) -> np.ndarray:
        return 20.0 * np.log10(np.maximum(np.abs(self.H), 1e-12))

    @property
    def phase_deg(self) -> np.ndarray:
        return np.degrees(np.unwrap(np.angle(self.H)))

    def cutoff_3db(self) -> float | None:
        """Primera frecuencia donde la magnitud cae 3 dB respecto a la banda de paso."""
        ref = self.mag_db[1] if self.mag_db.size > 1 else self.mag_db[0]
        below = np.where(self.mag_db <= ref - 3.0)[0]
        return float(self.f[below[0]]) if below.size else None


def response(kind: str, fs: float, n: int = 2048, **kw) -> FreqResponse:
    """
    Respuesta en frecuencia teórica de un filtro.
      kind='movavg'  -> kw: N
      kind='ema'     -> kw: alpha
      kind='butter'  -> kw: cutoff, order, btype
      kind='fir'     -> kw: cutoff, numtaps, window
    """
    f = np.linspace(0.0, fs / 2.0, n)
    w = 2.0 * np.pi * f / fs
    z = np.exp(1j * w)
    kind = kind.lower()
    if kind in ("movavg", "ma", "moving_average"):
        N = int(kw.get("N", kw.get("n", 8)))
        with np.errstate(invalid="ignore", divide="ignore"):
            H = (1.0 / N) * (1 - z ** -N) / (1 - z ** -1)
        H[0] = 1.0
        label = f"Media móvil N={N}"
    elif kind == "ema":
        a = float(kw.get("alpha", 0.2))
        H = a / (1 - (1 - a) * z ** -1)
        label = f"EMA α={a:g}"
    elif kind == "butter":
        _require_scipy()
        order = int(kw.get("order", 4))
        btype = kw.get("btype", "low")
        cutoff = np.atleast_1d(np.asarray(kw["cutoff"], dtype=float)) / (fs / 2.0)
        cutoff = cutoff if cutoff.size > 1 else cutoff[0]
        b, a = _sig.butter(order, cutoff, btype=btype)
        _, H = _sig.freqz(b, a, worN=w)
        label = f"Butterworth {btype} fc={kw['cutoff']} Hz orden {order}"
    elif kind == "fir":
        _require_scipy()
        numtaps = int(kw.get("numtaps", 63)) | 1
        taps = _sig.firwin(numtaps, np.asarray(kw["cutoff"], dtype=float) / (fs / 2.0),
                           window=kw.get("window", "hamming"))
        _, H = _sig.freqz(taps, [1.0], worN=w)
        label = f"FIR fc={kw['cutoff']} Hz {numtaps} taps"
    else:
        raise ValueError(f"kind desconocido: {kind}")
    return FreqResponse(f=f, H=np.asarray(H), fs=fs, label=label)


def apply(kind: str, x: np.ndarray, fs: float, **kw) -> np.ndarray:
    """Aplica un filtro por nombre (mismos kinds que response())."""
    kind = kind.lower()
    if kind in ("movavg", "ma", "moving_average"):
        return moving_average(x, kw.get("N", kw.get("n", 8)))
    if kind == "median":
        return median_filter(x, kw.get("N", kw.get("n", 5)))
    if kind == "ema":
        return ema(x, kw.get("alpha", 0.2))
    if kind == "butter":
        return butter(x, fs, kw["cutoff"], order=kw.get("order", 4),
                      btype=kw.get("btype", "low"), zero_phase=kw.get("zero_phase", True))
    if kind == "fir":
        return fir_lowpass(x, fs, kw["cutoff"], numtaps=kw.get("numtaps", 63),
                           window=kw.get("window", "hamming"),
                           zero_phase=kw.get("zero_phase", False))
    raise ValueError(f"kind desconocido: {kind}")


def group_delay(fr: FreqResponse) -> np.ndarray:
    """Retardo de grupo en muestras: -dφ/dω."""
    phase = np.unwrap(np.angle(fr.H))
    w = 2.0 * np.pi * fr.f / fr.fs
    return -np.gradient(phase, w)


# ----------------------------------------------------------------------------
# Gráficas
# ----------------------------------------------------------------------------
def plot_compare(t: np.ndarray, raw: np.ndarray, filt: np.ndarray, fs: float,
                 title: str = "Filtrado digital: antes / después"):
    """Panel 2x1: señal en el tiempo (raw vs filt) + espectros superpuestos."""
    import matplotlib.pyplot as plt
    from .spectrum import amplitude_spectrum

    fig, (a0, a1) = plt.subplots(2, 1, figsize=(9, 6))
    a0.plot(t, raw, lw=0.7, alpha=0.6, label="cruda")
    a0.plot(t, filt, lw=1.1, label="filtrada")
    a0.set_xlabel("Tiempo [s]"); a0.set_ylabel("Amplitud")
    a0.grid(True, alpha=0.3); a0.legend(fontsize=8); a0.set_title(title)

    s_raw = amplitude_spectrum(raw, fs)
    s_flt = amplitude_spectrum(filt, fs)
    a1.plot(s_raw.freqs, s_raw.db(), lw=0.7, alpha=0.6, label="cruda")
    a1.plot(s_flt.freqs, s_flt.db(ref=float(np.max(s_raw.amplitude))), lw=1.0, label="filtrada")
    a1.set_xlabel("Frecuencia [Hz]"); a1.set_ylabel("Magnitud [dB]")
    a1.set_xlim(0, fs / 2); a1.grid(True, alpha=0.3); a1.legend(fontsize=8)
    fig.tight_layout()
    return fig


def plot_bode(*responses: FreqResponse, title: str = "Respuesta en frecuencia"):
    """Bode (magnitud + fase) de uno o varios filtros."""
    import matplotlib.pyplot as plt

    fig, (a0, a1) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    for fr in responses:
        a0.semilogx(fr.f[1:], fr.mag_db[1:], label=fr.label)
        a1.semilogx(fr.f[1:], fr.phase_deg[1:])
    a0.axhline(-3, color="k", ls=":", lw=0.8, alpha=0.6)
    a0.set_ylabel("Magnitud [dB]"); a0.grid(True, which="both", alpha=0.3)
    a0.legend(fontsize=8); a0.set_title(title)
    a1.set_xlabel("Frecuencia [Hz]"); a1.set_ylabel("Fase [°]")
    a1.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    return fig


def _require_scipy():
    if not HAVE_SCIPY:  # pragma: no cover
        raise ImportError("Esta función requiere scipy. Instala: pip install scipy")
