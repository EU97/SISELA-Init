# Práctica 5 — Control PWM para Servomotores (RP2040 + MicroPython)

Control de servomotores R/C (SG90, MG90S, MG996R, etc.) mediante PWM de 50 Hz. Incluye barrido, control manual por ángulo, prueba de pulso directo (us) y control con potenciómetro.

## 🔄 Versión RP2040

Esta es la **adaptación para RP2040** (Raspberry Pi Pico) de la práctica original ESP32. Los cambios principales son:
- **Pin PWM**: GP18 (PWM1 A) en lugar de GPIO18
- **Pin ADC**: GP26 (ADC0) en lugar de GPIO34
- **ADC 16 bits**: Control por potenciómetro **16× más suave**
- **Sin configuración ADC**: No requiere `atten()`, siempre 0–3.3V
- **VSYS disponible**: 5V del USB para servos pequeños sin fuente externa

Ver [**GUIA_MIGRACION.md**](../../GUIA_MIGRACION.md) para detalles completos de traducción ESP32→RP2040.

## Objetivos

- Configurar PWM a 50 Hz en el RP2040 para control de servos.
- Relacionar ancho de pulso (us) con ángulo (°) y realizar calibración básica.
- Implementar un menú interactivo con 4 modos prácticos.
- Aprovechar las ventajas del RP2040: PWM estable, ADC 16-bit, VSYS.

## Materiales

| Cantidad | Componente | Especificación |
|----------|------------|----------------|
| 1 | Raspberry Pi Pico | RP2040 con MicroPython |
| 1 | Servomotor | SG90/MG90S/MG996R u otro R/C estándar |
| 1 | Fuente 5V (opcional) | 1–2 A para servos grandes (VSYS suficiente para SG90) |
| 1 | Potenciómetro (opcional) | 10 kΩ para control analógico |
| n | Cables Dupont | Macho-hembra / macho-macho |

> **Ventaja RP2040**: Servos pequeños (SG90, MG90S) pueden alimentarse desde **VSYS** (5V del USB, hasta 500 mA) sin fuente externa. Servos grandes (MG996R) requieren fuente externa.

## Conexiones

Ver detalle de pines en [**PINES.md**](PINES.md) y diagrama en [**assets/wiring.svg**](assets/wiring.svg).

Resumen rápido:

| Señal RP2040 | Pin | Servomotor | Descripción |
|--------------|-----|------------|-------------|
| GP18 | PWM1 A | Señal (amarillo/blanco) | Control a 50 Hz |
| VSYS | 5V | VCC (rojo) | Alimentación (USB o externa) |
| GND | — | GND (negro/marrón) | Tierra común |
| GP26 (opcional) | ADC0 | Cursor potenciómetro | Control analógico de ángulo |

## Uso (Pymakr)

1. Abre la carpeta:
   ```
   MicroPython/RP2040/P5/
   ```
2. Conecta el Raspberry Pi Pico y selecciona el puerto COM en Pymakr.
3. Sincroniza y ejecuta:
   - "Sync project to device" (sube boot.py, main.py, lib/servo.py).
   - "Run" o reinicia la placa.
4. Interacción:
   - Aparece un menú con 4 modos.
   - Durante cualquier modo, escribe `m` + ENTER para volver al menú.

## Modos de operación

| Modo | Descripción | Salida típica |
|------|-------------|---------------|
| 1 | Barrido 0–180–0 | Movimiento suave ida/vuelta |
| 2 | Ángulo manual (0–180) | `Ángulo→ 90°  (pulso ~1500us)` |
| 3 | Pulso directo (us) | `Pulso→ 1800us` |
| 4 | Control por potenciómetro | `ADC=32768 →  90°` |
| q | Salir | — |

### Parámetros ajustables (main.py)

```python
SERVO_PIN = 18               # GP18 (PWM1 A)
SERVO_FREQ = 50              # Hz (20 ms)
SERVO_MIN_US = 500           # us (≈ 0°)
SERVO_MAX_US = 2400          # us (≈ 180°)
ANGLE_MIN = 0
ANGLE_MAX = 180

ADC_PIN = 26                 # GP26 (ADC0), potenciómetro opcional
```

> Nota: Algunos servos saturan antes de 0°/180°. Ajusta `SERVO_MIN_US`/`SERVO_MAX_US` hasta que el servo recorra seguro sin forzarse.

## Verificación

1. Arranque: `=== Práctica 5: Control PWM para Servomotores (RP2040) ===`.
2. Menú funcional: selección 1–4 y `q` responde.
3. Barrido: el servo oscila suave entre extremos sin vibración excesiva.
4. Manual: ángulos 0–180° posicionan de forma reproducible.
5. Potenciómetro: el ángulo sigue la perilla **de forma muy suave** (16-bit ADC).

**Criterio de éxito**: Servo recorre sin atascos, no se calienta, y mantiene posición acorde al ángulo pedido. **Movimiento más suave que ESP32** gracias al ADC de 16 bits en modo 4.

## 🆚 Diferencias con ESP32

