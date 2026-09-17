
# SISELA-Init


Repositorio didáctico para prácticas de instrumentación y sistemas embebidos en aeronáutica, usando dos plataformas de hardware (ESP32 y RP2040) y dos enfoques de software (C++ unificado con PlatformIO y MicroPython). Todas las prácticas P1–P7 están completas en las 4 combinaciones (C++ ESP32, C++ RP2040, MicroPython ESP32, MicroPython RP2040). P8 está completa en MicroPython y es un template funcional en C++. Estructura y documentación actualizadas para facilitar comparación, portabilidad y validación cruzada.


## Objetivo del repositorio

- Reforzar fundamentos de adquisición de datos, acondicionamiento de señales, control y comunicación en sistemas embebidos aplicados a aeronáutica.
- Implementar las mismas prácticas (P1..P8) en C++ (PlatformIO unificado) y MicroPython, para ESP32 y RP2040.
- Documentar conexiones, pines, diagramas y resultados de forma clara y reproducible.
- Facilitar validación cruzada y comparación entre plataformas y lenguajes.


## Plataformas y enfoques

- **C++ (PlatformIO unificado):** Máximo control, drivers y portabilidad. Un solo código fuente para ESP32 y RP2040, selección de práctica y plataforma por macros y entornos. Drivers propios para servos, PWM, ADC, stepper, etc.
- **MicroPython:** Desarrollo rápido, iteración interactiva, ideal para prototipos y docencia. Estructura modular y checklist para prácticas.
- **ESP32:** Wi‑Fi/BLE, doble núcleo, ADC robusto, periféricos avanzados.
- **RP2040:** Microcontrolador económico, PIO para I/O determinista, excelente para educación y prototipos.

Comparar ambos enfoques permite elegir la herramienta adecuada según restricciones de tiempo, costo, rendimiento y mantenimiento.


## Estructura del repositorio

- `C++/SISELA-CPP/`: Proyecto unificado PlatformIO (C++), selecciona práctica y plataforma por entorno.
	- `src/practices/`: Implementaciones P1..P8 (selección por macro `-DPRACTICE=N`).
	- `include/pins/`: Tablas de pines unificadas por práctica y plataforma.
	- `src/common/`: Drivers para servos, PWM, ADC, stepper, etc.
	- Documentación: `README.md`, `QUICK_START.md`.
- `MicroPython/ESP32/` y `MicroPython/RP2040/`: Implementaciones por práctica, checklist y plantillas para documentación, pines y diagramas.
- Cada práctica tiene su propio `README.md`, `PINES.md`, diagramas y bitácora.


## Resumen de prácticas (P1..P8)


Las prácticas cubren desde GPIO y temporización hasta integración de sensores, actuadores y validación de sistemas. Cada práctica incluye objetivos, materiales, conexiones, modos de operación y criterios de validación. Todas las prácticas de RP2040/MicroPython (P1–P8) están implementadas y documentadas con detalles de conexiones, diagramas y bitácoras en sus respectivas carpetas.


- **P1:** GPIO, temporización, menú interactivo, LEDs y botones
- **P2:** ADC, sensor de posición analógico (potenciómetro), calibración
- **P3:** Termistor NTC (ecuación Beta) y sensor lineal LM35, medición de temperatura
- **P4:** Altímetro barométrico con sensor digital **BMP180** (I2C), compensación de 11 coeficientes y altitud ISA
- **P5:** Control de servomotores con PWM (50 Hz), barrido y control por potenciómetro
- **P6:** Conmutación de potencia con PWM y transistor (MOSFET/BJT)
- **P7:** Control de motores a pasos (A4988/ULN2003), homing y endstop
- **P8:** Integración completa: sensores ADC, servos, motor PWM y tren de aterrizaje

> **Análisis de señales (P4–P8):** cada práctica de P4 a P8 incorpora modos de
> análisis de señales (muestreo/aliasing, espectro/FFT, filtrado digital,
> caracterización de ADC y respuesta dinámica) que se apoyan en un generador de
> funciones + osciloscopio de banco y en la toolkit PC
> [`tools/sisela_signal/`](tools/sisela_signal/README.md). Ver el
> [reporte de verificación](docs/VERIFICACION_PRACTICAS.md).


## Índice de prácticas y estado


### Estado de implementación (febrero 2026)

> **Nota:** Todas las prácticas P1–P8 están implementadas en MicroPython (ESP32 y RP2040) y en C++ (PlatformIO unificado). C++ P8 es un template funcional pendiente de extensión.

| Práctica | C++ ESP32 | C++ RP2040 | MicroPython ESP32 | MicroPython RP2040 |
|----------|:---------:|:----------:|:----------------:|:-----------------:|
| P1       | ✅ Completa | ✅ Completa | ✅ Completa | ✅ Completa |
| P2       | ✅ Completa | ✅ Completa | ✅ Completa | ✅ Completa |
| P3       | ✅ Completa | ✅ Completa | ✅ Completa | ✅ Completa |
| P4       | ✅ Completa | ✅ Completa | ✅ Completa | ✅ Completa |
| P5       | ✅ Completa | ✅ Completa | ✅ Completa | ✅ Completa |
| P6       | ✅ Completa | ✅ Completa | ✅ Completa | ✅ Completa |
| P7       | ✅ Completa | ✅ Completa | ✅ Completa | ✅ Completa |
| P8       | ⚠️ Template | ⚠️ Template | ✅ Completa | ✅ Completa |

