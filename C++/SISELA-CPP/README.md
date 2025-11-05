# SISELA-CPP — Proyecto unificado (PlatformIO)

Proyecto C++ unificado para ESP32 y RP2040 usando PlatformIO (framework Arduino). Un solo código fuente con selección de práctica y diferencias por plataforma vía `#ifdef` y `build_flags`.

## Requisitos
- VS Code + extensión PlatformIO IDE
- Placas: ESP32 DevKit v1 y/o Raspberry Pi Pico

## Estructura
```
SISELA-CPP/
├─ platformio.ini               # Configuración de entornos (ESP32 / RP2040)
├─ src/
│  ├─ main.cpp                  # Punto de entrada común
│  ├─ common/                   # Utilidades compartidas
│  └─ practices/                # Implementaciones P1..P8 (guardadas por PRACTICE)
├─ include/
│  ├─ board_config.h            # Selección de configuración por plataforma
│  ├─ config/esp32.h            # Pines / helpers ESP32
│  ├─ config/rp2040.h           # Pines / helpers RP2040
│  ├─ pins/                     # Mapa de pines por práctica y plataforma
│  │  ├─ pins_types.h           # Estructuras Pins/Stepper
│  │  ├─ pins.h                 # API para obtener pines actuales
│  │  ├─ pins_esp32.h           # Tabla de pines ESP32 (P1..P8)
│  │  └─ pins_rp2040.h          # Tabla de pines RP2040 (P1..P8)
│  └─ practices/practice.h      # Interface de prácticas (setup/loop)
├─ lib/                         # Librerías propias (si aplica)
└─ tools/
   └─ visualization/            # Scripts Python para graficar telemetría
```

## Seleccionar práctica y plataforma
- Edita `platformio.ini` y ajusta `build_flags = -DPRACTICE=N` con N ∈ [1..8].
- Compila/sube el entorno deseado:
  - ESP32: `env:esp32dev`
  - RP2040: `env:pico`

## Estado de las prácticas

| Práctica | Estado | Descripción | Hardware clave |
|----------|--------|-------------|----------------|
| P1 | ⚪ Template | LEDs y serial básico | LED onboard |
| P2 | ⚪ Template | Potenciómetro ADC | ADC |
| P3 | ⚪ Template | Sensor NTC temperatura | ADC |
| P4 | ⚪ Template | Sensor presión MPX5500DP | ADC |
| **P5** | ✅ **Implementada** | **Servomotor PWM 50 Hz** | Servo + ADC opcional |
| **P6** | ✅ **Implementada** | **Conmutación PWM + transistor** | PWM + ADC opcional |
| P7 | ⚪ Template | Motor a pasos (A4988/ULN2003) | Stepper + endstop |
| **P8** | ✅ **Integrada** | Sistema completo vuelo | Todo integrado |

### P5: Servomotor PWM

Control de servomotor R/C con señal PWM de 50 Hz (1000-2000 µs para 0-180°).

**Características:**
- **ESP32**: Usa librería `ESP32Servo` (instalada automáticamente)
- **RP2040**: Usa PWM nativo con `analogWriteFreq(50)` y `analogWriteRange(20000)`
- **Modos de operación**:
  1. Barrido automático 0-180-0° (por defecto)
  2. Control manual por ADC (potenciómetro en pin altitude si disponible)
- **Control por serial**: Envía '1' o '2' para cambiar modo

### P6: Conmutación de potencia

Control de carga (LED/motor/resistencia) mediante PWM + transistor MOSFET/BJT.

**Características:**
- **Frecuencia**: 1 kHz (típico para LEDs/motores, ajustable según carga)
- **Duty cycle**: 0-100% con resolución de 8 bits (0-255)
- **Modos de operación**:
  1. Rampa automática 0-100% duty (por defecto)
  2. Control manual por serial (enviar 0-100)
  3. Control por ADC (potenciómetro en pin altitude si disponible)
- **Control por serial**: 
  - Envía '1', '2', '3' para cambiar modo
  - En modo 2: envía valores 0-100 para ajustar duty directamente

**Notas de hardware:**
- Usa MOSFET canal N (AO3400, IRLZ44N) o BJT NPN (2N2222, TIP120)
- Resistencia 220Ω en compuerta/base recomendada
- **GND común obligatorio** entre microcontrolador y fuente de carga
- Diodo flyback (1N5819/1N4007) obligatorio para cargas inductivas

