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
| **P1** | ✅ **Implementada** | **LEDs y botones (4 modos)** | 3× LED + 2× Botones |
| **P2** | ✅ **Implementada** | **Potenciómetro ADC** | ADC |
| **P3** | ✅ **Implementada** | **Sensor temperatura (NTC o LM35)** | ADC + NTC/LM35 |
| **P4** | ✅ **Implementada** | **Sensor presión MPX5500DP (kPa)** | ADC + MPX5500DP |
| **P5** | ✅ **Implementada** | **Servomotor PWM 50 Hz** | Servo + ADC opcional |
| **P6** | ✅ **Implementada** | **Conmutación PWM + transistor** | PWM + ADC opcional |
| **P7** | ✅ **Implementada** | **Motor a pasos (4 modos)** | Stepper + endstop |
| **P8** | ✅ **Integrada** | **Sistema completo vuelo** | Todo integrado |

### P1: LEDs y Botones

Control básico de GPIO con 3 LEDs y 2 botones (pull-up interno, activo LOW).

**Características:**
- **LEDs**: Onboard + 2 externos (con resistencias 220-330Ω)
- **Botones**: Pull-up interno, activo LOW (contacto a GND)
- **4 modos interactivos**:
  1. Blink LED1 cada 1s
  2. Chaser 3 LEDs (secuencia 300ms)
  3. Monitor botones (reflejar estado en LED2/LED3)
  4. Integrado: BTN1 alterna patrón (chaser/blink-all), BTN2 cambia velocidad
- **Menú por serial**: Timeout 5s (default modo 4), 'm' para volver al menú

**Pines:**
- **ESP32**: LED1=GPIO2, LED2=GPIO4, LED3=GPIO5, BTN1=GPIO13, BTN2=GPIO14
- **RP2040**: LED1=GP25, LED2=GP16, LED3=GP17, BTN1=GP14, BTN2=GP15

### P2: Potenciómetro ADC

Lectura básica de ADC con normalización por plataforma.

**Características:**
- Salida: ADC RAW, Voltaje (3.3V), Porcentaje (0-100%)
- Frecuencia: 5 Hz (200 ms)
- Normalización automática: 12-bit (ESP32) vs 10-bit (RP2040)

### P3: Sensor de Temperatura (NTC o LM35)

Medición de temperatura con dos opciones de sensor seleccionables por menú.

**Características:**
- **Menú inicial**: Selección entre NTC Termistor o LM35

**Opción 1: NTC Termistor (10kΩ, Beta=3950)**
- **Divisor resistivo**: 3V3 → R_series 10kΩ → [nodo ADC] → NTC 10kΩ → GND
- **Conversión NTC**:
  1. ADC → Voltaje (normalizado por plataforma)
  2. Voltaje → R_NTC: `R_NTC = R_series × V_nodo / (V_supply - V_nodo)`
  3. R_NTC → Temperatura: `1/T = 1/T0 + (1/β) × ln(R/R0)` (ecuación Beta)
- **Parámetros NTC**: R0=10kΩ @ 25°C, Beta=3950 (típico)
- **4 modos NTC**:
  1. ADC crudo + Voltaje
  2. Resistencia NTC (Ω)
  3. Temperatura (°C)
  4. Monitor CSV: `t_ms,adc,v_node_v,r_ntc_ohm,t_c`

**Opción 2: LM35 (Sensor lineal 10mV/°C)**
- **Conexión directa**: LM35 Vout → [ADC] (Vs del LM35 a 3.3V o 5V)
- **Conversión LM35**: `T(°C) = Voltaje(V) × 100` (10mV/°C = 0.01V/°C)
- **Rango**: 0-100°C típico (LM35DZ), hasta 150°C en otras versiones
- **Nota**: Máxima precisión con Vs=5V (si usa 3.3V, precisión reducida)
- **3 modos LM35**:
  1. ADC crudo + Voltaje
  2. Temperatura (°C)
  3. Monitor CSV: `t_ms,adc,v_node_v,t_c`

**Configuración común:**
- **Promedio**: 16 muestras por lectura
- **Frecuencia**: 10 Hz (100 ms)
- **Menú interactivo**: 'm' vuelve al menú de modos del sensor actual (no re‑selecciona sensor)

### P4: Sensor Presión MPX5500DP

Sensor piezoresistivo de presión absoluta 20-520 kPa.

