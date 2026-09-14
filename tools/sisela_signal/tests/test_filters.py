import numpy as np
import pytest

from sisela_signal import filters


def test_moving_average_preserves_length_and_dc():
    x = np.ones(100) * 5.0
    y = filters.moving_average(x, 8)
    assert y.shape == x.shape
    assert np.allclose(y, 5.0)


def test_moving_average_attenuates_high_freq():
    fs = 1000.0
    n = 2000
    t = np.arange(n) / fs
    lf = np.sin(2 * np.pi * 5 * t)
    hf = 0.5 * np.sin(2 * np.pi * 200 * t)
    y = filters.moving_average(lf + hf, 16)
    # el componente de baja frecuencia sobrevive; el de alta se atenúa
    assert np.std(y - lf) < 0.2


def test_median_filter_removes_spikes():
    x = np.zeros(101)
    x[50] = 100.0
    y = filters.median_filter(x, 5)
    assert y[50] == 0.0


def test_ema_step_response_time_constant():
    x = np.ones(1000)
    x[:100] = 0.0
    alpha = filters.ema_alpha_for_cutoff(10.0, 1000.0)
    y = filters.ema(x, alpha)
    # tras ~1 tau debe alcanzar ~63%
    tau_samples = int(1000.0 / (2 * np.pi * 10.0))
    assert y[100 + tau_samples] == pytest.approx(0.63, abs=0.1)


def test_butter_lowpass_cutoff(sine):
    t, x, fs = sine  # 1 kHz
    # filtro con corte en 200 Hz debe eliminar casi todo el tono de 1 kHz
    y = filters.butter(x, fs, 200.0, order=4, btype="low")
    assert np.std(y) < 0.1 * np.std(x)


def test_response_movavg_first_null():
    fr = filters.response("movavg", 1000.0, N=10)
    # primer nulo de una media móvil de N=10 a Fs=1000 => 100 Hz
    idx = np.argmin(np.abs(fr.f - 100.0))
    assert fr.mag_db[idx] < -30


def test_response_butter_3db_point():
    fr = filters.response("butter", 2000.0, cutoff=100.0, order=4, btype="low")
    fc = fr.cutoff_3db()
    assert fc == pytest.approx(100.0, rel=0.15)
