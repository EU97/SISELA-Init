"""
Genera CSV sintéticos usados como fixtures por los tests y por la documentación.
Ejecutar:  python tools/sisela_signal/examples/make_examples.py
"""

import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def _write(name, header, t_us, cols):
    path = os.path.join(HERE, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(header + "\n")
        for i in range(len(t_us)):
            fh.write(f"{t_us[i]:.1f}," + ",".join(f"{c[i]:.6g}" for c in cols) + "\n")
    print("escrito", path)


def main():
    rng = np.random.default_rng(1)

    # 1) seno 1 kHz limpio, Fs=20 kHz, 4096 muestras, 0-3.3 V (offset 1.65)
    fs = 20_000.0
    n = 4096
    t = np.arange(n) / fs
    v = 1.65 + 1.5 * np.sin(2 * np.pi * 1000.0 * t) + rng.normal(0, 0.002, n)
    _write("sine_1k.csv", "t_us,v", (t * 1e6), [v])

    # 2) seno cuantizado a 12 bits (ENOB de referencia ~ 11.8) sobre 0-3.3 V
    fs = 48_000.0
    n = 8192
    t = np.arange(n) / fs
    a = 1.62
    pure = 1.65 + a * np.sin(2 * np.pi * 997.0 * t)
    lsb = 3.3 / 4096.0
    codes = np.round(pure / lsb)
    vq = codes * lsb + rng.normal(0, 0.05 * lsb, n)
    _write("sine_quantized.csv", "t_us,v", (t * 1e6), [vq])

    # 3) escalón de 1er orden: 90 -> 120 con tau = 8 ms, Fs = 2 kHz
    fs = 2_000.0
    n = 400
    t = np.arange(n) / fs
    t0 = 0.05
    tau = 0.008
    y = np.where(t < t0, 90.0, 90.0 + 30.0 * (1 - np.exp(-(t - t0) / tau)))
    y += rng.normal(0, 0.15, n)
    _write("step.csv", "t_us,deg", (t * 1e6), [y])

    # 4) PWM 1 kHz, duty 30%, Fs = 200 kHz (para espectro de armónicos)
    fs = 200_000.0
    n = 4000
    t = np.arange(n) / fs
    fpwm = 1000.0
    duty = 0.30
    ph = (t * fpwm) % 1.0
    pwm = np.where(ph < duty, 3.3, 0.0) + rng.normal(0, 0.01, n)
    _write("pwm_1k.csv", "t_us,v", (t * 1e6), [pwm])

    # 5) aliasing: seno real de 7 kHz muestreado a 5 kHz -> alias en 2 kHz
    fs = 5_000.0
    n = 2048
    t = np.arange(n) / fs
    alias = 1.65 + 1.2 * np.sin(2 * np.pi * 7000.0 * t) + rng.normal(0, 0.003, n)
    _write("aliased_7k_at_5k.csv", "t_us,v", (t * 1e6), [alias])


if __name__ == "__main__":
    main()
