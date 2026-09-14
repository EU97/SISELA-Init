"""
spectrum — análisis espectral: FFT con ventanas, PSD (Welch), THD, SNR, SINAD,
ENOB, SFDR y piso de ruido.

Convención: se trabaja con señales reales muestreadas a Fs. La amplitud del
espectro de una sinusoide de amplitud A aparece como A en `amplitude_spectrum`
(corrección de ganancia coherente de la ventana aplicada).

Referencias:
  * Nyquist / DFT: Oppenheim & Schafer, "Discrete-Time Signal Processing".
  * ENOB/SINAD/THD/SFDR: IEEE Std 1241-2010 (ADC testing), Analog Devices MT-003.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# ----------------------------------------------------------------------------
# Ventanas
# ----------------------------------------------------------------------------
_WINDOWS = ("rect", "hann", "hamming", "blackman", "blackmanharris", "flattop")


def get_window(name: str, n: int) -> np.ndarray:
    """Devuelve una ventana de longitud n. Nombres: rect, hann, hamming,
    blackman, blackmanharris, flattop."""
    name = (name or "hann").lower()
    if name in ("rect", "boxcar", "none"):
        return np.ones(n)
    if name == "hann":
        return np.hanning(n)
    if name == "hamming":
        return np.hamming(n)
    if name == "blackman":
        return np.blackman(n)
    if name in ("blackmanharris", "bh", "bh4"):
        a = (0.35875, 0.48829, 0.14128, 0.01168)
        k = np.arange(n)
        return (a[0] - a[1] * np.cos(2 * np.pi * k / (n - 1))
                + a[2] * np.cos(4 * np.pi * k / (n - 1))
                - a[3] * np.cos(6 * np.pi * k / (n - 1)))
    if name == "flattop":
        a = (0.21557895, 0.41663158, 0.277263158, 0.083578947, 0.006947368)
        k = np.arange(n)
        return (a[0] - a[1] * np.cos(2 * np.pi * k / (n - 1))
                + a[2] * np.cos(4 * np.pi * k / (n - 1))
                - a[3] * np.cos(6 * np.pi * k / (n - 1))
                + a[4] * np.cos(8 * np.pi * k / (n - 1)))
    raise ValueError(f"Ventana desconocida: {name!r}. Opciones: {_WINDOWS}")


# ----------------------------------------------------------------------------
# Espectro de amplitud (FFT de un solo bloque)
# ----------------------------------------------------------------------------
@dataclass
class Spectrum:
    freqs: np.ndarray          # Hz (0 .. Fs/2)
    amplitude: np.ndarray      # amplitud lineal (misma unidad que la señal)
    fs: float
    window: str

    def db(self, ref: float | None = None) -> np.ndarray:
        """Espectro en dB. ref=None -> relativo al máximo (dBc del tono mayor)."""
        a = np.maximum(self.amplitude, 1e-20)
        r = ref if ref is not None else float(np.max(a))
        return 20.0 * np.log10(a / r)

    def peak(self) -> tuple[float, float]:
        """(frecuencia, amplitud) del bin de mayor amplitud (excluyendo DC)."""
        idx = np.argmax(self.amplitude[1:]) + 1
        return float(self.freqs[idx]), float(self.amplitude[idx])


def amplitude_spectrum(x: np.ndarray, fs: float, window: str = "hann",
                       detrend: bool = True) -> Spectrum:
    """
    Espectro de amplitud de un solo bloque, calibrado para que una sinusoide de
    amplitud A aparezca con amplitud A (corrección por ganancia coherente de la
    ventana).
    """
    x = np.asarray(x, dtype=float)
    n = x.size
    if detrend:
        x = x - np.mean(x)
    w = get_window(window, n)
    cg = np.sum(w) / n  # coherent gain
    X = np.fft.rfft(x * w)
    amp = np.abs(X) / n / cg * 2.0
    if n % 2 == 0:
        amp[-1] /= 2.0
    amp[0] /= 2.0
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    return Spectrum(freqs=freqs, amplitude=amp, fs=fs, window=window)


def welch_psd(x: np.ndarray, fs: float, nperseg: int | None = None,
              window: str = "hann", overlap: float = 0.5):
    """
    Densidad espectral de potencia por el método de Welch (V²/Hz).
    Devuelve (freqs, psd). Implementación propia (sin depender de scipy.signal)
    para portabilidad, con resultados equivalentes.
    """
    x = np.asarray(x, dtype=float)
    n = x.size
    if nperseg is None:
        nperseg = min(n, max(256, 1 << int(np.log2(max(n // 8, 256)))))
    nperseg = int(min(nperseg, n))
    step = max(1, int(nperseg * (1.0 - overlap)))
    w = get_window(window, nperseg)
    scale = 1.0 / (fs * np.sum(w ** 2))
    segs = range(0, n - nperseg + 1, step)
    acc = np.zeros(nperseg // 2 + 1)
    count = 0
    for start in segs:
        seg = x[start:start + nperseg]
        seg = seg - np.mean(seg)
        X = np.fft.rfft(seg * w)
        p = (np.abs(X) ** 2) * scale
        p[1:-1] *= 2.0
        acc += p
        count += 1
    if count == 0:
        seg = x - np.mean(x)
        X = np.fft.rfft(seg * get_window(window, n))
        acc = (np.abs(X) ** 2) / (fs * np.sum(get_window(window, n) ** 2))
        acc[1:-1] *= 2.0
        count = 1
        nperseg = n
    psd = acc / count
    freqs = np.fft.rfftfreq(nperseg, d=1.0 / fs)
    return freqs, psd


# ----------------------------------------------------------------------------
# Métricas de calidad (ADC / cadena de instrumentación)
# ----------------------------------------------------------------------------
@dataclass
class ToneMetrics:
    f_signal: float          # Hz
    signal_dbfs: float       # nivel de la fundamental relativo a fondo de escala
    thd_pct: float           # distorsión armónica total [%]
    thd_db: float            # THD en dB
    snr_db: float            # relación señal/ruido (sin armónicos)
    sinad_db: float          # señal / (ruido + distorsión)
    enob_bits: float         # número efectivo de bits = (SINAD - 1.76) / 6.02
    sfdr_db: float           # rango dinámico libre de espurios
    noise_floor_dbfs: float  # piso de ruido medio
    harmonics: list          # [(f, dbc), ...] hasta el 6º armónico

    def report(self) -> str:
        h = "  ".join(f"H{i+2}:{d:+.1f}" for i, (_, d) in enumerate(self.harmonics))
        return (
            f"f_señal      : {self.f_signal:.2f} Hz\n"
            f"THD          : {self.thd_pct:.3f} %  ({self.thd_db:.1f} dB)\n"
            f"SNR          : {self.snr_db:.1f} dB\n"
            f"SINAD        : {self.sinad_db:.1f} dB\n"
            f"ENOB         : {self.enob_bits:.2f} bits\n"
            f"SFDR         : {self.sfdr_db:.1f} dB\n"
            f"piso de ruido : {self.noise_floor_dbfs:.1f} dBFS\n"
            f"armónicos    : {h}"
        )


def tone_metrics(x: np.ndarray, fs: float, full_scale: float | None = None,
                 window: str = "blackmanharris", n_harmonics: int = 6) -> ToneMetrics:
    """
    Analiza una captura que contiene UNA sinusoide dominante y calcula THD, SNR,
    SINAD, ENOB y SFDR (método IEEE 1241, ventana + FFT).

    full_scale: amplitud de fondo de escala (p.ej. 3.3 para un ADC 0–3.3 V, o
                65535 para códigos RP2040). Si None, se usa 2*amplitud de la
                fundamental (fondo de escala = pico-a-pico de la señal).
    """
    x = np.asarray(x, dtype=float)
    n = x.size
    x = x - np.mean(x)
    w = get_window(window, n)
    X = np.abs(np.fft.rfft(x * w))
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    power = X ** 2

    # Ancho de lóbulo de la ventana (bins a cada lado a excluir en cada tono).
    leak = {"rect": 1, "hann": 2, "hamming": 2, "blackman": 3,
            "blackmanharris": 4, "flattop": 5}.get(window, 3)

    def band(idx):
        lo = max(1, idx - leak)
        hi = min(len(power), idx + leak + 1)
        return np.arange(lo, hi)

    # Fundamental
    search = power.copy()
    search[0:leak + 1] = 0.0
    k_sig = int(np.argmax(search))
    f_sig = float(freqs[k_sig])
    sig_bins = band(k_sig)
    p_signal = float(np.sum(power[sig_bins]))

    # Armónicos (con aliasing plegado a [0, Fs/2])
    nyq = fs / 2.0
    harmonics = []
    p_harm = 0.0
    used = set(sig_bins.tolist())
    for h in range(2, n_harmonics + 2):
        fh = h * f_sig
        # plegado por aliasing
        fa = fh % fs
        if fa > nyq:
            fa = fs - fa
        kh = int(round(fa / (fs / n)))
        if kh <= leak or kh >= len(power) - leak:
            harmonics.append((fa, -200.0))
            continue
        bins = band(kh)
        p_h = float(np.sum(power[bins]))
        p_harm += p_h
        used.update(bins.tolist())
        dbc = 10.0 * np.log10(max(p_h, 1e-30) / max(p_signal, 1e-30))
        harmonics.append((fa, dbc))

    # Ruido = todo lo demás (excluye DC, fundamental y armónicos)
    mask = np.ones(len(power), dtype=bool)
    mask[0:leak + 1] = False
    for b in used:
        if 0 <= b < len(mask):
            mask[b] = False
    p_noise = float(np.sum(power[mask]))

    # Escalas
    amp_sig = 2.0 * np.sqrt(p_signal) / np.sum(w)
    fs_amp = full_scale if full_scale else amp_sig
    signal_dbfs = 20.0 * np.log10(max(amp_sig, 1e-20) / max(fs_amp, 1e-20))

    snr = 10.0 * np.log10(p_signal / max(p_noise, 1e-30))
    sinad = 10.0 * np.log10(p_signal / max(p_noise + p_harm, 1e-30))
    thd_ratio = np.sqrt(max(p_harm, 0.0) / max(p_signal, 1e-30))
    thd_pct = 100.0 * thd_ratio
    thd_db = 20.0 * np.log10(max(thd_ratio, 1e-12))
    enob = (sinad - 1.76) / 6.02

    # SFDR: fundamental vs mayor espurio (armónico o ruido)
    spur = power[mask]
    p_spur_max = float(np.max(spur)) if spur.size else 1e-30
    p_harm_max = max((10 ** (d / 10.0) * p_signal for _, d in harmonics if d > -199), default=1e-30)
    sfdr = 10.0 * np.log10(p_signal / max(p_spur_max, p_harm_max, 1e-30))

    # Piso de ruido medio en dBFS
    with np.errstate(divide="ignore"):
        noise_amp = 2.0 * np.sqrt(power[mask]) / np.sum(w)
    noise_floor_dbfs = 20.0 * np.log10(max(np.median(noise_amp), 1e-20) / max(fs_amp, 1e-20))

    return ToneMetrics(
        f_signal=f_sig,
        signal_dbfs=signal_dbfs,
        thd_pct=thd_pct,
        thd_db=thd_db,
        snr_db=snr,
        sinad_db=sinad,
        enob_bits=enob,
        sfdr_db=sfdr,
        noise_floor_dbfs=noise_floor_dbfs,
        harmonics=harmonics,
    )


# ----------------------------------------------------------------------------
# Gráficas
# ----------------------------------------------------------------------------
def plot_spectrum(spec: Spectrum, ax=None, db: bool = True, mark_harmonics: int = 0,
                  title: str | None = None):
    """Grafica un espectro de amplitud. Devuelve el eje matplotlib."""
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(9, 4))
    y = spec.db() if db else spec.amplitude
    ax.plot(spec.freqs, y, lw=0.9)
    ax.set_xlabel("Frecuencia [Hz]")
    ax.set_ylabel("Magnitud [dBc]" if db else "Amplitud")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, spec.fs / 2)
    if mark_harmonics:
        f0, _ = spec.peak()
        for h in range(1, mark_harmonics + 1):
            fh = f0 * h
            if fh < spec.fs / 2:
                ax.axvline(fh, color="r", ls=":", lw=0.7, alpha=0.6)
    ax.set_title(title or f"Espectro (ventana {spec.window}, Fs={spec.fs:.0f} Hz)")
    return ax


def plot_psd(freqs: np.ndarray, psd: np.ndarray, ax=None, title: str | None = None):
    """Grafica una PSD (Welch) en dB/Hz."""
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(9, 4))
    ax.semilogy(freqs, np.maximum(psd, 1e-30), lw=0.9)
    ax.set_xlabel("Frecuencia [Hz]")
    ax.set_ylabel("PSD [unidad²/Hz]")
    ax.grid(True, which="both", alpha=0.3)
    ax.set_title(title or "Densidad espectral de potencia (Welch)")
    return ax
