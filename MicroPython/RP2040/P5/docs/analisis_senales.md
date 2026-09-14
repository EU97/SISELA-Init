# Análisis de señales — Práctica 5 (Servo PWM)

Esta práctica sí usa el **generador de funciones** (señal senoidal hacia el ADC) y el
**osciloscopio** (medida del tren de pulsos PWM). Cubre los cuatro paradigmas:
muestreo/aliasing, análisis espectral, filtrado (respuesta en frecuencia del lazo) y
caracterización (jitter del PWM, respuesta al escalón).

Modos del firmware: **5) Jitter de PWM** · **6) Muestreo y aliasing (ADC)** ·
**7) Respuesta al escalón del servo-lazo**.
Herramienta PC: [`tools/sisela_signal/`](../../../../tools/sisela_signal/README.md).

---

## 1. Fundamentos

### 1.1 El PWM como señal periódica
El servo espera un pulso cada **20 ms** (50 Hz) de ancho 1.0–2.0 ms. Visto como señal,
su espectro es una serie de armónicos de 50 Hz cuya amplitud depende del *duty*
(≈ 2.5–12.5 %). El **jitter** del flanco (variación del ancho de pulso entre periodos)
es el parámetro de calidad clave: se traduce en micro-vibración del eje.

- **ESP32 (LEDC)**: σ del ancho de pulso ~ **100 ns**.
- **RP2040 (PWM slice)**: σ ~ **10 ns** (≈10× mejor).

Se mide con el osciloscopio (*Measure → Pulse Width → StdDev*, o histograma) y se
procesa el CSV exportado con `sisela_signal characterize --scope`.

### 1.2 Muestreo y aliasing (modo 6)
Se inyecta un **seno del generador** (0–3.3 V, offset +1.65 V) en el pin ADC y se
muestrea a una Fs elegida (`siglab.BlockSampler`). Barriendo la frecuencia del
generador:

| f generador | relación con Fs/2 | qué se observa |
|---|---|---|
| f < Fs/2 | banda base | el pico aparece en f (correcto) |
| f = Fs/2 | Nyquist | 2 muestras/ciclo, amplitud incierta |
| Fs/2 < f < Fs | 2ª zona | **alias** en Fs − f |
| f = Fs | — | alias en DC (señal "congelada") |

`alias_frequency(f, Fs) = |((f + Fs/2) mod Fs) − Fs/2|`.

### 1.3 Caracterización del ADC (modo 6)
Con un seno limpio del generador (coherente si es posible), la FFT da:
**THD, SNR, SINAD, ENOB = (SINAD − 1.76)/6.02, SFDR**. Compara:

- **ESP32**: 12 bit nominal, ENOB real ~9–10 (no linealidad del ADC SAR).
- **RP2040**: 12 bit efectivos empacados en 16, ENOB real ~8.7 (*datasheet*).

### 1.4 Respuesta al escalón del servo-lazo (modo 7)
El servo es un lazo cerrado (motor + reductora + potenciómetro + comparador). Con un
potenciómetro de realimentación acoplado al eje → ADC, se comanda un escalón de ángulo
y se mide la posición real: **tiempo de subida, sobre-oscilación, tiempo de
establecimiento, τ, ancho de banda**. Es el análogo de laboratorio de la dinámica de
un actuador *fly-by-wire*.

---

## 2. Equipo

| Equipo | Uso |
|---|---|
| Generador de funciones | seno hacia el ADC (modo 6). Amplitud ≤ 2 Vpp, **offset +1.65 V**, salida HighZ |
| Osciloscopio (2 canales) | CH1 = señal PWM del servo (GP18); CH2 = ADC/realimentación |
| Potenciómetro 10 kΩ | realimentación de posición al eje del servo (modo 7) |
| Fuente 5 V dedicada | alimentación del servo (nunca desde el pin del MCU) |

> ⚠️ **Antes de conectar el generador al ADC**, verifica con el osciloscopio que la
> señal completa está dentro de **0–3.3 V**. Un pico negativo daña el pin.

---

## 3. Procedimiento

### Caso A — Jitter de PWM (modo 5)
1. Menú → **5**, pulso 1500 µs, 30 s.
2. Osciloscopio: CH1 en la señal del servo, 1 ms/div, trigger flanco subida ~1.5 V.
3. *Measure → Pulse Width* con estadística. Anota Min / Max / Mean / StdDev.
4. Exporta 1 captura larga a CSV y en la PC:
   ```bash
   python -m sisela_signal characterize --scope --file scopeCH1.csv --col CH1 --mode adc
   ```
5. Repite en la otra plataforma (ESP32 ↔ RP2040) y compara σ.

### Caso B — Aliasing con el generador (modo 6)
1. Generador: seno 1.0 Vpp, offset 1.65 V, 300 Hz. Verifica con el osciloscopio.
2. Conecta a GP26 (RP2040). Menú → **6**, Fs = 2000 Hz, N = 2048.
3. Guarda el CSV. En la PC:
   ```bash
   python -m sisela_signal spectrum --file cap.csv --col v --metrics --full-scale 3.3
   python -m sisela_signal alias    --file cap.csv --true-f 300
   ```
