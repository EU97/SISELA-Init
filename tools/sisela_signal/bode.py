"""
bode — respuesta en frecuencia de una cadena de señal por barrido senoidal
escalonado (stepped-sine), con el generador de funciones de banco.

Flujo de laboratorio:
  1. El generador entrega una sinusoide a frecuencia f_k (amplitud fija, dentro de
     0–3.3 V con offset).
  2. El firmware captura un bloque a Fs y transmite CSV (o se exporta del osciloscopio).
  3. Por cada f_k se estima ganancia y fase respecto a la entrada.
  4. Se ensambla el diagrama de Bode y se extrae f_-3dB y la pendiente de caída.

Este módulo NO controla el generador (entrada manual de frecuencias). Si el
generador soporta SCPI, se puede automatizar aparte.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


def _fit_sine(t: np.ndarray, x: np.ndarray, f: float) -> tuple[float, float]:
    """Ajuste por mínimos cuadrados de x(t) ≈ A*cos(2πft) + B*sin(2πft) + C.
    Devuelve (amplitud, fase[rad])."""
    w = 2.0 * np.pi * f
    M = np.column_stack([np.cos(w * t), np.sin(w * t), np.ones_like(t)])
    coef, *_ = np.linalg.lstsq(M, x, rcond=None)
    a, b = coef[0], coef[1]
    amp = np.hypot(a, b)
    phase = np.arctan2(-b, a)
    return float(amp), float(phase)


@dataclass
class BodePoint:
    f: float
    gain_db: float
    phase_deg: float
    amp_in: float
    amp_out: float


@dataclass
class BodeResult:
    points: list[BodePoint] = field(default_factory=list)

    @property
    def f(self):
        return np.array([p.f for p in self.points])

    @property
    def gain_db(self):
        return np.array([p.gain_db for p in self.points])

    @property
    def phase_deg(self):
        return np.array([p.phase_deg for p in self.points])

    def cutoff_3db(self) -> float | None:
        g = self.gain_db
        if g.size < 2:
            return None
        ref = np.max(g[: max(1, g.size // 3)])
        below = np.where(g <= ref - 3.0)[0]
        if not below.size:
            return None
        i = below[0]
        if i == 0:
            return float(self.f[0])
        # interpolación log-lineal
        f0, f1 = self.f[i - 1], self.f[i]
        g0, g1 = g[i - 1], g[i]
        frac = (ref - 3.0 - g0) / (g1 - g0)
        return float(np.exp(np.log(f0) + frac * (np.log(f1) - np.log(f0))))

    def rolloff_db_per_decade(self) -> float | None:
        """Pendiente de caída ajustada en la última década de datos."""
        if len(self.points) < 3:
            return None
        f = np.log10(self.f)
        g = self.gain_db
        m = f >= (f.max() - 1.0)
        if np.count_nonzero(m) < 2:
            m = slice(-3, None)
        slope = np.polyfit(f[m], g[m], 1)[0]
        return float(slope)


def point_from_capture(t: np.ndarray, x_in: np.ndarray, x_out: np.ndarray,
                       f: float) -> BodePoint:
    """Un punto de Bode a partir de capturas simultáneas de entrada y salida."""
    t = np.asarray(t, dtype=float)
    ai, pi = _fit_sine(t, np.asarray(x_in, float), f)
    ao, po = _fit_sine(t, np.asarray(x_out, float), f)
    gain = 20.0 * np.log10(max(ao, 1e-12) / max(ai, 1e-12))
    phase = np.degrees(((po - pi) + np.pi) % (2 * np.pi) - np.pi)
    return BodePoint(f=f, gain_db=gain, phase_deg=phase, amp_in=ai, amp_out=ao)


def point_from_output(t: np.ndarray, x_out: np.ndarray, f: float,
                      amp_in: float) -> BodePoint:
    """Un punto de Bode cuando solo se captura la salida (entrada de amplitud
    conocida y fija del generador). La fase queda referida a la del generador (0)."""
    t = np.asarray(t, dtype=float)
    ao, po = _fit_sine(t, np.asarray(x_out, float), f)
    gain = 20.0 * np.log10(max(ao, 1e-12) / max(amp_in, 1e-12))
    return BodePoint(f=f, gain_db=gain, phase_deg=float(np.degrees(po)),
                     amp_in=amp_in, amp_out=ao)


def plot_bode(res: BodeResult, title: str = "Diagrama de Bode (barrido senoidal)"):
    import matplotlib.pyplot as plt

    fig, (a0, a1) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    a0.semilogx(res.f, res.gain_db, "o-", ms=4)
    fc = res.cutoff_3db()
    if fc:
        a0.axvline(fc, color="r", ls="--", lw=0.8, label=f"f₋₃dB ≈ {fc:.1f} Hz")
        a0.legend(fontsize=8)
    a0.axhline(-3, color="k", ls=":", lw=0.7)
    a0.set_ylabel("Ganancia [dB]"); a0.grid(True, which="both", alpha=0.3)
    a0.set_title(title)
    a1.semilogx(res.f, res.phase_deg, "o-", ms=4)
    a1.set_xlabel("Frecuencia [Hz]"); a1.set_ylabel("Fase [°]")
    a1.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    return fig
