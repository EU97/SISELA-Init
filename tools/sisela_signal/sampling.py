"""
sampling — muestreo y aliasing (teorema de Nyquist–Shannon).

Herramientas:
  * alias_frequency(f, fs)     -> frecuencia aparente tras el muestreo
  * folding_diagram(fmax, fs)  -> datos para el diagrama de plegado
  * sweep_apparent(records)    -> tabla real vs aparente de un barrido con el generador
  * sampling_jitter(t)         -> estadística del jitter de la base de tiempo
  * reconstruct(x, fs, up)     -> reconstrucción por interpolación sinc (banda limitada)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def alias_frequency(f: float | np.ndarray, fs: float) -> float | np.ndarray:
    """
    Frecuencia aparente (0 .. fs/2) de un tono real de frecuencia f muestreado a fs.

    Un tono por encima de fs/2 se "pliega" (aliasing). Ejemplo clásico:
        alias_frequency(1300, 1000) -> 300.0
        alias_frequency(700, 1000)  -> 300.0
    """
    f = np.abs(np.asarray(f, dtype=float))
    fn = fs / 2.0
    r = np.mod(f, fs)
    r = np.where(r > fn, fs - r, r)
    return float(r) if np.ndim(r) == 0 else r


def is_undersampled(f_max: float, fs: float) -> bool:
    """True si fs no cumple el criterio de Nyquist para f_max (fs <= 2*f_max)."""
    return fs <= 2.0 * f_max


def nyquist_zone(f: float, fs: float) -> int:
    """Zona de Nyquist (1, 2, 3, ...) en la que cae el tono f."""
    return int(np.floor(f / (fs / 2.0))) + 1


def folding_diagram(f_max: float, fs: float, n: int = 2000):
    """
    Datos para el diagrama de plegado: (f_real, f_aparente) desde 0 hasta f_max.
    Útil para ilustrar cómo las frecuencias > fs/2 se reflejan en la banda base.
    """
    f = np.linspace(0.0, f_max, n)
    return f, alias_frequency(f, fs)


@dataclass
class SweepPoint:
    f_gen: float          # frecuencia ajustada en el generador [Hz]
    f_apparent: float     # frecuencia medida en el espectro de la captura [Hz]
    f_expected: float     # alias teórico [Hz]
    zone: int             # zona de Nyquist


def sweep_apparent(f_gen_list, fs: float, f_apparent_list=None) -> list[SweepPoint]:
    """
    Construye la tabla real-vs-aparente de un barrido de frecuencia del generador.

    f_gen_list      : frecuencias ajustadas en el generador
    fs              : Fs de muestreo del ADC
    f_apparent_list : frecuencias medidas en cada captura (opcional; si se omite,
                      se usa el alias teórico como "medido")
    """
    out = []
    for i, fg in enumerate(f_gen_list):
        fe = alias_frequency(fg, fs)
        fa = f_apparent_list[i] if f_apparent_list is not None else fe
        out.append(SweepPoint(f_gen=float(fg), f_apparent=float(fa),
                              f_expected=float(fe), zone=nyquist_zone(fg, fs)))
    return out


@dataclass
class JitterStats:
    fs_mean: float        # Hz
    dt_mean_s: float
    dt_std_s: float       # jitter RMS de la base de tiempo
    dt_pp_s: float        # jitter pico-a-pico
    dropouts: int
    # Ruido de fase equivalente para un tono a f_sig por jitter de apertura:
    # SNR_jitter = -20*log10(2*pi*f_sig*t_jitter)   (IEEE 1241)

    def snr_jitter_db(self, f_sig: float) -> float:
        tj = self.dt_std_s
        if tj <= 0 or f_sig <= 0:
            return float("inf")
        return -20.0 * np.log10(2.0 * np.pi * f_sig * tj)


def sampling_jitter(t_seconds: np.ndarray) -> JitterStats:
    """Estadística del jitter de muestreo a partir del vector de tiempo (s)."""
    t = np.asarray(t_seconds, dtype=float)
    dt = np.diff(t)
    dt = dt[dt > 0]
    med = float(np.median(dt)) if dt.size else 0.0
    return JitterStats(
        fs_mean=1.0 / np.mean(dt) if dt.size else 0.0,
        dt_mean_s=float(np.mean(dt)) if dt.size else 0.0,
        dt_std_s=float(np.std(dt)) if dt.size else 0.0,
        dt_pp_s=float(np.max(dt) - np.min(dt)) if dt.size else 0.0,
        dropouts=int(np.count_nonzero(dt > 1.5 * med)) if med else 0,
    )


def reconstruct(x: np.ndarray, fs: float, upsample: int = 10) -> tuple[np.ndarray, np.ndarray]:
    """
    Reconstrucción de banda limitada por interpolación sinc (Whittaker–Shannon).
    Devuelve (t_fino, x_reconstruida). Ilustra que, si se cumple Nyquist, la
    señal continua se recupera exactamente de las muestras.
    """
    x = np.asarray(x, dtype=float)
    n = x.size
    t = np.arange(n) / fs
    t_fine = np.linspace(0.0, (n - 1) / fs, n * upsample)
    # matriz sinc: x_fine[k] = sum_m x[m] * sinc((t_fine[k]-t[m]) * fs)
    tt = (t_fine[:, None] - t[None, :]) * fs
    x_fine = np.sinc(tt) @ x
    return t_fine, x_fine


def plot_folding(f_max: float, fs: float, ax=None):
    """Grafica el diagrama de plegado de frecuencias."""
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(8, 4))
    f, fa = folding_diagram(f_max, fs)
    ax.plot(f, fa, lw=1.2)
    ax.axvline(fs / 2, color="r", ls="--", label="Fs/2 (Nyquist)")
    ax.axvline(fs, color="k", ls=":", alpha=0.5, label="Fs")
    ax.plot([0, fs / 2], [0, fs / 2], color="g", ls=":", alpha=0.6, label="sin aliasing")
    ax.set_xlabel("Frecuencia real de entrada [Hz]")
    ax.set_ylabel("Frecuencia aparente tras muestreo [Hz]")
    ax.set_title(f"Diagrama de plegado (aliasing) — Fs = {fs:.0f} Hz")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    return ax
