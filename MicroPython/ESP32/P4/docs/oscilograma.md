# Oscilograma y visualización — Práctica 4 (BMP180)

El BMP180 es un sensor **digital I2C**: no hay una señal analógica de sensor que ver en
el osciloscopio. Lo que sí se observa es el **tráfico del bus I2C** (SDA/SCL) y, en la
PC, las **series temporales** de presión/altitud.

- Análisis de señales completo (ruido, muestreo, espectro, filtrado): ver
  [analisis_senales.md](analisis_senales.md).
- Altímetro visual tipo instrumento: `tools/altimeter_gui.py`.

---

## 1. Formatos CSV del firmware

### Modo 4 — Monitor CSV (para `altimeter_gui.py` y análisis)
```csv
timestamp_ms,temp_C,pressure_hPa,altitude_m
0,23.4,1013.25,540.2
200,23.4,1013.20,540.6
```

### Modo 6 — Bloque de muestreo (análisis de ruido/espectro)
```csv
t_us,alt_m
0,540.213
199950,540.198
...
# fin  fs_real=5.01  jitter_us=340.20
```

### Modo 7 — Filtro digital en vivo
```csv
t_us,alt_raw,alt_filt
0,540.21,540.21
200100,540.19,540.20
```

| Columna | Descripción |
|---|---|
| `timestamp_ms` / `t_us` | tiempo desde el inicio del modo |
| `temp_C` | temperatura compensada (°C) |
| `pressure_hPa` | presión compensada (hPa) |
| `altitude_m` / `alt_m` / `alt_raw` | altitud ISA respecto al QNH (m) |
| `alt_filt` | altitud tras el filtro digital elegido (m) |

---

## 2. Bus I2C en el osciloscopio

| Canal | Señal | Base de tiempo | Trigger |
|---|---|---|---|
| CH1 | **SCL** (GPIO22) | 10 µs/div | flanco de bajada |
| CH2 | **SDA** (GPIO21) | — | — |

Qué medir:

- **Frecuencia de SCL**: ≈ 100 kHz (`I2C_FREQ` en `main.py`).
- **Transacción de lectura**: START → `0x77`+W → ACK → registro → ACK → RESTART →
  `0x77`+R → ACK → datos → NACK → STOP.
- **Periodo entre transacciones**: igual a `1/Fs` del modo activo (200 ms en modos 1–5,
  variable en modo 6).
- **Nivel lógico**: 3.3 V (pull-ups de 4.7 kΩ del módulo GY-68).

Forma de onda idealizada de un byte + ACK:

```
SCL  ─┐_┌─┐_┌─┐_┌─┐_┌─┐_┌─┐_┌─┐_┌─┐_┌─┐_┌──
SDA  ──D7──D6──D5──D4──D3──D2──D1──D0──ACK──   (SDA estable mientras SCL alto)
```

---

## 3. Visualización en la PC

### Altímetro aeronáutico (modo 4)
```bash
cd tools && pip install -r requirements.txt
python altimeter_gui.py --port /dev/ttyUSB0
```

### Análisis de señales (modos 6–7) — toolkit `sisela_signal`
```bash
pip install -r ../../../../tools/sisela_signal/requirements.txt
PYTHONPATH=../../../../tools python -m sisela_signal spectrum --file cap.csv --col alt_m --psd
PYTHONPATH=../../../../tools python -m sisela_signal filter   --file cap.csv --col alt_raw --kind movavg --n 8 --bode
```

---

## 4. Consejos de medida

- Para el ruido en reposo (modo 6), deja el sensor lejos de corrientes de aire y de
  fuentes de calor; tapa el orificio con una espuma suave (no lo selles herméticamente).
- El BMP180 responde a **cambios reales** de presión: abrir una puerta, el aire
  acondicionado o el ascensor se ven en la altitud.
- Si el bus I2C muestra flancos redondeados o glitches, revisa la longitud de los
  cables y que no haya pull-ups adicionales en la protoboard.
