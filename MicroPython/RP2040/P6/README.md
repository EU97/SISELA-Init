# Práctica 6 — Conmutación de potencia por PWM (transistor) (RP2040)

Control de potencia de cargas externas mediante PWM y transistor MOSFET/BJT. Incluye 4 modos de operación: On/Off, control manual, barrido y control por potenciómetro.

## 🔄 Versión RP2040

Esta es la **adaptación para RP2040** (Raspberry Pi Pico) de la práctica original ESP32. Los cambios principales son:
- **Pin PWM**: GP18 (PWM1 A) en lugar de GPIO18
- **Pin ADC**: GP26 (ADC0) en lugar de GPIO34
- **ADC 16 bits**: Control por potenciómetro **16× más suave**
- **Sin configuración ADC**: No requiere `atten()`, siempre 0–3.3V
- **PWM más estable**: Jitter ~1 ns (10× mejor que ESP32)
- **VSYS disponible**: 5V del USB para cargas <500 mA sin fuente externa

Ver [**GUIA_MIGRACION.md**](../../GUIA_MIGRACION.md) para detalles completos de traducción ESP32→RP2040.

## Objetivos

- Comprender la conmutación de potencia con transistores (MOSFET/BJT) en configuración de bajo lado.
- Generar PWM desde el RP2040 y relacionar ciclo de trabajo con potencia media en la carga.
- Seleccionar una frecuencia PWM adecuada según el tipo de carga.
- Implementar medidas de protección (diodo flyback para cargas inductivas) y cableado correcto (GND común).
- Aprovechar las ventajas del RP2040: PWM ultra estable, ADC 16-bit, VSYS.

## Materiales

| Cantidad | Componente | Especificación |
|----------|------------|----------------|
| 1 | Raspberry Pi Pico | RP2040 con MicroPython |
| 1 | MOSFET canal N | Compuerta lógica: AO3400, IRLZ44N, IRF540N |
| 1 | Resistencia 220 Ω | Limitación de corriente de compuerta |
| 1 | Diodo flyback | 1N5819 (Schottky) o 1N4007 para cargas inductivas |
| 1 | Carga | Tira LED, motor DC, lámpara 12V, ventilador, etc. |
| 1 | Fuente externa (opcional) | 5–12V adecuada a la carga (VSYS suficiente para <500 mA) |
| 1 | Potenciómetro (opcional) | 10 kΩ para control analógico |
| n | Cables y protoboard | — |

> **Ventaja RP2040**: Cargas pequeñas (<500 mA) pueden alimentarse desde **VSYS** (5V del USB) sin fuente externa. Cargas grandes requieren fuente externa con GND común.

## Conexiones

Ver detalle de pines en [**PINES.md**](PINES.md) y diagrama en [**assets/wiring.mmd**](assets/wiring.mmd).

Resumen rápido:

| Señal RP2040 | Pin | Destino | Descripción |
|--------------|-----|---------|-------------|
| GP18 | PWM1 A | Resistencia 220 Ω → Gate MOSFET | Señal PWM de control |
| GND | — | Source MOSFET + GND fuente | Tierra común **obligatoria** |
| VSYS (opcional) | 5V | +V carga (<500 mA) | Alimentación USB simplificada |
| GP26 (opcional) | ADC0 | Cursor potenciómetro | Control analógico de duty |

**Etapa de potencia** (bajo lado con MOSFET N):
```
+V fuente → Carga → Drenador (D) MOSFET
Fuente (S) MOSFET → GND común (RP2040 + fuente)
Diodo flyback: Cátodo a +V, Ánodo a Drenador
```

## Uso (Pymakr)

1. Abre la carpeta:
   ```
   MicroPython/RP2040/P6/
   ```
2. Conecta el Raspberry Pi Pico y selecciona el puerto COM en Pymakr.
3. Sincroniza y ejecuta:
   - "Sync project to device" (sube boot.py, main.py).
   - "Run" o reinicia la placa.
4. Interacción:
   - Aparece un menú con 4 modos.
   - Durante cualquier modo, escribe `m` + ENTER para volver al menú.

## Modos de operación

| Modo | Descripción | Salida típica |
|------|-------------|---------------|
| 1 | Encendido/Apagado | Alterna 0%/100% cada 1 segundo |
| 2 | PWM manual (0–100%) | `Ingresa duty %: 50` → `Aplicado duty = 50.0%` |
| 3 | Barrido 0→100→0 | Duty aumenta/disminuye continuamente |
| 4 | Control por potenciómetro | `ADC=32768 → Duty=50%` (control ultra suave) |
| q | Salir | Apaga PWM (duty 0%) y termina |

### Parámetros ajustables (main.py)

```python
ACT_PIN = 18                 # GP18 (PWM1 A)
PWM_FREQ = 1000              # Hz (ajustar según carga)
ADC_PIN = 26                 # GP26 (ADC0), potenciómetro opcional
```

