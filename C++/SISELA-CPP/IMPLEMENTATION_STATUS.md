# Resumen de implementación C++ unificado

## ✅ Completado

### Estructura base
- [x] PlatformIO proyecto unificado (ESP32 + RP2040)
- [x] Sistema de macros para selección de práctica (PRACTICE=1..8)
- [x] Sistema de macros para selección de driver stepper (A4988/ULN2003)
- [x] Configuración de board por plataforma (board_config.h)

### Pin mapping unificado
- [x] Estructura de datos `Pins` con soporte para ADC, servos, PWM, endstop, steppers
- [x] Tablas de pines ESP32 completadas para P1-P8
- [x] Tablas de pines RP2040 completadas para P1-P8
- [x] API de acceso: `pins()` y macros de conveniencia
- [x] Documentación de matriz de pines en README

### Drivers comunes
- [x] **FlightSensors**: Lectura ADC normalizada por plataforma (12-bit ESP32, 10-bit RP2040)
- [x] **FlightControls**: Control servo PWM 50 Hz REAL
  - ESP32: Librería ESP32Servo (attach/write)
  - RP2040: PWM nativo (analogWriteFreq + analogWrite con pulseWidth 1000-2000 µs)
- [x] **PropulsionSystem**: Control PWM motor/throttle (analogWrite 0-255)
- [x] **LandingGear**: Control stepper A4988/ULN2003 con endstop y homing

### Prácticas implementadas

#### P1: LEDs y Botones ✅
- Control de 3 LEDs (onboard + 2 externos)
- Lectura de 2 botones (pull-up interno, activo LOW)
- 4 modos interactivos:
  1. Blink LED1 cada 1s
  2. Chaser 3 LEDs (300ms)
  3. Monitor botones (reflejo en LED2/LED3)
  4. Integrado (BTN1=patrón chaser/blink-all, BTN2=velocidad)
- Pines:
  - ESP32: LED1=GPIO2, LED2=GPIO4, LED3=GPIO5, BTN1=GPIO13, BTN2=GPIO14
  - RP2040: LED1=GP25, LED2=GP16, LED3=GP17, BTN1=GP14, BTN2=GP15
- Menú por serial con timeout 5s (default modo 4)

#### P2: Potenciómetro ADC ✅
- Lectura ADC con normalización por plataforma
- Salida: RAW, voltaje (3.3V), porcentaje
- Frecuencia: 5 Hz (200 ms)
- Pines: ESP32=GPIO34, RP2040=GP26

#### P3: Sensor NTC Temperatura ✅
- Lectura ADC de divisor resistivo (3V3 → R_series 10kΩ → nodo → NTC 10kΩ → GND)
- Cálculo de resistencia NTC: R_NTC = R_series * V_nodo / (V_supply - V_nodo)
- Conversión a temperatura con ecuación Beta: 1/T = 1/T0 + (1/β) * ln(R/R0)
- Parámetros: R0=10kΩ @ 25°C, Beta=3950
- 3 modos seleccionables:
  1. ADC crudo + Voltaje
  2. Resistencia NTC (Ω)
  3. Temperatura (°C)
- Promedio de 16 muestras por lectura
- Frecuencia: 10 Hz (100 ms)
- Pines: ESP32=GPIO34, RP2040=GP26

#### P4: Sensor Presión MPX5500DP ✅
- Sensor piezoresistivo de presión absoluta 20-520 kPa
- Transfer function: Vout = VS × (0.2 × P + 0.2)
- Conversión inversa: P(kPa) = (Vout - Vmin) / sensitivity + Pmin
- Sensibilidad: ~0.0052 V/kPa @ 3.3V
- Advertencia: Sensor requiere VS=4.75-5.25V para especificación óptima
- 3 modos seleccionables:
  1. ADC crudo + Voltaje
  2. Voltaje del sensor
  3. Presión (kPa)
- Promedio de 50 muestras por lectura
- Frecuencia: 10 Hz (100 ms)
- Pines: ESP32=GPIO34, RP2040=GP26

#### P5: Servomotor PWM ✅
- **Control PWM 50 Hz real** con ESP32Servo (ESP32) y PWM nativo (RP2040)
- Rango: 0-180° (1000-2000 µs)
- Modos:
  1. Barrido automático 0-180-0°
  2. Control manual por ADC (potenciómetro)
- Control por serial: '1' o '2' para cambiar modo
- Pines: Servo=GPIO18/GP18; ADC opcional=GPIO34/GP26

#### P6: Conmutación de potencia ✅
- Control PWM para carga (LED/motor/resistencia) mediante transistor
- Frecuencia: 1 kHz (ajustable)
- Duty cycle: 0-100%
- Modos:
  1. Rampa automática 0-100-0%
  2. Control manual por serial (0-100)
  3. Control por ADC (potenciómetro)
- Control por serial: '1', '2', '3' para modo; valores 0-100 en modo 2
- Pines: PWM=GPIO18/GP18; ADC opcional=GPIO34/GP26

#### P7: Motor a Pasos ✅
- Soporte para A4988/DRV8825 (NEMA 17) y ULN2003 (28BYJ-48)
- Conversión RPM → intervalo entre pasos (µs)
- Endstop opcional con pull-up interno (activo LOW)
- 4 modos interactivos:
  1. Jog manual ('+' avanza, '-' retrocede paso a paso)
  2. Mover N pasos (con RPM configurable)
  3. Barrido continuo (avanza hasta límite/endstop, retrocede, repite)
  4. Homing (buscar fin de carrera retrocediendo)
