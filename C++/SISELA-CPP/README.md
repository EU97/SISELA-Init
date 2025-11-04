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

## Notas
- Usa `Serial` a 115200 baudios.
- El LED integrado se configura por plataforma para la prueba del template.
- A medida que avances, reemplaza el contenido de cada `src/practices/pN.cpp`.
