# PINES — P6 Conmutación de potencia (PWM + transistor) (RP2040)

Conexiones principales en RP2040 (Raspberry Pi Pico) y etapa de potencia:

## Configuración RP2040

| Señal | Pin | Función | Descripción |
|-------|-----|---------|-------------|
| GP18 | PWM1 A | Señal PWM | Control de compuerta/base del transistor |
| GP26 | ADC0 | ADC opcional | Potenciómetro (cursor) para control analógico |
| GND | — | Tierra común | **Obligatorio**: GND del RP2040 + fuente externa |
| VSYS | — | 5V (opcional) | Disponible para cargas <500 mA |

## Conexiones de potencia

**Etapa de conmutación (bajo lado con MOSFET canal N)**:

```
GP18 → Resistencia 220 Ω → Compuerta (G) MOSFET
GND (RP2040) → Fuente (S) MOSFET → GND fuente externa (común)
Drenador (D) MOSFET → Extremo negativo de la carga
+V fuente externa → Extremo positivo de la carga
```

**Diodo flyback** (obligatorio para cargas inductivas):
- Cátodo (banda) → +V (positivo de la carga)
- Ánodo → Drenador (D) del MOSFET
- Diodo recomendado: 1N5819 (Schottky, bajo Vf) o 1N4007

**Potenciómetro opcional** (modo 4):
```
3V3 (RP2040) → Terminal 1 del potenciómetro
GND (RP2040) → Terminal 3 del potenciómetro
GP26 (ADC0) → Cursor (terminal 2)
```

## 🆚 Comparación con ESP32

| Aspecto | ESP32 | RP2040 (esta práctica) |
|---------|-------|------------------------|
| **Pin PWM** | GPIO18 | GP18 (PWM1 A) |
| **Pin ADC** | GPIO34 (input-only) | GP26 (GPIO/ADC flexible) |
| **Resolución ADC** | 12 bits (0–4095) | **16 bits (0–65535)** ✅ |
| **Config ADC** | `atten(11dB)` requerido | **No requiere** ✅ |
| **Lectura ADC** | `adc.read()` | `adc.read_u16()` |
| **Suavidad control** | 0.024%/bit (2.44 mV) | **0.0015%/bit (0.05 mV)** ✅ |
| **Jitter PWM** | ~10 ns típico | **~1 ns típico** ✅ (10× mejor) |
| **Alimentación 5V** | Fuente externa siempre | **VSYS disponible** ✅ (cargas <500 mA) |

**Ventajas RP2040**: 
- PWM 10× más estable → menos ripple electromagnético
- ADC 16× más suave → control por potenciómetro ultra preciso
- VSYS simplifica alimentación de cargas pequeñas

## Notas de seguridad y buenas prácticas

### ⚠️ Obligatorio

1. **GND común**: GND del RP2040 y GND de la fuente externa **deben estar unidos**.
2. **Fuente externa**: NO alimentes cargas >100 mA desde 3V3 del RP2040.
3. **Diodo flyback**: Obligatorio para motores, relés, bobinas (cargas inductivas).
4. **Resistencia de compuerta**: 220 Ω recomendado para limitar corriente transitoria.

### 🔧 Selección de transistor

**MOSFET canal N** (recomendado):
- Modelos de compuerta lógica (Vgs(th) < 2V): AO3400, IRLZ44N, IRF540N
- Verifica Vgs(on) en datasheet (debe ser ≤3V para saturación con 3.3V del RP2040)
- Corriente continua (Id) > corriente de carga con margen 2×
- Disipación: Calcular Pd = Id² × Rds(on)

**BJT NPN** (alternativa):
- Modelos: 2N2222, TIP120 (Darlington), BC548 (cargas <100 mA)
- Resistencia base: R = (3.3V - 0.7V) / (Ic / hFE)
- Ejemplo: Carga 500 mA, hFE=50 → Ib=10 mA → R=260 Ω (usar 220 Ω estándar)

### ⚙️ Ajuste de frecuencia PWM

| Tipo de carga | Frecuencia recomendada | Notas |
|---------------|------------------------|-------|
| LED / Lámpara | 100–1000 Hz | Evitar parpadeo visible (>100 Hz) |
| Motor DC | 500–2000 Hz | Compromiso: eficiencia vs ruido audible |
| Electroválvula | 50–200 Hz | Frecuencias bajas evitan sobrecalentamiento |
| Resistencia calefactora | 10–100 Hz | Baja frecuencia suficiente (inercia térmica) |