**Guía de frecuencias**:
- **LED/Lámpara**: 100–1000 Hz (evitar parpadeo visible)
- **Motor DC**: 500–2000 Hz (compromiso eficiencia/ruido)
- **Electroválvula**: 50–200 Hz (evitar sobrecalentamiento)
- **Resistencia calefactora**: 10–100 Hz (inercia térmica alta)

**RP2040 ventaja**: Jitter <1 ns permite frecuencias hasta 20 kHz sin distorsión (PWM "silencioso" en motores).

## Verificación

1. **Arranque**: `[BOOT] P6 — Conmutación de potencia (PWM con transistor) (RP2040)`.
2. **Menú funcional**: Selección 1–4 responde correctamente.
3. **Modo 1 (On/Off)**: Carga enciende/apaga cada segundo.
4. **Modo 2 (Manual)**: Duty 0–100% controla intensidad/velocidad proporcionalmente.
5. **Modo 3 (Barrido)**: Carga aumenta/disminuye suavemente sin saltos.
6. **Modo 4 (Potenciómetro)**: Duty sigue la perilla **muy suavemente** (16-bit ADC).

**Criterio de éxito**: 
- Carga responde al PWM sin ruido electromagnético excesivo.
- MOSFET no se calienta (temperatura <60°C sin disipador).
- Control por potenciómetro es **16× más suave** que ESP32.
- Osciloscopio muestra PWM estable (jitter <10 ns).

## 🆚 Diferencias con ESP32

| Aspecto | ESP32 | RP2040 (esta práctica) |
|---------|-------|------------------------|
| **Pin PWM** | GPIO18 | GP18 (PWM1 A) |
| **Jitter PWM** | ~10 ns típico | **~1 ns típico** ✅ (10× mejor) |
| **Pin ADC** | GPIO34 (input-only) | GP26 (GPIO/ADC flexible) |
| **Resolución ADC** | 12 bits (0–4095) | **16 bits (0–65535)** ✅ |
| **Config ADC** | `atten(11dB)` requerido | **No requiere** ✅ |
| **Lectura ADC** | `adc.read()` | `adc.read_u16()` |
| **Suavidad potenciómetro** | 0.024%/bit | **0.0015%/bit** ✅ (16× mejor) |
| **Alimentación 5V** | Fuente externa siempre | **VSYS disponible** ✅ |
| **Pines PWM disponibles** | Todos GPIO excepto input-only | **16 pines PWM** (8 slices × 2) |

**Ventajas RP2040**: PWM ultra estable, control subporcentual con potenciómetro, alimentación simplificada, hasta 16 cargas PWM simultáneas.

## Teoría rápida: PWM y potencia

**Potencia media** en la carga:
```
P_media = V × I × (duty / 100)
```

**Ejemplo**: Motor 12V 1A con duty 50%:
```
P_media = 12V × 1A × 0.5 = 6W
```

**Disipación en MOSFET** (modo saturación):
```
P_mosfet = I² × R_ds(on)
```

**Ejemplo**: IRLZ44N (Rds(on)=0.022Ω), carga 1A:
```
P_mosfet = 1² × 0.022 = 22 mW → Sin disipador necesario ✅
```

Consulta [**docs/oscilograma.md**](docs/oscilograma.md) para formas de onda esperadas y medición con osciloscopio.

## Control ultra preciso con ADC de 16 bits

El RP2040 permite **control subporcentual** del duty con potenciómetro:

```python
# ESP32 (12-bit): 100% / 4095 = 0.024% por bit ADC
# RP2040 (16-bit): 100% / 65535 = 0.0015% por bit ADC ✅

# Ejemplo: Ajuste fino a 50.5% duty
# ESP32: 50.5% ≈ 2068 bits → 50.48% (error 0.02%)
# RP2040: 50.5% ≈ 33095 bits → 50.500% (error <0.001%) ✅
```

**Aplicaciones de precisión**:
- Control de intensidad lumínica (fotografía/video profesional)
- Regulación térmica de precisión (±0.1°C)
- Motores de posicionamiento fino
- Mezcla de gases/líquidos proporcional exacta

## Alimentación simplificada con VSYS

El RP2040 simplifica la alimentación para cargas pequeñas:

### Opción 1: VSYS (5V del USB)

**Cargas compatibles** (<500 mA):
- Tira LED pequeña (5V, <10 LEDs, ~150 mA)
- Ventilador 5V pequeño (40×40 mm, <200 mA)
- Relé 5V (bobina <100 mA)
- Motor DC mini (3–6V, <300 mA)

**Conexión**:
```
VSYS (pin 40) → +V carga
GP18 → 220Ω → MOSFET Gate
MOSFET Drain → GND carga
MOSFET Source → GND RP2040
```

