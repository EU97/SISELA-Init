import numpy as np
import pytest

from sisela_signal import spectrum


def test_amplitude_spectrum_peak_bin_and_amplitude(sine):
    t, x, fs = sine
    spec = spectrum.amplitude_spectrum(x, fs, window="hann")
    f0, a0 = spec.peak()
    assert f0 == pytest.approx(1000.0, abs=fs / len(x))
    # amplitud de una sinusoide de amplitud 1.0 debe recuperarse ~1.0
    assert a0 == pytest.approx(1.0, rel=0.02)


def test_windows_have_expected_length_and_finite():
    for w in ("rect", "hann", "hamming", "blackman", "blackmanharris", "flattop"):
        win = spectrum.get_window(w, 512)
        assert win.shape == (512,)
        assert np.all(np.isfinite(win))


def test_welch_psd_parseval_like(sine):
    t, x, fs = sine
    f, p = spectrum.welch_psd(x, fs, nperseg=1024)
    # potencia integrada ~ varianza de la señal (0.5 para sin de amplitud 1)
    power = np.trapezoid(p, f)
    assert power == pytest.approx(0.5, rel=0.15)


def test_tone_metrics_clean_sine_high_enob(sine):
    t, x, fs = sine
    m = spectrum.tone_metrics(x, fs, full_scale=2.0)
    assert m.f_signal == pytest.approx(1000.0, abs=10)
    assert m.thd_pct < 0.1
    assert m.enob_bits > 14  # seno float "perfecto" => ENOB alto


def test_tone_metrics_quantized_sine_enob(examples_dir):
    from sisela_signal.dataio import load_csv
    cap = load_csv(f"{examples_dir}/sine_quantized.csv")
    m = spectrum.tone_metrics(cap.col("v"), cap.fs, full_scale=3.3)
    # 12 bits ideal => ENOB ~ 11.7; con un poco de ruido añadido, 10.5–12
    assert 10.0 < m.enob_bits < 12.5
    assert 0.0 <= m.thd_pct < 5.0


def test_tone_metrics_harmonics_detected():
    fs = 50_000.0
    n = 8192
    t = np.arange(n) / fs
    x = np.sin(2 * np.pi * 1000 * t) + 0.05 * np.sin(2 * np.pi * 2000 * t) \
        + 0.02 * np.sin(2 * np.pi * 3000 * t)
    m = spectrum.tone_metrics(x, fs, full_scale=1.0)
    # THD de 5% + 2% => sqrt(0.05^2+0.02^2) ~ 5.4%
    assert m.thd_pct == pytest.approx(5.4, abs=1.0)
    h2_f, h2_db = m.harmonics[0]
    assert h2_f == pytest.approx(2000.0, abs=20)
    assert h2_db == pytest.approx(20 * np.log10(0.05), abs=3.0)