| Aspecto | ESP32 | RP2040 (esta práctica) |
|---------|-------|------------------------|
| **Pin PWM** | GPIO18 | GP18 (PWM1 A) |
| **Jitter PWM** | ~10 ns típico | **~1 ns típico** ✅ (10× mejor) |
| **Pin ADC** | GPIO34 (input-only) | GP26 (GPIO/ADC flexible) |
| **Resolución ADC** | 12 bits (0–4095) | **16 bits (0–65535)** ✅ |
| **Config ADC** | `atten(11dB)` requerido | **No requiere** ✅ |
| **Lectura ADC** | `adc.read()` | `adc.read_u16()` |
| **Suavidad potenciómetro** | 0.044°/bit | **0.0027°/bit** ✅ (16× mejor) |
| **Alimentación 5V** | Fuente externa siempre | **VSYS disponible** ✅ |

**Ventajas RP2040**: PWM más estable, control por potenciómetro 16× más suave, alimentación simplificada para servos pequeños.

## Teoría rápida: PWM de servos

- Periodo fijo ≈ 20 ms (50 Hz).
- Ancho de pulso típico: 1.0 ms ≈ 0°, 1.5 ms ≈ 90°, 2.0 ms ≈ 180°.
- Algunos servos aceptan 0.5–2.4 ms para ampliar recorrido; otros no (cuidado).

Consulta [**docs/oscilograma.md**](docs/oscilograma.md) para forma de onda esperada y medición con osciloscopio.

## Control suave con ADC de 16 bits

El RP2040 permite control **subgrado** con potenciómetro:

```python
# ESP32 (12-bit): 180° / 4095 = 0.044° por bit ADC
# RP2040 (16-bit): 180° / 65535 = 0.0027° por bit ADC ✅

# Ejemplo: Detectar movimiento de 0.01° (imperceptible en ESP32)
delta_adc_rp2040 = int(0.01 / 0.0027)  # ~4 bits
delta_adc_esp32 = int(0.01 / 0.044)    # ~0 bits (no detectable)
```

## Alimentación de servos con VSYS

El RP2040 **simplifica** la alimentación para servos pequeños:

```
SG90 (mini servo):
- Idle: 10 mA
- Movimiento: 100–250 mA  
- Peak: 600 mA
- Fuente: VSYS (USB 5V) ✅ Suficiente

MG996R (servo de torque):
- Idle: 20 mA
- Movimiento: 500–900 mA
- Peak: 1500 mA
- Fuente: Externa 5V 2A ❌ VSYS insuficiente
```

**Conexión VSYS**:
```
Servo VCC → VSYS (pin 40 Pico)
Servo GND → GND (cualquier pin GND)
Servo Signal → GP18
```

## Herramientas (PC)

- `tools/servo_cli.py`: envía ángulos o pulsos por el puerto serie para pruebas rápidas desde el PC. Requiere `pyserial`.

Instalación (opcional):

```bash
pip install -r tools/requirements.txt
python tools/servo_cli.py --port COM5 --angle 90
```

## Proyectos avanzados con RP2040

### 1. Control multiservos (hasta 16)
El RP2040 tiene **8 PWM slices × 2 canales = 16 servos simultáneos**:

```python
servos = [
    Servo(18),  # PWM1 A
    Servo(19),  # PWM1 B
    Servo(20),  # PWM2 A
    Servo(21),  # PWM2 B
    # ... hasta GP26, GP27 (PWM5 A/B)
]

# Sincronización perfecta (jitter <1ns)
for s in servos:
    s.angle(90)
```

### 2. Trayectorias suaves (interpolación)
Aprovecha el ADC de 16 bits para movimientos cinematográficos:

```python
def smooth_move(servo, start, end, duration_ms, steps=100):
    """Movimiento suave con interpolación lineal."""
    for i in range(steps + 1):
        ratio = i / steps
        angle = start + (end - start) * ratio
        servo.angle(angle)
        time.sleep_ms(duration_ms // steps)

# Movimiento de 10 segundos ultra suave
smooth_move(servo, 0, 180, 10000, steps=1000)
```

### 3. Control PID con sensor de posición
Si el servo tiene feedback de posición (servo continuo modificado):

```python
def pid_control(servo, adc, target_angle, kp=1.0, ki=0.1, kd=0.05):
    """Control PID para tracking preciso."""
    integral = 0
    last_error = 0
    
    while True:
        current = adc.read_u16() / 65535 * 180  # Posición actual
        error = target_angle - current
        integral += error
        derivative = error - last_error
        
        output = kp * error + ki * integral + kd * derivative
        servo.angle(int(output))
        
        last_error = error
        time.sleep_ms(10)
```

## Limitaciones y notas

- **Carga USB**: Si usas VSYS, no excedas 500 mA total (servo + Pico + periféricos).
- **Servo bloqueado**: Si el servo no puede moverse, desconecta señal PWM para evitar daño.
- **Ruido eléctrico**: Servos grandes generan picos de corriente; usa condensador de filtro (470 µF) cerca del servo.
- **Calibración**: Cada servo tiene tolerancias; ajusta `SERVO_MIN_US` y `SERVO_MAX_US` experimentalmente.

## Recursos

- **Servo Control Theory**: [docs/oscilograma.md](docs/oscilograma.md)
- **RP2040 PWM Datasheet**: https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf (Sección 4.5)
- **MicroPython PWM RP2040**: https://docs.micropython.org/en/latest/rp2/quickref.html#pwm-pulse-width-modulation
- **Guía de migración ESP32→RP2040**: [GUIA_MIGRACION.md](../../GUIA_MIGRACION.md)