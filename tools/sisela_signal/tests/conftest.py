import os
import sys

import numpy as np
import pytest

# Permite `import sisela_signal` sin instalar (añade tools/ al path).
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Backend no interactivo para matplotlib en CI.
import matplotlib  # noqa: E402
matplotlib.use("Agg")


@pytest.fixture
def sine():
    """Sinusoide de amplitud 1.0, ~1 kHz coherente, Fs 20 kHz, 4096 muestras, sin ruido."""
    fs = 20_000.0
    n = 4096
    cycles = round(1000.0 * n / fs)          # frecuencia coherente (bin exacto)
    f = cycles * fs / n                       # ≈ 1000.98 Hz
    t = np.arange(n) / fs
    x = np.sin(2 * np.pi * f * t)
    return t, x, fs


@pytest.fixture
def examples_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples"))
