"""
characterize — caracterización de ADC / cadena de instrumentación y de respuesta
dinámica (escalón).

ADC / cadena analógica (a partir de una captura senoidal):
  * adc_metrics()      -> ENOB, SINAD, SNR, THD, SFDR, ruido RMS (envuelve spectrum.tone_metrics)
  * effective_resolution_bits()
  * code_histogram()   -> densidad de códigos y DNL/INL aproximados (método histograma)
  * noise_rms()        -> ruido RMS con entrada en DC

Respuesta dinámica (a partir de una captura de escalón):
  * step_metrics()     -> rise time, fall time, overshoot, settling, tau, ancho de banda
  * allan_deviation()  -> estabilidad vs tiempo de promediado (deriva del sensor/ADC)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .spectrum import tone_metrics, ToneMetrics


# ----------------------------------------------------------------------------
# ADC / cadena analógica
# ----------------------------------------------------------------------------
def adc_metrics(x: np.ndarray, fs: float, full_scale: float | None = None,
                window: str = "blackmanharris") -> ToneMetrics:
    """
    Métricas dinámicas del ADC/cadena para una captura que contiene UNA sinusoide.
    full_scale: fondo de escala en las unidades de x (p.ej. 3.3 V, o 65535 códigos).
    """
    return tone_metrics(x, fs, full_scale=full_scale, window=window)


def effective_resolution_bits(x_dc: np.ndarray, full_scale: float) -> float:
    """
    Resolución efectiva (bits) con entrada estática:
        ENOB_dc = log2(full_scale / (sqrt(12) * rms_ruido))
    Equivale a "cuántos bits son estables" frente al ruido de fondo.
    """
    rms = float(np.std(np.asarray(x_dc, dtype=float)))
    if rms <= 0:
        return float("inf")
    return float(np.log2(full_scale / (np.sqrt(12.0) * rms)))


def noise_rms(x_dc: np.ndarray) -> dict:
    """Ruido con entrada en DC: RMS, pico-a-pico, y nº de códigos pp si son enteros."""
    x = np.asarray(x_dc, dtype=float)
    x = x - np.mean(x)
    return {
        "rms": float(np.std(x)),
        "pp": float(np.max(x) - np.min(x)),
        "pp_codes": float(np.round(np.max(x) - np.min(x))),
    }


@dataclass
class HistogramResult:
    codes: np.ndarray
    counts: np.ndarray
    dnl: np.ndarray       # LSB
    inl: np.ndarray       # LSB
    dnl_max: float
    inl_max: float
    missing_codes: int


def code_histogram(x_codes: np.ndarray, n_bits: int | None = None) -> HistogramResult:
    """
    DNL/INL aproximados por el método de histograma (densidad de códigos) usando
    una rampa lenta o una sinusoide que cubra el rango. Con sinusoide se aplica la
    corrección de PDF arcoseno.

    x_codes: muestras del ADC en CÓDIGOS enteros que barren el rango.
    """
    x = np.asarray(x_codes, dtype=float)
    lo, hi = int(np.floor(x.min())), int(np.ceil(x.max()))
    edges = np.arange(lo, hi + 2) - 0.5
    counts, _ = np.histogram(x, bins=edges)
    codes = np.arange(lo, hi + 1)

    # ¿rampa o seno? heurística: si el histograma tiene forma de "U" -> seno
    mid = counts[len(counts) // 4: 3 * len(counts) // 4]
    ends = np.concatenate([counts[:len(counts) // 8], counts[-len(counts) // 8:]])
    sine_like = ends.mean() > 1.5 * max(mid.mean(), 1e-9)

    if sine_like:
        a = (hi - lo) / 2.0
        c = (hi + lo) / 2.0
        ideal = 1.0 / (np.pi * np.sqrt(np.maximum(a ** 2 - (codes - c) ** 2, 1e-9)))
        ideal = ideal / ideal.sum() * counts.sum()
    else:
        ideal = np.full_like(counts, counts.sum() / len(counts), dtype=float)

    with np.errstate(divide="ignore", invalid="ignore"):
        dnl = counts / ideal - 1.0
    dnl[~np.isfinite(dnl)] = 0.0
    dnl[[0, -1]] = 0.0  # los códigos extremos no son fiables
    inl = np.cumsum(dnl)
    interior = counts[1:-1] if counts.size > 2 else counts
    return HistogramResult(
        codes=codes, counts=counts, dnl=dnl, inl=inl,
        dnl_max=float(np.max(np.abs(dnl))), inl_max=float(np.max(np.abs(inl))),
        missing_codes=int(np.count_nonzero(interior == 0)),
    )


# ----------------------------------------------------------------------------
# Respuesta al escalón
# ----------------------------------------------------------------------------
@dataclass
class StepMetrics:
    t0: float             # instante del escalón [s]
    y_initial: float
    y_final: float
    rise_time_s: float    # 10 % -> 90 %
    settling_time_s: float # entrada permanente a ±2 %
    overshoot_pct: float
    tau_s: float          # constante de tiempo (ajuste 1er orden), 63.2 %
    bandwidth_hz: float    # f_-3dB ≈ 1/(2*pi*tau) para 1er orden
    delay_s: float        # retardo hasta 50 %

    def report(self) -> str:
        return (
            f"escalón       : {self.y_initial:.4g} -> {self.y_final:.4g}\n"
            f"retardo (50%) : {self.delay_s * 1e3:.3f} ms\n"
            f"t. subida 10-90: {self.rise_time_s * 1e3:.3f} ms\n"
            f"sobreimpulso  : {self.overshoot_pct:.2f} %\n"
            f"t. estab. ±2% : {self.settling_time_s * 1e3:.3f} ms\n"
            f"τ (63.2%)     : {self.tau_s * 1e3:.3f} ms\n"
            f"ancho de banda : {self.bandwidth_hz:.2f} Hz"
        )


def step_metrics(t: np.ndarray, y: np.ndarray, settle_frac: float = 0.02) -> StepMetrics:
    """
    Métricas de respuesta al escalón. Detecta automáticamente el instante y la
    dirección del escalón a partir de la mayor derivada.
    """
    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float)

    dy = np.gradient(y, t)
    k0 = int(np.argmax(np.abs(dy)))
    t0 = t[k0]

    pre = y[max(0, k0 - len(y) // 10):max(1, k0)]
    post = y[min(len(y) - 1, k0 + int(0.8 * (len(y) - k0))):]
    y_i = float(np.median(pre)) if pre.size else float(y[0])
    y_f = float(np.median(post)) if post.size else float(y[-1])
    span = y_f - y_i
    if span == 0:
        span = 1e-12
    yn = (y - y_i) / span  # normalizada 0 -> 1

    def _cross(level, start):
        for i in range(start, len(yn)):
            if (span > 0 and yn[i] >= level) or (span < 0 and yn[i] <= level):
                return t[i]
        return t[-1]

    t10 = _cross(0.1, k0)
    t50 = _cross(0.5, k0)
    t90 = _cross(0.9, k0)
    rise = max(t90 - t10, 0.0)

    seg = yn[k0:]
    overshoot = max(0.0, (np.max(seg) - 1.0) * 100.0) if span > 0 else max(0.0, (1.0 - np.min(seg)) * 100.0)

    # settling: último instante fuera de la banda ±settle_frac
    outside = np.where(np.abs(yn[k0:] - 1.0) > settle_frac)[0]
    settling = (t[k0 + outside[-1]] - t0) if outside.size else 0.0

    # tau por ajuste exponencial 1er orden: yn = 1 - exp(-(t-t0)/tau)
    mask = (t >= t0) & (yn < 0.98) & (yn > 0.02)
    if np.count_nonzero(mask) >= 3:
        tt = t[mask] - t0
        val = np.clip(1.0 - yn[mask], 1e-6, 1.0)
        tau = float(-np.polyfit(tt, np.log(val), 1)[0])
        tau = 1.0 / tau if tau > 0 else max(t90 - t0, 1e-9)
    else:
        tau = max(t90 - t0, 1e-9)
    bw = 1.0 / (2.0 * np.pi * tau) if tau > 0 else float("inf")

    return StepMetrics(
        t0=float(t0), y_initial=y_i, y_final=y_f,
        rise_time_s=float(rise), settling_time_s=float(settling),
        overshoot_pct=float(overshoot), tau_s=float(tau),
        bandwidth_hz=float(bw), delay_s=float(max(t50 - t0, 0.0)),
    )


# ----------------------------------------------------------------------------
# Estabilidad (Allan) — deriva de sensor/ADC
# ----------------------------------------------------------------------------
def allan_deviation(x: np.ndarray, fs: float, taus=None):
    """
    Desviación de Allan (overlapping) vs tiempo de promediado. Muestra hasta qué
    punto promediar mejora la resolución antes de que domine la deriva.
    Devuelve (taus_s, adev).
    """
    x = np.asarray(x, dtype=float)
    n = x.size
    dt = 1.0 / fs
    if taus is None:
        mmax = n // 4
        ms = np.unique(np.floor(np.logspace(0, np.log10(max(mmax, 2)), 30)).astype(int))
        ms = ms[ms >= 1]
    else:
        ms = np.unique((np.asarray(taus) * fs).astype(int))
        ms = ms[ms >= 1]
    adev = []
    tau_out = []
    for m in ms:
        if m < 1 or m > n // 2:
            continue
        # promedios de bloques de m muestras
        k = n // m
        blocks = x[:k * m].reshape(k, m).mean(axis=1)
        d = np.diff(blocks)
        if d.size < 1:
            continue
        av = np.sqrt(0.5 * np.mean(d ** 2))
        adev.append(av)
        tau_out.append(m * dt)
    return np.asarray(tau_out), np.asarray(adev)


# ----------------------------------------------------------------------------
# Gráficas
# ----------------------------------------------------------------------------
def plot_step(t, y, m: StepMetrics, ax=None):
    import matplotlib.pyplot as plt
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 4))
    ax.plot(t, y, lw=1.0)
    ax.axvline(m.t0, color="k", ls=":", lw=0.8)
    ax.axhline(m.y_final, color="g", ls="--", lw=0.8, alpha=0.7)
    band = abs(m.y_final - m.y_initial) * 0.02
    ax.axhspan(m.y_final - band, m.y_final + band, color="g", alpha=0.1)
    ax.set_xlabel("Tiempo [s]"); ax.set_ylabel("Salida")
    ax.set_title(f"Respuesta al escalón — τ={m.tau_s*1e3:.2f} ms, "
                 f"tr={m.rise_time_s*1e3:.2f} ms, OS={m.overshoot_pct:.1f} %")
    ax.grid(True, alpha=0.3)
    return ax


def plot_histogram(h: HistogramResult):
    import matplotlib.pyplot as plt
    fig, (a0, a1, a2) = plt.subplots(3, 1, figsize=(9, 7), sharex=True)
    a0.bar(h.codes, h.counts, width=1.0)
    a0.set_ylabel("cuentas"); a0.set_title("Densidad de códigos")
    a1.plot(h.codes, h.dnl, lw=0.8); a1.axhline(0, color="k", lw=0.5)
    a1.set_ylabel("DNL [LSB]"); a1.grid(True, alpha=0.3)
    a2.plot(h.codes, h.inl, lw=0.8); a2.axhline(0, color="k", lw=0.5)
    a2.set_ylabel("INL [LSB]"); a2.set_xlabel("Código ADC"); a2.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig
