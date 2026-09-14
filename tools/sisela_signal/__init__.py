"""
sisela_signal — Toolkit de análisis de señales para SISELA-Init (Prácticas P4–P8)

Paradigmas cubiertos:
  * Muestreo y aliasing (teorema de Nyquist)         -> sampling
  * Análisis espectral (FFT, ventanas, THD, SFDR)    -> spectrum
  * Filtrado digital (FIR/IIR, media móvil, mediana) -> filters
  * Caracterización de ADC/instrumento (SNR, SINAD,  -> characterize
    ENOB, ruido RMS, respuesta escalón, Bode)           bode

Entrada de datos:
  * capture  — stream CSV del microcontrolador por puerto serie
  * scopeio  — exportaciones CSV de osciloscopios de banco (Rigol/Siglent/Tek/genérico)

Uso rápido (línea de comandos):
    python -m sisela_signal spectrum --file captura.csv --col v --fs 5000
    python -m sisela_signal alias    --file barrido.csv
    python -m sisela_signal filter   --file captura.csv --kind butter-lp --cutoff 50
    python -m sisela_signal characterize --file seno.csv --mode adc
    python -m sisela_signal capture  --port /dev/ttyUSB0 --menu 6 --seconds 5

Uso como librería:
    from sisela_signal import spectrum, filters, sampling, characterize
    from sisela_signal.scopeio import load_scope_csv

Dependencias: numpy, scipy, matplotlib, pyserial  (ver requirements.txt)
Licencia: MIT — SISELA-Init / FIME-UANL
"""

from . import spectrum, sampling, filters, characterize, bode, scopeio, capture, report  # noqa: F401

__all__ = [
    "spectrum",
    "sampling",
    "filters",
    "characterize",
    "bode",
    "scopeio",
    "capture",
    "report",
]

__version__ = "0.1.0"