## Matriz de pines por práctica

### ESP32 DevKit v1

| P# | ADC (altitude) | ADC (otros) | Servo (aileron) | Servo (elevator) | PWM Motor | Endstop | Stepper |
|----|----------------|-------------|-----------------|------------------|-----------|---------|---------|
| P1 | — | — | — | — | — | — | — |
| P2 | **34** | — | — | — | — | — | — |
| P3 | **34** | — | — | — | — | — | — |
| P4 | **34** | — | — | — | — | — | — |
| P5 | 34 (opt) | — | **18** | — | — | — | — |
| P6 | 34 (opt) | — | — | — | **18** | — | — |
| P7 | — | — | — | — | — | **4** | A4988: 18,19,5<br>ULN: 26,25,33,32 |
| P8 | **34** | 35,32,33 | **25** | **26** | **18** | **4** | A4988: 19,21,5<br>ULN: 26,25,33,32 |

### RP2040 (Raspberry Pi Pico)

| P# | ADC (altitude) | ADC (otros) | Servo (aileron) | Servo (elevator) | PWM Motor | Endstop | Stepper |
|----|----------------|-------------|-----------------|------------------|-----------|---------|---------|
| P1 | — | — | — | — | — | — | — |
| P2 | **26** | — | — | — | — | — | — |
| P3 | **26** | — | — | — | — | — | — |
| P4 | **26** | — | — | — | — | — | — |
| P5 | 26 (opt) | — | **18** | — | — | — | — |
| P6 | 26 (opt) | — | — | — | **18** | — | — |
| P7 | — | — | — | — | — | **4** | A4988: 18,19,5<br>ULN: 26,27,28,22 |
| P8 | **26** | 27,28 | **14** | **15** | **13** | **4** | A4988: 18,19,5<br>ULN: 26,27,28,22 |

**Leyenda:**
- **(opt)**: Pin opcional para control manual con potenciómetro
- **A4988**: STEP, DIR, EN
- **ULN**: IN1, IN2, IN3, IN4
- **ADC (otros)**: speed, attitude, light según práctica

## Mapa de pines unificado

### Acceso a pines en código

- Los pines se definen por práctica y plataforma en `include/pins/pins_*.h`.
- Usa la función `pins()` o las macros de conveniencia (`PIN_SERVO_AILERON`, `PIN_PWM_MOTOR`, etc.).
- Selección del driver de stepper:
  - Por defecto se usa A4988 (`-DSTEPPER_A4988`).
  - Para ULN2003, usa `-DSTEPPER_ULN2003` en `build_flags` del entorno.

Ejemplo de uso:
```cpp
#include "pins/pins.h"
void setup(){
  if (PIN_SERVO_AILERON >= 0) pinMode(PIN_SERVO_AILERON, OUTPUT);
}
```

## Drivers comunes

En `src/common/` se incluyen drivers mínimos para:

- **FlightSensors** (`sensors.h`): Lectura de sensores analógicos (altitud, velocidad, actitud, luz).
  - `analogRead()` normalizado según resolución de cada plataforma.
  - ESP32: 12 bits (0–4095); RP2040: 10 bits (0–1023) en Arduino.

- **FlightControls** (`flight_controls.h`): Control de servos R/C con PWM de 50 Hz real.
  - ESP32: Usa `ESP32Servo` library con attach/write
  - RP2040: PWM nativo con `analogWriteFreq(50)` + `analogWrite(pulseWidth)`
  - Rango: 1000-2000 µs para 0-180°

- **PropulsionSystem** (`propulsion.h`): Control de motor/throttle mediante PWM.
  - `setThrottle(0-100)` traduce a duty cycle 0-255 con `analogWrite()`.
  - Frecuencia configurable por plataforma (1 kHz típico).

- **LandingGear** (`landing_gear.h`): Control de motor a pasos (A4988 o ULN2003) con sensor de fin de carrera.
  - Soporte para dos drivers: A4988 (pulsos STEP/DIR) y ULN2003 (secuencia de 8 pasos).
  - Homing automático con endstop (pull-up interno, activo en LOW).

## Configuración y uso