**RP2040 ventaja**: Jitter <1 ns permite usar frecuencias altas (hasta 20 kHz) sin distorsión, ideal para PWM silencioso en motores.

### 🔬 Cálculos de potencia

**Potencia media en la carga**:
```
P_media = V_carga × I_carga × (duty / 100)
```

**Ejemplo**: Motor 12V 1A, duty 50%:
```
P_media = 12V × 1A × 0.5 = 6W
```

**Disipación en MOSFET** (saturación):
```
P_mosfet = I_d² × R_ds(on)
```

**Ejemplo**: IRLZ44N (Rds(on)=0.022Ω), carga 1A:
```
P_mosfet = 1² × 0.022 = 0.022W (22 mW) → Sin disipador
```

### 🌡️ Temperatura y disipación

- **Sin disipador**: Hasta ~500 mW (TO-220) / ~150 mW (SOT-23)
- **Con disipador pequeño**: Hasta ~2W (TO-220)
- **Temperatura máxima**: 150°C (típico Tj max)
- **Margen de seguridad**: 2× la potencia calculada

**Consejo**: Toca el transistor después de 30 segundos de operación. Si quema, añade disipador o reduce corriente.

## Pines RP2040 compatibles con PWM

El RP2040 tiene **8 PWM slices × 2 canales (A/B)** = 16 pines PWM:

| PWM Slice | Canal A | Canal B | Notas |
|-----------|---------|---------|-------|
| PWM0 | GP0 | GP1 | — |
| PWM1 | **GP18** ✅ | GP19 | **Usado en esta práctica** |
| PWM2 | GP4 | GP5 | — |
| PWM3 | GP6 | GP7 | — |
| PWM4 | GP8 | GP9 | — |
| PWM5 | GP10 | GP11 | — |
| PWM6 | GP12 | GP13 | — |
| PWM7 | GP14 | GP15 | — |

**Ventaja**: Puedes controlar hasta **16 cargas simultáneas** con PWM independientes.

## Alimentación de cargas con VSYS

El RP2040 permite alimentar **cargas pequeñas** desde VSYS:

### Opción 1: VSYS (5V del USB)

**Cargas compatibles** (<500 mA):
- Tira LED pequeña (5V, <10 LEDs)
- Ventilador 5V pequeño (40×40 mm, <200 mA)
- Relé 5V (bobina <100 mA)

**Conexión**:
```
VSYS (pin 40) → +V carga
GP18 → 220Ω → MOSFET G
MOSFET D → GND carga
MOSFET S → GND RP2040
```

**Límites**:
- **Corriente máxima**: 500 mA (límite USB)
- **Cargas incompatibles**: Motores >500 mA, tiras LED >10 LEDs, electroimanes

### Opción 2: Fuente externa (5–48V)

**Necesaria para**:
- Motores DC grandes (>500 mA)
- Tiras LED 12V
- Electroválvulas 12V/24V
- Cualquier carga >500 mA o >5V

**Conexión**:
```
Fuente +V → +V carga
GP18 → 220Ω → MOSFET G
MOSFET D → GND carga
MOSFET S → GND RP2040 + GND fuente (común)
```

## Control preciso con ADC de 16 bits

El RP2040 permite **control subporcentual** del duty con potenciómetro:

```python
# ESP32 (12-bit): 100% / 4095 = 0.024% por bit ADC
# RP2040 (16-bit): 100% / 65535 = 0.0015% por bit ADC ✅

# Ejemplo: Ajuste fino a 50.5% duty
# ESP32: 50.5% ≈ 2068 bits → 50.48% (error 0.02%)
# RP2040: 50.5% ≈ 33095 bits → 50.500% (error <0.001%) ✅
```

**Aplicaciones de precisión**:
- Control de intensidad lumínica en fotografía/video
- Regulación térmica de precisión (±0.1°C)
- Motores de posicionamiento fino
- Mezcla de gases/líquidos con proporcionalidad exacta

## Recursos

- **RP2040 Datasheet** (Sección 4.5 PWM): https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf
- **MicroPython PWM RP2040**: https://docs.micropython.org/en/latest/rp2/quickref.html#pwm-pulse-width-modulation
- **MOSFET Selection Guide**: https://www.infineon.com/mosfet
- **Guía de migración ESP32→RP2040**: [../../GUIA_MIGRACION.md](../../GUIA_MIGRACION.md)