### Acceso rápido a prácticas

#### C++ (PlatformIO unificado)
- [SISELA-CPP/README.md](C++/SISELA-CPP/README.md) — guía de compilación, selección de práctica y plataforma
- [QUICK_START.md](C++/SISELA-CPP/QUICK_START.md) — inicio rápido
- Selección de práctica y plataforma vía `-DPRACTICE=N` y `env:esp32dev` / `env:pico` en `platformio.ini`

#### MicroPython
- ESP32: [P1](MicroPython/ESP32/P1/README.md) | [P2](MicroPython/ESP32/P2/README.md) | [P3](MicroPython/ESP32/P3/README.md) | [P4](MicroPython/ESP32/P4/README.md) | [P5](MicroPython/ESP32/P5/README.md) | [P6](MicroPython/ESP32/P6/README.md) | [P7](MicroPython/ESP32/P7/README.md) | [P8](MicroPython/ESP32/P8/README.md)
- RP2040: [P1](MicroPython/RP2040/P1/README.md) | [P2](MicroPython/RP2040/P2/README.md) | [P3](MicroPython/RP2040/P3/README.md) | [P4](MicroPython/RP2040/P4/README.md) | [P5](MicroPython/RP2040/P5/README.md) | [P6](MicroPython/RP2040/P6/README.md) | [P7](MicroPython/RP2040/P7/README.md) | [P8](MicroPython/RP2040/P8/README.md)

## Conexiones y mapeo de pines


Las conexiones y pines de cada práctica están documentados en los archivos `PINES.md` y diagramas `assets/wiring.mmd`/`wiring.svg` dentro de cada carpeta de práctica. El proyecto C++ unificado usa tablas de pines centralizadas (`include/pins/pins_esp32.h`, `pins_rp2040.h`) y macros para acceso rápido. Para RP2040/MicroPython, todos los detalles de pines y diagramas están completos y disponibles en los archivos `PINES.md` y `assets/wiring.mmd` de cada práctica.

### Ejemplo de mapeo (ESP32 DevKit v1)

| Práctica | ADC (altitude) | Servo | PWM Motor | Endstop | Stepper |
|----------|----------------|-------|-----------|---------|---------|
| P2/P3/P4 | 34             | —     | —         | —       | —       |
| P5       | 34 (opt)       | 18    | —         | —       | —       |
| P6       | 34 (opt)       | —     | 18        | —       | —       |
| P7       | —              | —     | —         | 4       | 18,19,5 |
| P8       | 34             | 25/26 | 18        | 4       | 19,21,5 |

### Ejemplo de mapeo (RP2040 Pico)

| Práctica | ADC (altitude) | Servo | PWM Motor | Endstop | Stepper |
|----------|----------------|-------|-----------|---------|---------|
| P2/P3/P4 | 26             | —     | —         | —       | —       |
| P5       | 26 (opt)       | 18    | —         | —       | —       |
| P6       | 26 (opt)       | —     | 18        | —       | —       |
| P7       | —              | —     | —         | 4       | 18,19,5 |
| P8       | 26             | 14/15 | 13        | 4       | 18,19,5 |

Consulta los archivos de cada práctica para detalles, advertencias de voltaje y diagramas.

## Guía rápida de uso

### C++ (PlatformIO)
1. Instala VS Code y la extensión PlatformIO IDE.
2. Abre `C++/SISELA-CPP/` como proyecto PlatformIO.
3. Edita `platformio.ini` para seleccionar la práctica (`-DPRACTICE=N`) y plataforma (`env:esp32dev` o `env:pico`).
4. Compila y sube al hardware.
5. Consulta `QUICK_START.md` para instrucciones detalladas, y [docs/VERIFICACION_PRACTICAS.md](docs/VERIFICACION_PRACTICAS.md) §6.2 para la matriz de compilación validada (las 8 prácticas × ESP32/RP2040).

### MicroPython
1. Abre la carpeta de la práctica deseada (`MicroPython/ESP32/Pn` o `MicroPython/RP2040/Pn`).
2. Sigue el checklist y plantilla de README para materiales, conexiones y pasos.
3. Usa Pymakr (VS Code) o Thonny para cargar y ejecutar el código.
4. Consulta los diagramas y archivos de pines para conexiones.

## Documentación y recursos

- [SISELA-CPP/README.md](C++/SISELA-CPP/README.md): detalles del proyecto C++ unificado
- [QUICK_START.md](C++/SISELA-CPP/QUICK_START.md): guía rápida de uso, compilación y validación
- [docs/VERIFICACION_PRACTICAS.md](docs/VERIFICACION_PRACTICAS.md): estado y bitácora de verificación (todas las prácticas, ambas arquitecturas)
- [CHECKLIST_PRACTICAS.md](MicroPython/ESP32/CHECKLIST_PRACTICAS.md): checklist para prácticas MicroPython
- Plantillas y ejemplos en `_template/` de cada plataforma
- Diagramas y documentación técnica en cada carpeta de práctica

## Créditos y licencia

Material académico para prácticas de instrumentación y sistemas embebidos. Uso libre con atribución. Consulta los archivos de cada práctica para créditos específicos de sensores, drivers y recursos externos.
