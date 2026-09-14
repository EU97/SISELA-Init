import os
import subprocess
import sys

import numpy as np
import pytest

from sisela_signal import dataio, scopeio

TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_ENV = {**os.environ, "PYTHONPATH": TOOLS_DIR, "MPLBACKEND": "Agg"}


def test_load_csv_canonical(examples_dir):
    cap = dataio.load_csv(f"{examples_dir}/sine_1k.csv")
    assert "v" in cap.channels
    assert cap.n == 4096
    assert cap.fs == pytest.approx(20000.0, rel=1e-3)


def test_load_csv_ignores_banner_lines():
    text = "\n".join([
        "=== Practica 5 ===",
        "[siglab] Fs=5000 Hz n=8",
        "t_us,v",
        "0,1.0",
        "200,1.1",
        "menu>",
        "400,1.2",
        "600,1.3",
    ])
    cap = dataio.load_csv(text, is_text=True)
    assert cap.n == 4
    assert list(cap.channels) == ["v"]


def test_estimate_fs_and_jitter():
    t = np.array([0, 1e-3, 2e-3, 3e-3, 5.1e-3])  # una muestra perdida (gap 2.1 ms)
    fs, jitter, drop = dataio.estimate_fs(t)
    assert fs == pytest.approx(1000.0)
    assert drop == 1


def test_scope_generic_two_column(tmp_path):
    p = tmp_path / "scope.csv"
    fs = 10000.0
    t = np.arange(1000) / fs
    v = np.sin(2 * np.pi * 60 * t)
    p.write_text("time,CH1\n" + "\n".join(f"{ti:.6e},{vi:.4f}" for ti, vi in zip(t, v)))
    cap = scopeio.load_scope_csv(str(p))
    assert cap.fs == pytest.approx(10000.0, rel=1e-3)
    assert "CH1" in cap.channels


def test_cli_spectrum_smoke(examples_dir, tmp_path):
    out = tmp_path / "spec.png"
    r = subprocess.run(
        [sys.executable, "-m", "sisela_signal", "spectrum",
         "--file", f"{examples_dir}/sine_1k.csv", "--col", "v",
         "--metrics", "--full-scale", "3.3", "--save", str(out)],
        capture_output=True, text=True, env=_ENV,
    )
    assert r.returncode == 0, r.stderr
    assert out.exists()
    assert "ENOB" in r.stdout


def test_cli_alias_smoke(tmp_path):
    out = tmp_path / "alias.png"
    r = subprocess.run(
        [sys.executable, "-m", "sisela_signal", "alias", "--f", "1300", "--fs", "1000",
         "--save", str(out)],
        capture_output=True, text=True, env=_ENV,
    )
    assert r.returncode == 0, r.stderr
    assert "300" in r.stdout
    assert "ALIASING" in r.stdout
