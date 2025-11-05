# Guía de pruebas de compilación

Este documento guía las pruebas básicas de compilación para validar las implementaciones de P5 y P6.

## Pre-requisitos

- PlatformIO Core CLI instalado
- VS Code con extensión PlatformIO IDE (opcional, recomendado)

## Validación rápida

### P5: Servo PWM

```bash
# ESP32
pio run -e esp32dev -t compiledb
# Cambiar PRACTICE=5 en platformio.ini primero, o descomentar env:esp32_p5

# RP2040
pio run -e pico -t compiledb
# Cambiar PRACTICE=5 en platformio.ini primero, o descomentar env:pico_p5
```

**Verificación exitosa:**
- Compila sin errores
- Librería `ESP32Servo` se descarga automáticamente para ESP32
- RP2040 usa PWM nativo (sin librerías externas)

### P6: Conmutación PWM

```bash
# ESP32
# Cambiar PRACTICE=6 en platformio.ini
pio run -e esp32dev

# RP2040
# Cambiar PRACTICE=6 en platformio.ini
pio run -e pico
```

**Verificación exitosa:**
- Compila sin errores
- `PropulsionSystem` instancia correctamente
- ADC opcional se configura si el pin está disponible

### P8: Sistema integrado

```bash
# ESP32
# Cambiar PRACTICE=8 en platformio.ini
pio run -e esp32dev

# RP2040
pio run -e pico
```

**Verificación exitosa:**
- Todos los drivers (sensors, controls, propulsion, landing gear) compilan
- Pin mapping para P8 se carga correctamente
- Imprime información de pines en setup

## Pruebas funcionales (con hardware)

### P5: Servo PWM

**Conexiones mínimas:**
- ESP32: Servo señal → GPIO18; GND común; VCC servo → 5V externa
- RP2040: Servo señal → GP18; GND común; VCC servo → VSYS (si <500 mA)

**Comportamiento esperado:**
- Al iniciar: servo se posiciona en 90°
- Modo 1 (default): barrido automático 0-180-0°
- Serial muestra ángulo cada 30°
- Enviar '2' por serial + conectar potenciómetro → control manual

### P6: Conmutación PWM

**Conexiones mínimas:**
- GPIO18/GP18 → R 220Ω → compuerta MOSFET (o base BJT)
- MOSFET drain → LED (con R 220Ω) → GND
- GND común obligatorio

**Comportamiento esperado:**
- Al iniciar: duty 0%
- Modo 1 (default): rampa automática 0-100-0%
- LED varía brillo suavemente
- Enviar '2' por serial + enviar "50" → duty fijo 50%
- Enviar '3' + conectar potenciómetro → control manual

## Errores comunes

### Error: `'Servo' was not declared`

**Causa:** ESP32Servo no instalada o no incluida.

**Solución:**
```ini
[env:esp32dev]
lib_deps = 
    madhephaestus/ESP32Servo@^3.0.5
```

### Error: `'analogWriteFreq' was not declared` (RP2040)

**Causa:** Estás usando un core RP2040 que no soporta esta función.

**Solución:** Actualiza `platform = raspberrypi` en platformio.ini. La función está disponible en Arduino-Pico 3.0+.

### Warning: `unused variable` en pin mapping

**No crítico:** Algunos pines pueden ser -1 si no se usan en la práctica actual. Es comportamiento esperado.

## Matriz de validación

| Práctica | ESP32 | RP2040 | Hardware mínimo | Estado |
|----------|-------|--------|-----------------|--------|
| P5 | ✅ | ✅ | Servo R/C | Implementada |
| P6 | ✅ | ✅ | LED + MOSFET | Implementada |
| P8 | ✅ | ✅ | ADC + servos + stepper | Integrada |

## Siguientes pasos

1. **Validar con hardware real:** Conecta los componentes y verifica el comportamiento esperado.
2. **Portar P2-P4:** Implementar lógica de ADC + cálculos de sensor (potenciómetro, NTC, MPX5500).
3. **Implementar P7:** Port completo de stepper (A4988/ULN2003) con homing y secuencias.
4. **Telemetría CSV:** Activar logging en P5/P6 para graficar con `tools/visualization/plot_telemetry.py`.

## Notas de integración continua

Si se configura CI/CD (GitHub Actions), añadir workflow:

```yaml
- name: Test compile P5
  run: |
    pio run -e esp32dev
    pio run -e pico
```

Ajustar `PRACTICE` en cada paso o crear entornos específicos en `platformio.ini`.