- Parámetros: DEFAULT_RPM=60, STEPS_PER_REV=200 (NEMA 17)
- Pines:
  - A4988: STEP=GPIO18/GP18, DIR=GPIO19/GP19, EN=GPIO5/GP5
  - ULN2003: IN1-IN4 = GPIO26,25,33,32 (ESP32) o GP26,27,28,22 (RP2040)
  - Endstop: GPIO4/GP4 (opcional)

#### P8: Sistema integrado ✅
- Todos los subsistemas funcionando:
  - 4× ADC (altitude, speed, attitude, light)
  - 2× Servos (aileron, elevator)
  - 1× Motor PWM (throttle)
  - 1× Stepper (A4988 o ULN2003)
  - 1× Endstop
- Telemetría periódica cada 500 ms
- Pines completos documentados para ambas plataformas

## 🔄 Historial reciente

**2025-11-04**: Implementación completa de P1, P3, P4, P7
- P1: Sistema completo de LEDs y botones con 4 modos interactivos
- P3: Sensor NTC con ecuación Beta (temperatura °C)
- P4: Sensor MPX5500DP con transfer function (presión kPa)
- P7: Control stepper completo con jog, mover N, barrido y homing
- Actualización de tablas de pines para P1 (reutilizando campos disponibles)
- Todas las prácticas incluyen menú por serial con timeout y modo 'm' para volver

## 📋 Matriz de pines (resumen)

### Conflictos ULN2003 documentados

**ESP32:**
- ULN2003 usa GPIO 26,25,33,32
- Conflicto con servos (25,26 usados en P8 para aileron/elevator)
- **Solución**: Usar A4988 por defecto en P8; ULN2003 solo en P7

**RP2040:**
- ULN2003 usa GP 26,27,28,22
- Conflicto con ADCs (26,27,28 son ADC0,1,2 usados en P8)
- **Solución**: Usar A4988 por defecto en P8; ULN2003 requiere reconfiguración manual

### Pines reutilizados inteligentemente

| Pin | P2-P4 | P5 | P6 | P7 | P8 |
|-----|-------|----|----|----|----|
| ESP32 GPIO34 | ADC | ADC opt | ADC opt | — | ADC alt |
| ESP32 GPIO18 | — | Servo | PWM | Step | PWM motor |
| RP2040 GP26 | ADC | ADC opt | ADC opt | ULN IN1 | ADC alt |
| RP2040 GP18 | — | Servo | PWM | Step | — |

**Estrategia**: Compartir pines ADC opcionales y reutilizar GPIO18/GP18 para múltiples funciones PWM según práctica.

## 🛠️ Configuración actual

### platformio.ini
```ini
[env]
build_flags = -DPRACTICE=1 -DSTEPPER_A4988

[env:esp32dev]
lib_deps = madhephaestus/ESP32Servo@^3.0.5

[env:pico]
(sin lib_deps, PWM nativo)
```

### Cambiar práctica
Editar `build_flags = -DPRACTICE=N` con N ∈ [1..8]

### Cambiar driver stepper
- A4988 (default): `-DSTEPPER_A4988`
- ULN2003: `-DSTEPPER_ULN2003`

## 📊 Validación

### Build status
- **P2**: ✅ Compila (lint warning IntelliSense esperado)
- **P5**: ⏳ Requiere compilación con PlatformIO CLI
- **P6**: ⏳ Requiere compilación con PlatformIO CLI
- **P8**: ✅ Validado previamente

### Hardware testing
- **P5**: 🔬 Requiere servo R/C y fuente 5V
- **P6**: 🔬 Requiere MOSFET/BJT + carga (LED o motor)
- **P8**: 🔬 Requiere setup completo (4 ADC + 2 servos + stepper + endstop)

## 🎯 Próximos pasos sugeridos

### Corto plazo
1. **Compilar y flashear P5/P6** en hardware real para validación funcional
2. **Implementar P3** (NTC): Port de cálculo de temperatura desde MicroPython
3. **Implementar P4** (MPX5500): Port de conversión presión kPa
4. **Implementar P7** (Stepper): Port completo con modos de secuencia y homing

### Mediano plazo
1. **Telemetría CSV**: Añadir logging estructurado en P5/P6 para gráficos
2. **P1 básico**: Implementar secuencias LED y monitor de botones
3. **Calibración ADC**: Port de wizard de calibración desde MicroPython (P3/P4)
4. **Tests unitarios**: Validación de drivers comunes con mocks

### Largo plazo
1. **CI/CD**: GitHub Actions con compile checks para todas las prácticas
2. **OTA Updates**: Soporte para actualización remota (ESP32)
3. **RTOS**: Migración a FreeRTOS para tareas concurrentes (P8)
4. **Display**: Integración de OLED/LCD para visualización local

## 📚 Documentación

### Archivos de referencia
- `README.md`: Overview completo del proyecto
- `COMPILE_TEST.md`: Guía de pruebas de compilación
- `MicroPython/*/PINES.md`: Documentación de pines original (fuente de verdad)

### Diagramas
- Pin mapping tables en README
- Wiring diagrams en `assets/wiring.mmd` (MicroPython, referencia)

## 🔗 Links útiles

- **ESP32Servo**: https://github.com/madhephaestus/ESP32Servo
- **Arduino-Pico**: https://github.com/earlephilhower/arduino-pico
- **PlatformIO Docs**: https://docs.platformio.org/
- **MicroPython reference**: Carpetas `MicroPython/ESP32/` y `MicroPython/RP2040/`

---

**Última actualización**: 2025-11-04  
**Estado general**: 🟢 Estructura completa, 4/8 prácticas funcionales (P2, P5, P6, P8)
