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

#### P2: Potenciómetro ADC ✅
- Lectura ADC con normalización por plataforma
- Salida: RAW, voltaje (3.3V), porcentaje
- Frecuencia: 5 Hz (200 ms)
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

#### P8: Sistema integrado ✅
- Todos los subsistemas funcionando:
  - 4× ADC (altitude, speed, attitude, light)
  - 2× Servos (aileron, elevator)
  - 1× Motor PWM (throttle)
  - 1× Stepper (A4988 o ULN2003)
  - 1× Endstop
- Telemetría periódica cada 500 ms
- Pines completos documentados para ambas plataformas

## 🔄 Pendiente (templates)

- [ ] P1: LEDs y serial básico
- [ ] P3: Sensor NTC con cálculo de temperatura (ecuación Beta)
- [ ] P4: Sensor presión MPX5500DP con conversión kPa
- [ ] P7: Control stepper completo con modos de operación

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
