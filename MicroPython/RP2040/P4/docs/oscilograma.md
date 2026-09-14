# Oscilograma y visualización — Práctica 4 (BMP180, RP2040)

El BMP180 es un sensor **digital I2C**: no hay una señal analógica de sensor que ver en
el osciloscopio. Lo que sí se observa es el **tráfico del bus I2C** (SDA/SCL) y, en la
PC, las **series temporales** de presión/altitud.

- Análisis de señales completo (ruido, muestreo, espectro, filtrado): ver
  [analisis_senales.md](analisis_senales.md).
- Altímetro visual tipo instrumento: `MicroPython/ESP32/P4/tools/altimeter_gui.py`
  (funciona con cualquier plataforma que emita el CSV del modo 4).

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
# fin  fs_real=5.01  jitter_us=310.40
```

### Modo 7 — Filtro digital en vivo
```csv
t_us,alt_raw,alt_filt
0,540.21,540.21
200100,540.19,540.20
```

---

## 2. Bus I2C en el osciloscopio

| Canal | Señal | Base de tiempo | Trigger |
|---|---|---|---|
| CH1 | **SCL** (GP1) | 10 µs/div | flanco de bajada |
| CH2 | **SDA** (GP0) | — | — |

Qué medir:

- **Frecuencia de SCL**: ≈ 100 kHz (`I2C_FREQ` en `main.py`; el RP2040 admite hasta 1 MHz).
- **Transacción de lectura**: START → `0x77`+W → ACK → registro → ACK → RESTART →
  `0x77`+R → ACK → datos → NACK → STOP.
- **Periodo entre transacciones**: igual a `1/Fs` del modo activo.
- **Nivel lógico**: 3.3 V (pull-ups de 4.7 kΩ del módulo GY-68).

---

## 3. Visualización en la PC

```bash
# Altímetro aeronáutico (modo 4)
cd ../../ESP32/P4/tools && pip install -r requirements.txt
python altimeter_gui.py --port /dev/ttyACM0

# Análisis de señales (modos 6–7)
pip install -r ../../../../tools/sisela_signal/requirements.txt
PYTHONPATH=../../../../tools python -m sisela_signal spectrum --file cap.csv --col alt_m --psd
PYTHONPATH=../../../../tools python -m sisela_signal characterize --file cap.csv --col alt_m --mode allan
```

---

## 4. Ventaja del RP2040

El BMP180 hace su propia conversión sigma-delta internamente, así que el ruido de
**presión** es idéntico en ambas plataformas (lo fija el sensor, no el ADC del MCU).
La ventaja del RP2040 aquí es la **planificación de muestreo** más determinista
(`ticks_us`, jitter bajo) para los modos 6–7, y la posibilidad de subir la frecuencia
del bus I2C.
