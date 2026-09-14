import numpy as np
import pytest

from sisela_signal import characterize, bode


def test_effective_resolution_bits_matches_quantization():
    rng = np.random.default_rng(0)
    full_scale = 3.3
    lsb = full_scale / 4096
    # ruido uniforme de 1 LSB pp -> sigma = lsb/sqrt(12) -> ENOB_dc ~ 12
    noise = rng.uniform(-lsb / 2, lsb / 2, 20000)
    er = characterize.effective_resolution_bits(noise, full_scale)
    assert er == pytest.approx(12.0, abs=0.3)


def test_step_metrics_first_order(examples_dir):
    from sisela_signal.dataio import load_csv
    cap = load_csv(f"{examples_dir}/step.csv")
    m = characterize.step_metrics(cap.t, cap.col("deg"))
    assert m.y_initial == pytest.approx(90.0, abs=1.0)
    assert m.y_final == pytest.approx(120.0, abs=1.0)
    assert m.tau_s == pytest.approx(0.008, rel=0.35)
    assert m.overshoot_pct < 5.0  # 1er orden puro no sobreimpulsa
    # rise 10-90 de un 1er orden ~ 2.2*tau
    assert m.rise_time_s == pytest.approx(2.2 * 0.008, rel=0.4)


def test_step_metrics_overshoot_detected():
    fs = 5000.0
    n = 1500
    t = np.arange(n) / fs
    t0 = 0.05
    wn = 2 * np.pi * 40
    zeta = 0.2
    wd = wn * np.sqrt(1 - zeta ** 2)
    y = np.where(t < t0, 0.0,
                 1.0 - np.exp(-zeta * wn * (t - t0)) *
                 (np.cos(wd * (t - t0)) + (zeta * wn / wd) * np.sin(wd * (t - t0))))
    m = characterize.step_metrics(t, y)
    assert m.overshoot_pct > 30  # zeta=0.2 => ~52%


def test_code_histogram_ramp_flags_missing_codes():
    rng = np.random.default_rng(2)
    # rampa lenta que barre 200..1200 con ruido de <1 LSB
    codes = np.repeat(np.arange(200, 1201), 40).astype(float)
    codes += rng.normal(0, 0.3, codes.size)
    codes = np.round(codes)
    codes[codes == 700] = 701  # elimina por completo el código 700
    h = characterize.code_histogram(codes.astype(int))
    assert h.missing_codes >= 1
    assert h.dnl[np.where(h.codes == 700)[0][0]] == pytest.approx(-1.0, abs=0.2)
    assert h.dnl_max < 5.0


def test_allan_deviation_decreases_for_white_noise():
    rng = np.random.default_rng(3)
    x = rng.normal(0, 1.0, 20000)
    taus, adev = characterize.allan_deviation(x, 1000.0)
    # para ruido blanco, adev ~ 1/sqrt(tau) => decreciente
    assert adev[0] > adev[-1]


def test_bode_point_from_capture_lowpass():
    fs = 10000.0
    n = 4000
    t = np.arange(n) / fs
    f = 300.0
    x_in = np.sin(2 * np.pi * f * t)
    # RC de 1er orden, fc = 100 Hz -> a 300 Hz: |H| ~ 1/sqrt(1+9) = -10 dB
    fc = 100.0
    from scipy.signal import butter, sosfilt
    sos = butter(1, fc / (fs / 2), output="sos")
    x_out = sosfilt(sos, x_in)
    p = bode.point_from_capture(t, x_in, x_out, f)
    assert p.gain_db == pytest.approx(-10.0, abs=1.5)
    assert p.phase_deg == pytest.approx(-71.6, abs=8)