### Opción 2: Fuente externa (5–48V)

**Necesaria para**:
- Motores DC grandes (>500 mA)
- Tiras LED 12V (>1A)
- Electroválvulas 12V/24V
- Cualquier carga >500 mA o >5V

**Conexión**:
```
Fuente +V → +V carga
GP18 → 220Ω → MOSFET Gate
MOSFET Drain → GND carga
MOSFET Source → GND RP2040 + GND fuente (común obligatorio)
```

## Proyectos avanzados con RP2040

### 1. Control de 16 cargas simultáneas
El RP2040 tiene **16 pines PWM** (8 slices × 2 canales):

```python
# main.py con múltiples salidas PWM
pwm_pins = [18, 19, 20, 21, 4, 5, 6, 7]  # 8 cargas
pwms = [PWM(Pin(p), freq=1000) for p in pwm_pins]

# Control sincronizado
for pwm in pwms:
    pwm.duty_u16(int(65535 * 0.5))  # 50% duty todas
```

### 2. Control de motor H-bridge (dirección + velocidad)
Usa 2 pines PWM para control bidireccional:

```python
# GP18 = PWM adelante, GP19 = PWM reversa
pwm_fwd = PWM(Pin(18), freq=2000)
pwm_rev = PWM(Pin(19), freq=2000)

def motor_control(speed):  # speed: -100 a +100
    if speed > 0:  # Adelante
        pwm_fwd.duty_u16(int(65535 * abs(speed) / 100))
        pwm_rev.duty_u16(0)
    elif speed < 0:  # Reversa
        pwm_fwd.duty_u16(0)
        pwm_rev.duty_u16(int(65535 * abs(speed) / 100))
    else:  # Freno
        pwm_fwd.duty_u16(0)
        pwm_rev.duty_u16(0)

motor_control(75)   # 75% adelante
motor_control(-50)  # 50% reversa
motor_control(0)    # Freno
```

### 3. Dimmer inteligente con curva gamma
Corrección gamma para LEDs (percepción visual no lineal):

```python
import math

def apply_gamma(duty_linear, gamma=2.2):
    """Aplica corrección gamma para LEDs."""
    duty_corrected = math.pow(duty_linear / 100.0, gamma) * 100
    return duty_corrected

# Ejemplo: Barrido con corrección gamma
for duty in range(0, 101, 5):
    duty_corrected = apply_gamma(duty)
    pwm.duty_u16(int(65535 * duty_corrected / 100))
    time.sleep_ms(100)
```

## Seguridad y buenas prácticas

### ⚠️ Obligatorio

1. **GND común**: GND del RP2040 y GND de la fuente externa **deben estar unidos**.
2. **Fuente externa**: NO alimentes cargas >100 mA desde 3V3 del RP2040.
3. **Diodo flyback**: Obligatorio para motores, relés, bobinas (cargas inductivas).
4. **Resistencia de compuerta**: 220 Ω recomendado para limitar corriente transitoria.
5. **Disipación térmica**: Si el MOSFET se calienta >60°C, añade disipador o reduce corriente.

### 🔧 Selección de MOSFET

**Para cargas hasta 2A** (sin disipador):
- AO3400 (SOT-23): 5.8A, Rds(on)=30mΩ @ 4.5V
- IRLZ44N (TO-220): 47A, Rds(on)=22mΩ @ 5V ✅ Recomendado

**Para cargas 2–10A** (con disipador):
- IRF540N (TO-220): 33A, Rds(on)=44mΩ @ 10V
- IRFZ44N (TO-220): 49A, Rds(on)=17.5mΩ @ 10V

**Criterio de selección**:
- **Vgs(th)** < 2V (encendido con 3.3V del RP2040)
- **Rds(on)** bajo para minimizar disipación
- **Id** > 2× corriente de carga (margen de seguridad)

## Limitaciones y notas

- **Carga USB**: Si usas VSYS, no excedas 500 mA total (RP2040 + carga + periféricos).
- **Ruido electromagnético**: Cargas inductivas generan picos de voltaje; verifica el diodo flyback.
- **Frecuencia audible**: Si la carga emite zumbido (500–2000 Hz), aumenta a >20 kHz o disminuye a <100 Hz.
- **Sobrecalentamiento**: Si el MOSFET se calienta, reduce duty o añade disipador.

## Recursos

- **Power Switching Theory**: [docs/oscilograma.md](docs/oscilograma.md)
- **RP2040 PWM Datasheet**: https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf (Sección 4.5)
- **MicroPython PWM RP2040**: https://docs.micropython.org/en/latest/rp2/quickref.html#pwm-pulse-width-modulation
- **MOSFET Selection Guide**: https://www.infineon.com/mosfet
- **Guía de migración ESP32→RP2040**: [GUIA_MIGRACION.md](../../GUIA_MIGRACION.md)