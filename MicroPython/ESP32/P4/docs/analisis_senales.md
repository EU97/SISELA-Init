# Análisis de señales — Práctica 4 (BMP180)

El BMP180 es un sensor **digital** (I2C): no hay una señal analógica que inyectar con
el generador de funciones. El análisis de señales de esta práctica se hace sobre la
**serie temporal digital** que produce el sensor (presión / altitud) y sobre el **bus
I2C** con el osciloscopio.

Modos del firmware: **6) Análisis de ruido y muestreo** · **7) Filtro digital en vivo**.
Herramienta PC: [`tools/sisela_signal/`](../../../../tools/sisela_signal/README.md).

---

## 1. Fundamentos

### 1.1 Muestreo de un sensor lento
Cada `read_all()` del BMP180 hace 2 transacciones I2C y espera la conversión
sigma-delta: **~8 ms** (OSS=1) a **~26 ms** (OSS=3) por lectura completa. La Fs
práctica es de **5–30 Hz**. El modo 6 planifica las lecturas con `ticks_us`
(`siglab.BlockSampler`) y reporta:

- **Fs real** vs Fs solicitada (si pides más de la que el sensor puede dar, lo verás).
- **Jitter de muestreo** σ(Δt): variación del intervalo entre muestras.
- Si Fs es demasiado baja frente a un cambio rápido de altitud (subir en ascensor),
  la reconstrucción del perfil sufre **aliasing temporal**.

### 1.2 Ruido y resolución efectiva
La presión compensada tiene ruido (RMS ~3–6 Pa según OSS, *datasheet* Bosch). Cerca
del suelo **1 hPa ≈ 8.43 m**, así que 0.01 hPa de resolución ≈ **8.4 cm** por LSB.
El ruido de altitud se caracteriza con:

- **σ y RMS** de un bloque estático (modo 6, `siglab.Stats`).
- **Resolución efectiva** = log₂(rango / (√12 · σ)) — cuántos "bits" son estables.
- **PSD** (Welch) del bloque: forma del piso de ruido (¿blanco? ¿1/f?).
- **Desviación de Allan** vs tiempo de promediado: hasta qué punto promediar mejora
  la resolución antes de que domine la **deriva** (temperatura, meteo).

### 1.3 Filtrado
El modo 7 aplica en la placa media móvil / mediana / EMA y transmite `alt_raw` y
`alt_filt`. En la PC se compara:

- **Dominio del tiempo**: suavizado vs retardo de grupo.
- **Dominio de la frecuencia**: la media móvil de N tiene ceros en k·Fs/N;
  la EMA es un pasa-bajos de 1er orden con fc = Fs·α/(2π(1−α)).
- **Respuesta al escalón** (subir unas escaleras): tiempo de subida y sobre-oscilación
  del filtro elegido.

---

## 2. Equipo

| Equipo | Uso |
|---|---|
| Osciloscopio (2 canales) | temporización I2C en SDA/SCL |
| Analizador lógico (opcional) | decodificación de tramas I2C |
| — | *no se usa el generador de funciones en esta práctica* |

---

## 3. Procedimiento

### Caso A — Fs real y jitter (modo 6)
1. `oss` = 1 en `main.py` (`BMP_OSS`).
2. Menú → **6**. Fs = 5 Hz, N = 256.
3. Anota del reporte: Fs real, error %, jitter σ.
4. Repite con Fs = 20 Hz: observa que el firmware **no la alcanza** (error negativo
   grande) porque el sensor es más lento → **el límite de Nyquist efectivo lo pone
   el sensor, no el bucle**.
5. Guarda el CSV y en la PC:
   ```bash
   python -m sisela_signal spectrum     --file cap.csv --col alt_m --psd
   python -m sisela_signal characterize  --file cap.csv --col alt_m --mode allan
   ```

### Caso B — Ruido y OSS (modo 6)
1. Sensor quieto sobre la mesa (sin corrientes de aire).
2. Captura N = 512 con `oss` = 0, 1, 2, 3 (reinicia entre cada uno).
3. Tabla: OSS · σ_alt (m) · resolución efectiva · tiempo/lectura.
4. Verifica la relación **ruido ∝ 1/√(nº de muestras internas)** del *datasheet*.

### Caso C — Filtro y respuesta al escalón (modo 7)
1. Menú → **7**. Filtro = media móvil, N = 8.
2. Deja el sensor quieto 20 s, luego súbelo ~1 piso de escaleras y mantenlo.
3. Guarda el CSV. En la PC:
   ```bash
   python -m sisela_signal filter        --file cap.csv --col alt_raw --kind movavg --n 8 --bode
   python -m sisela_signal characterize   --file cap.csv --col alt_filt --mode step
   ```
4. Repite con mediana N=5 (mejor ante *spikes*) y EMA α=0.2. Compara retardo vs ruido.

### Caso D — Bus I2C con osciloscopio
1. CH1 → SCL, CH2 → SDA, pinzas a GND. Base 10 µs/div, trigger flanco de bajada en SDA.
2. Mide: frecuencia de SCL (~100 kHz), duración de una transacción de lectura,
   periodo entre transacciones (= 1/Fs del modo activo).
3. Relaciona el "tiempo muerto" del bus con el margen para subir Fs.

---

## 4. Tablas de registro

**Tabla 4-A — Muestreo**

| Fs solicitada (Hz) | Fs real (Hz) | error (%) | jitter σ (µs) | dropouts |
|---|---|---|---|---|
| 5 | | | | |
| 10 | | | | |
| 20 | | | | |

**Tabla 4-B — Ruido vs OSS**

| OSS | t/lectura (ms) | σ_alt (m) | RMS ruido (m) | resolución efectiva (bits/100 m) |
|---|---|---|---|---|
| 0 | | | | |
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

**Tabla 4-C — Filtros (respuesta al escalón de ~3 m)**

| Filtro | t. subida 10–90 % (s) | sobre-oscilación (%) | σ residual en reposo (m) |
|---|---|---|---|
| crudo | — | — | |
| media móvil N=8 | | | |
| mediana N=5 | | | |
| EMA α=0.2 | | | |

---

## 5. Gráficas requeridas

1. **Altitud vs tiempo** de un recorrido vertical (crudo + filtrado superpuestos).
2. **PSD** del ruido de altitud en reposo (escala log-log), para OSS=1 y OSS=3.
3. **Desviación de Allan** vs τ: identificar el mínimo (τ óptimo de promediado).
4. **Bode** de la media móvil N=8 y de la EMA α=0.2 (magnitud), marcando f₋₃dB.
5. Captura de osciloscopio de **una transacción I2C** con anotaciones (START, dirección,
   ACK, datos, STOP).

---

## 6. Preguntas

1. El sensor tarda ~8 ms por lectura a OSS=1. ¿Cuál es la frecuencia máxima de una
   señal de presión (p.ej. oscilación de una puerta) que podrías medir sin aliasing?
2. Promediar 10 lecturas reduce el ruido √10 ≈ 3.2×. ¿Por qué la desviación de Allan
   deja de bajar a partir de cierto τ?
3. La media móvil de N=8 a Fs=5 Hz, ¿qué frecuencias elimina por completo? ¿Qué
   retardo de grupo introduce en segundos?
4. Un filtro de mediana no es lineal. ¿En qué situación supera claramente a la media
   móvil? ¿Qué desventaja tiene frente a un escalón real?
5. Si subes Fs de 5 a 15 Hz manteniendo OSS=1, ¿mejora la resolución de altitud?
   Justifica con la PSD.
