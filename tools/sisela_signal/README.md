# sisela_signal — Toolkit de análisis de señales (P4–P8)

Herramienta PC reutilizable para los **paradigmas de análisis de señales** de las
prácticas P4–P8 de SISELA-Init. El microcontrolador adquiere y transmite; esta
toolkit hace el DSP y las gráficas.

| Paradigma | Módulo | Comando |
|---|---|---|
| Muestreo y aliasing (Nyquist) | `sampling` | `alias` |
| Análisis espectral (FFT, ventanas, THD, SFDR) | `spectrum` | `spectrum` |
| Filtrado digital (FIR/IIR, media móvil, mediana) | `filters` | `filter` |
| Caracterización ADC/instrumento (SNR, SINAD, ENOB) | `characterize` | `characterize` |
| Respuesta en frecuencia (Bode por barrido) | `bode` | `bode` |
| Adquisición serie / import de osciloscopio | `capture`, `scopeio` | `capture`, `scope` |

## Instalación

```bash
python -m venv .venv && source .venv/bin/activate      # opcional pero recomendado
pip install -r tools/sisela_signal/requirements.txt
```

Dependencias: `numpy`, `scipy`, `matplotlib`, `pyserial` (+ `pytest` para las pruebas).

Ejecuta siempre desde la **raíz del repo** o añade `tools/` a `PYTHONPATH`:

```bash
export PYTHONPATH=tools
python -m sisela_signal --help
```

## Uso rápido

```bash
# 1) Capturar un bloque del MCU (entra al modo 6, 5 s, guarda CSV)
python -m sisela_signal capture --port /dev/ttyUSB0 --menu 6 --seconds 5 --out cap.csv

# 1-bis) Vista en vivo (gráfica actualizándose) del mismo stream, sin capturar
#        primero — sirve para CUALQUIER práctica/modo que emita CSV por serie,
#        sea firmware MicroPython o C++ (el formato es idéntico, ver más abajo)
python -m sisela_signal live --port /dev/ttyUSB0 --menu 6 --cols dt_us
python -m sisela_signal live --port /dev/ttyUSB0 --menu 5 --cols duty_pct,adc_raw --window 10
#        (--save-csv además guarda el CSV recibido mientras se grafica en vivo)

# 2) Espectro + métricas de calidad de la cadena ADC
python -m sisela_signal spectrum --file cap.csv --col v --metrics --full-scale 3.3

# 3) Aliasing: ¿qué frecuencia aparente da un tono de 7 kHz a Fs=5 kHz?
python -m sisela_signal alias --f 7000 --fs 5000
#    ... o sobre una captura real:
python -m sisela_signal alias --file cap.csv --true-f 7000

# 4) Filtrar y comparar antes/después + respuesta en frecuencia
python -m sisela_signal filter --file cap.csv --col v --kind butter --cutoff 50 --order 4 --bode

# 5) Caracterizar la respuesta al escalón de un actuador
python -m sisela_signal characterize --file step.csv --col deg --mode step

# 6) Bode de una cadena por barrido senoidal (una captura por frecuencia)
python -m sisela_signal bode --amp-in 1.5 \
    --point 10:cap_10hz.csv --point 50:cap_50hz.csv --point 200:cap_200hz.csv

# 7) Importar un CSV exportado del osciloscopio de banco
python -m sisela_signal scope --file RigolDS1Z_CH1.csv
python -m sisela_signal spectrum --file RigolDS1Z_CH1.csv --scope --metrics
```

Añade `--save fig.png` a cualquier comando para guardar la gráfica en vez de mostrarla.

## Formato CSV canónico

El firmware (`lib/siglab.py`, `common/siglab.h`) emite:

```
t_us,ch0[,ch1,...]
0,32768
200,32450
...
```

`t_us` es una marca de tiempo monótona en microsegundos. La toolkit **estima la Fs
real** a partir de esa columna (no confía en la Fs solicitada) y reporta el jitter
de muestreo y las muestras perdidas. Las líneas de banner del menú del firmware
(`===`, `[siglab]`, `menu>`, …) se ignoran automáticamente.

## Configuración de los instrumentos de banco

### Generador de funciones → entrada ADC

El ADC de ESP32/RP2040 acepta **0–3.3 V** y **no tolera voltajes negativos ni
> 3.3 V**. Para inyectar una señal del generador:

- **Forma de onda**: seno (o la que pida la práctica).
- **Amplitud**: ≤ 2 Vpp.
- **Offset DC**: +1.65 V (centra la señal en medio del rango).
- **Salida del generador**: alta impedancia (`HighZ`) si el generador lo permite.
- **Protección** (recomendada): divisor 1:1 a 3.3 V + diodos de recorte a GND y 3.3 V,
  o simplemente mantener amplitud+offset dentro de 0.3–3.0 V y verificar con el
  osciloscopio **antes** de conectar al MCU.

> ⚠️ Nunca conectes la salida del generador directamente a un pin ADC sin verificar
> que la señal completa (offset − amplitud/2 … offset + amplitud/2) esté dentro de
> 0–3.3 V. Un pico negativo puede dañar el pin.

### Osciloscopio

- Sonda **×10**, compensada, punta de resorte a GND corto.
- Acoplamiento **DC** para medir niveles; **AC** para ver rizado/ruido pequeño sobre
  un nivel alto.
- Exporta la traza a CSV (USB) y procésala con `scope` / `--scope`.
- Para jitter de PWM/STEP: usa *Measure → Pulse Width* con estadística
  (Min/Max/Mean/StdDev) y, si el equipo lo permite, exporta el histograma.

## Módulos (uso como librería)

```python
from sisela_signal.dataio import load_csv
from sisela_signal import spectrum, filters, sampling, characterize, bode
from sisela_signal.scopeio import load_scope_csv
from sisela_signal.live import live_plot

cap = load_csv("cap.csv")                 # -> Capture(t, channels, fs, jitter_s, ...)
m = spectrum.tone_metrics(cap.col("v"), cap.fs, full_scale=3.3)
print(m.report())                         # THD, SNR, SINAD, ENOB, SFDR

live_plot(port="/dev/ttyUSB0", menu="6", cols=["dt_us"], window=15)
```

## Pruebas

```bash
pip install pytest
PYTHONPATH=tools python -m pytest tools/sisela_signal/tests -q
```

Las pruebas usan señales sintéticas y los *fixtures* de `examples/` (regenerables con
`python tools/sisela_signal/examples/make_examples.py`); **no requieren hardware**.

## Fuera de alcance

- Control SCPI del generador/osciloscopio (las frecuencias del barrido se
  introducen a mano).
- FFT en el propio microcontrolador (solo Goertzel de un bin — ver `siglab`).
