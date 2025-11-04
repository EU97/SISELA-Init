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

## Mapa de pines unificado
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

## Notas
- Usa `Serial` a 115200 baudios.
- El LED integrado se configura por plataforma para la prueba del template.
- A medida que avances, reemplaza el contenido de cada `src/practices/pN.cpp`.