4. Sube la frecuencia del generador: 900, 1000, 1100, 1700, 2100, 3000 Hz.
   Para cada una anota **f real** (generador) y **f aparente** (pico del espectro).
5. Comprueba que f aparente = `alias_frequency(f_real, 2000)`.

### Caso C — ENOB del ADC (modo 6)
1. Generador: seno de la mayor amplitud que quepa en 0.1–3.2 V (≈ 3.1 Vpp, offset 1.65 V),
   frecuencia ~ Fs/10 (p.ej. 200 Hz con Fs=2000).
2. Menú → **6**, Fs = 2000, N = 4096. Guarda el CSV.
   ```bash
   python -m sisela_signal characterize --file cap.csv --col v --mode adc --full-scale 3.3
   ```
3. Anota THD, SNR, SINAD, ENOB, SFDR. Compara con el *datasheet* (ENOB nominal).

### Caso D — Respuesta al escalón del servo-lazo (modo 7)
1. Acopla un potenciómetro al eje del servo, cursor → ADC, extremos a 3V3 y GND.
2. Menú → **7**. Ángulos 60 → 120, Fs = 500, N = 500.
3. Guarda el CSV. En la PC:
   ```bash
   python -m sisela_signal characterize --file step.csv --col v --mode step
   ```
4. Repite el escalón 90 → 95 (pequeño) y 30 → 150 (grande). ¿Es lineal la dinámica?

### Caso E — Bode del actuador (opcional)
Comanda ángulos senoidales (amplitud 20° alrededor de 90°) a 0.2, 0.5, 1, 2, 5 Hz
(un modo manual o `servo_cli.py`), captura la realimentación en cada frecuencia y:
```bash
python -m sisela_signal bode --amp-in 20 --point 0.2:c02.csv --point 0.5:c05.csv ...
```

---

## 4. Tablas de registro

**Tabla 5-A — Jitter de PWM**

| Plataforma | pulso nominal (µs) | Mean (µs) | StdDev (ns) | pico-a-pico (ns) |
|---|---|---|---|---|
| ESP32 | 1500 | | | |
| RP2040 | 1500 | | | |

**Tabla 5-B — Aliasing (Fs = 2000 Hz)**

| f generador (Hz) | zona de Nyquist | f aparente medida (Hz) | alias teórico (Hz) |
|---|---|---|---|
| 300 | 1 | | 300 |
| 900 | 1 | | 900 |
| 1100 | 2 | | 900 |
| 1700 | 2 | | 300 |
| 2100 | 3 | | 100 |
| 3000 | 3 | | 1000 |

**Tabla 5-C — ENOB del ADC**

| Plataforma | THD (%) | SNR (dB) | SINAD (dB) | ENOB (bits) | SFDR (dB) |
|---|---|---|---|---|---|
| ESP32 | | | | | |
| RP2040 | | | | | |

**Tabla 5-D — Respuesta al escalón**

| escalón | t. subida (ms) | sobre-oscilación (%) | t. estab. ±2 % (ms) | τ (ms) |
|---|---|---|---|---|
| 60→120 | | | | |
| 90→95 | | | | |
| 30→150 | | | | |

---

## 5. Gráficas requeridas

1. **Histograma de ancho de pulso** del PWM (ESP32 vs RP2040) en el mismo eje.
2. **Espectro de la captura del ADC** con el generador a 1100 Hz y Fs = 2000 Hz,
   marcando el pico de alias en 900 Hz y la línea de Nyquist.
3. **f aparente vs f real** (diagrama de plegado) con los puntos medidos de la Tabla 5-B.
4. **FFT del seno del ADC** con los marcadores de armónicos (para el ENOB).
5. **Respuesta al escalón** del servo-lazo con las anotaciones de tr, OS y ts.

---

## 6. Preguntas

1. El PWM del servo es de 50 Hz. Si muestrearas esa señal con el ADC a 80 Hz, ¿qué
   frecuencia aparente verías? ¿Y a 100 Hz exactos?
2. ¿Por qué el jitter de 100 ns del ESP32 produce vibración visible en el servo y el
   de 10 ns del RP2040 no? Relaciónalo con la resolución angular (0.029°/bit).
3. Un ADC de 12 bits tiene ENOB ≈ 9. ¿Dónde se han "perdido" los 3 bits? ¿Ruido,
   no linealidad, jitter de apertura?
4. Con Fs = 2000 Hz, un tono de 2100 Hz aparece en 100 Hz. ¿Cómo lo distinguirías de
   un tono real de 100 Hz sin cambiar la frecuencia del generador?
5. La respuesta al escalón del servo, ¿es de 1er o 2º orden? ¿Cómo lo deduces de la
   sobre-oscilación y del ajuste de τ?
6. Si añades un filtro de media móvil al comando de ángulo (para "suavizar" el
   movimiento), ¿qué le pasa al ancho de banda del actuador?
