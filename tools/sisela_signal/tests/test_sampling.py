import numpy as np
import pytest

from sisela_signal import sampling


@pytest.mark.parametrize("f,fs,expected", [
    (1300, 1000, 300),
    (700, 1000, 300),
    (7000, 5000, 2000),
    (100, 1000, 100),      # bien muestreado
    (500, 1000, 500),      # justo en Nyquist
    (2500, 2000, 500),
])
def test_alias_frequency(f, fs, expected):
    assert sampling.alias_frequency(f, fs) == pytest.approx(expected, abs=1e-6)


def test_alias_frequency_vectorized():
    f = np.array([100, 700, 1300])
    out = sampling.alias_frequency(f, 1000)
    np.testing.assert_allclose(out, [100, 300, 300])


def test_nyquist_zone():
    assert sampling.nyquist_zone(100, 1000) == 1
    assert sampling.nyquist_zone(700, 1000) == 2
    assert sampling.nyquist_zone(1300, 1000) == 3


def test_is_undersampled():
    assert sampling.is_undersampled(600, 1000) is True
    assert sampling.is_undersampled(400, 1000) is False


def test_aliased_capture_peak_matches_theory(examples_dir):
    from sisela_signal.dataio import load_csv
    from sisela_signal.spectrum import amplitude_spectrum
    cap = load_csv(f"{examples_dir}/aliased_7k_at_5k.csv")
    spec = amplitude_spectrum(cap.col("v"), cap.fs)
    f0, _ = spec.peak()
    assert f0 == pytest.approx(2000.0, abs=cap.fs / cap.n * 2)
    assert sampling.alias_frequency(7000, cap.fs) == pytest.approx(2000.0)


def test_sampling_jitter_on_uniform_grid():
    fs = 1000.0
    t = np.arange(500) / fs
    js = sampling.sampling_jitter(t)
    assert js.fs_mean == pytest.approx(1000.0, rel=1e-6)
    assert js.dt_std_s == pytest.approx(0.0, abs=1e-12)


def test_reconstruct_recovers_bandlimited_sine():
    fs = 8000.0
    n = 256
    t = np.arange(n) / fs
    x = np.sin(2 * np.pi * 500 * t)
    tf, xf = sampling.reconstruct(x, fs, upsample=5)
    ref = np.sin(2 * np.pi * 500 * tf)
    # ignora bordes (efecto de truncamiento del sinc)
    mid = slice(len(tf) // 5, -len(tf) // 5)
    assert np.max(np.abs(xf[mid] - ref[mid])) < 0.05