**Características:**
- **Transfer function**: `Vout = VS × (0.2 × P + 0.2)` donde P en kPa
- **Conversión inversa**: `P(kPa) = (Vout - Vmin) / sensitivity + Pmin`
- **Sensibilidad**: ~0.0052 V/kPa @ VS=3.3V
- **⚠ IMPORTANTE**: Sensor requiere VS=4.75-5.25V para especificación óptima
  - Con VS=3.3V funciona pero con menor precisión
  - Para máxima precisión: usar 5V + divisor de voltaje para ADC
- **3 modos seleccionables**:
  1. ADC crudo + Voltaje
  2. Voltaje del sensor
  3. Presión (kPa)
- **Promedio**: 50 muestras por lectura
- **Frecuencia**: 10 Hz (100 ms)

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

### P7: Motor a Pasos

Control completo de motor a pasos con soporte para A4988/DRV8825 (NEMA 17) y ULN2003 (28BYJ-48).

**Características:**
- **Conversión RPM → intervalo**: Cálculo automático de timing entre pasos
- **Endstop opcional**: Pull-up interno, activo LOW (contacto a GND)
- **4 modos interactivos**:
  1. **Jog manual**: '+' avanza, '-' retrocede paso a paso
  2. **Mover N pasos**: Número de pasos con RPM configurable (ej: 200, -200)
  3. **Barrido continuo**: Avanza hasta límite/endstop, retrocede, repite
  4. **Homing**: Buscar fin de carrera retrocediendo (requiere endstop)
- **Parámetros**: DEFAULT_RPM=60, STEPS_PER_REV=200 (NEMA 17)
- **Menú por serial**: Timeout 5s (default modo 4), 'm' para volver al menú

**Pines:**
- **A4988/DRV8825**: STEP=GPIO18/GP18, DIR=GPIO19/GP19, EN=GPIO5/GP5
- **ULN2003**: IN1-IN4 = GPIO26,25,33,32 (ESP32) o GP26,27,28,22 (RP2040)
- **Endstop**: GPIO4/GP4 (opcional)

**Selección de driver:**
- Edita `platformio.ini`: `-DSTEPPER_A4988` o `-DSTEPPER_ULN2003`

## Matriz de pines por práctica

### ESP32 DevKit v1

| P# | ADC (altitude) | ADC (otros) | Servo (aileron) | Servo (elevator) | PWM Motor | Endstop | Stepper | LEDs/Botones |
|----|----------------|-------------|-----------------|------------------|-----------|---------|---------|--------------|
| P1 | — | — | 4 (LED2) | 5 (LED3) | — | — | 13,14 (BTN1,BTN2) | LED1=GPIO2 |
| P2 | **34** | — | — | — | — | — | — | — |
| P3 | **34** | — | — | — | — | — | — | — |
| P4 | **34** | — | — | — | — | — | — | — |
| P5 | 34 (opt) | — | **18** | — | — | — | — | — |
| P6 | 34 (opt) | — | — | — | **18** | — | — | — |
| P7 | — | — | — | — | — | **4** | A4988: 18,19,5<br>ULN: 26,25,33,32 | — |
| P8 | **34** | 35,32,33 | **25** | **26** | **18** | **4** | A4988: 19,21,5<br>ULN: 26,25,33,32 | — |

**Nota P1**: Reusa campos de la tabla de pines de forma creativa (servo_aileron/elevator para LED2/LED3, a4988.step/dir para BTN1/BTN2)

### RP2040 (Raspberry Pi Pico)

| P# | ADC (altitude) | ADC (otros) | Servo (aileron) | Servo (elevator) | PWM Motor | Endstop | Stepper | LEDs/Botones |
|----|----------------|-------------|-----------------|------------------|-----------|---------|---------|--------------|
| P1 | — | — | 16 (LED2) | 17 (LED3) | — | — | 14,15 (BTN1,BTN2) | LED1=GP25 |
| P2 | **26** | — | — | — | — | — | — | — |
| P3 | **26** | — | — | — | — | — | — | — |
| P4 | **26** | — | — | — | — | — | — | — |
| P5 | 26 (opt) | — | **18** | — | — | — | — | — |
| P6 | 26 (opt) | — | — | — | **18** | — | — | — |
| P7 | — | — | — | — | — | **4** | A4988: 18,19,5<br>ULN: 26,27,28,22 | — |
| P8 | **26** | 27,28 | **14** | **15** | **13** | **4** | A4988: 18,19,5<br>ULN: 26,27,28,22 | — |

**Nota P1**: Reusa campos de la tabla de pines de forma creativa (servo_aileron/elevator para LED2/LED3, a4988.step/dir para BTN1/BTN2)

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
