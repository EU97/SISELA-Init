
# SISELA-Init

Repositorio didáctico para prácticas de instrumentación y sistemas embebidos en aeronáutica, usando dos plataformas de hardware (ESP32 y RP2040) y dos enfoques de software (C++ unificado con PlatformIO y MicroPython). **Las 8 prácticas (P1–P8) están completas en las 4 combinaciones** (C++ ESP32, C++ RP2040, MicroPython ESP32, MicroPython RP2040) — incluido P8, que integra sensores, servos, motor de propulsión, tren de aterrizaje a pasos y un módulo opcional de dron con motores 2212. P4–P8 incorporan además paradigmas de análisis de señales (muestreo/aliasing, espectro, filtrado digital, caracterización) con una toolkit PC compartida para capturar, analizar y **visualizar en vivo** los datos, sea cual sea el lenguaje del firmware.

## Objetivo del repositorio

- Reforzar fundamentos de adquisición de datos, acondicionamiento de señales, control y comunicación en sistemas embebidos aplicados a aeronáutica.
- Implementar las mismas prácticas (P1..P8) en C++ (PlatformIO unificado) y MicroPython, para ESP32 y RP2040.
- Documentar conexiones, pines, diagramas y resultados de forma clara y reproducible.
- Facilitar validación cruzada y comparación entre plataformas y lenguajes.
- Ofrecer una alternativa de trabajo en casa (multímetro + simulación) para cuando no hay acceso a laboratorio con osciloscopio/generador de funciones.

## Plataformas y enfoques

- **C++ (PlatformIO unificado):** Máximo control, drivers y portabilidad. Un solo código fuente para ESP32 y RP2040, selección de práctica y plataforma por macros y entornos. Drivers propios para servos, PWM, ADC, stepper, ESC, etc.
- **MicroPython:** Desarrollo rápido, iteración interactiva, ideal para prototipos y docencia. Estructura modular y checklist para prácticas.
- **ESP32:** Wi‑Fi/BLE, doble núcleo, ADC robusto, periféricos avanzados.
- **RP2040:** Microcontrolador económico, PIO para I/O determinista, excelente para educación y prototipos.

Comparar ambos enfoques permite elegir la herramienta adecuada según restricciones de tiempo, costo, rendimiento y mantenimiento.

## Estructura del repositorio

- `C++/SISELA-CPP/`: Proyecto unificado PlatformIO (C++), selecciona práctica y plataforma por entorno.
	- `src/practices/`: Implementaciones P1..P8 (selección por macro `-DPRACTICE=N`).
	- `include/pins/`: Tablas de pines unificadas por práctica y plataforma.
	- `src/common/`: Drivers para servos, PWM, ADC, stepper, ESC, análisis de señales (`siglab.h`), etc.
	- Documentación: `README.md`, `QUICK_START.md`.
- `MicroPython/ESP32/` y `MicroPython/RP2040/`: Implementaciones por práctica, checklist y plantillas para documentación, pines y diagramas.
- `tools/sisela_signal/`: toolkit PC compartida (Python) para capturar, analizar y visualizar en vivo los datos que emite cualquier práctica — funciona igual sobre firmware MicroPython o C++ (ver más abajo).
- `docs/manuales/`: manuales de laboratorio en LaTeX (P4–P8), con teoría, procedimiento, alternativa de trabajo en casa y preguntas de discusión. Compilar con `cd docs/manuales && make`.
- `docs/VERIFICACION_PRACTICAS.md`: auditoría y bitácora de verificación completa (las 4 combinaciones, ambas arquitecturas, herramientas de datos).
- Cada práctica tiene su propio `README.md`, `PINES.md`, diagramas y bitácora.

## Resumen de prácticas (P1..P8)

Las prácticas cubren desde GPIO y temporización hasta integración de sensores, actuadores y validación de sistemas. Cada práctica incluye objetivos, materiales, conexiones, modos de operación y criterios de validación.

- **P1:** GPIO, temporización, menú interactivo, LEDs y botones
- **P2:** ADC, sensor de posición analógico (potenciómetro), codificación ARINC 429 BNR
- **P3:** Termistor NTC (ecuación Beta) y sensor lineal LM35, medición de temperatura
- **P4:** Altímetro barométrico con sensor digital **BMP180** (I2C), compensación de 11 coeficientes y altitud ISA
- **P5:** Control de servomotores con PWM (50 Hz), barrido, control por potenciómetro y vista en vivo
- **P6:** Conmutación de potencia con PWM y transistor (MOSFET/BJT), registro CSV de barrido
- **P7:** Control de motores a pasos (A4988/ULN2003), homing, endstop y registro CSV de jitter de paso
- **P8:** Integración completa: sensores ADC, servos, motor de propulsión, tren de aterrizaje a pasos, análisis de señales de la cadena completa, y **módulo opcional de dron** (4 motores brushless 2212 + ESC, mezclador de vuelo en configuración X) — ver [`docs/dron_2212.md`](MicroPython/ESP32/P8/docs/dron_2212.md)

> **Análisis de señales y herramientas de datos (P4–P8):** cada práctica de P4 a P8
> tiene al menos un modo que emite datos como CSV por el puerto serie
> (`t_us,col1[,col2,...]`, mismo formato en MicroPython y C++), procesable con la
> toolkit PC compartida [`tools/sisela_signal/`](tools/sisela_signal/README.md):
> captura a archivo, espectro/FFT, aliasing, filtrado digital, caracterización
> ENOB/SINAD/THD/respuesta al escalón, Bode, y **vista en vivo** (gráfica
> actualizándose en tiempo real, sin capturar primero). Ver la tabla de modos por
> práctica más abajo y el [reporte de verificación](docs/VERIFICACION_PRACTICAS.md) §9.

## Índice de prácticas y estado

### Estado de implementación (2026-09-17)

Las 8 prácticas están **completas y verificadas** en las 4 combinaciones — compiladas
de verdad con PlatformIO (no solo revisadas) y probadas por importación/instanciación
en MicroPython. Detalle completo, incluidos los bugs encontrados y corregidos durante
la verificación, en [`docs/VERIFICACION_PRACTICAS.md`](docs/VERIFICACION_PRACTICAS.md).

| Práctica | C++ ESP32 | C++ RP2040 | MicroPython ESP32 | MicroPython RP2040 |
|----------|:---------:|:----------:|:----------------:|:-----------------:|
| P1       | ✅ Completa | ✅ Completa | ✅ Completa | ✅ Completa |
| P2       | ✅ Completa | ✅ Completa | ✅ Completa | ✅ Completa |
| P3       | ✅ Completa | ✅ Completa | ✅ Completa | ✅ Completa |
| P4       | ✅ Completa | ✅ Completa | ✅ Completa | ✅ Completa |
| P5       | ✅ Completa | ✅ Completa | ✅ Completa | ✅ Completa |
| P6       | ✅ Completa | ✅ Completa | ✅ Completa | ✅ Completa |
| P7       | ✅ Completa | ✅ Completa | ✅ Completa | ✅ Completa |
| P8       | ✅ Completa (9 modos + módulo dron opcional) | ✅ Completa | ✅ Completa | ✅ Completa |

### Acceso rápido a prácticas

#### C++ (PlatformIO unificado)
- [SISELA-CPP/README.md](C++/SISELA-CPP/README.md) — guía de compilación, selección de práctica y plataforma
- [QUICK_START.md](C++/SISELA-CPP/QUICK_START.md) — inicio rápido
- Selección de práctica y plataforma vía `-DPRACTICE=N` y `env:esp32dev` / `env:pico` en `platformio.ini`

#### MicroPython
- ESP32: [P1](MicroPython/ESP32/P1/README.md) | [P2](MicroPython/ESP32/P2/README.md) | [P3](MicroPython/ESP32/P3/README.md) | [P4](MicroPython/ESP32/P4/README.md) | [P5](MicroPython/ESP32/P5/README.md) | [P6](MicroPython/ESP32/P6/README.md) | [P7](MicroPython/ESP32/P7/README.md) | [P8](MicroPython/ESP32/P8/README.md)
- RP2040: [P1](MicroPython/RP2040/P1/README.md) | [P2](MicroPython/RP2040/P2/README.md) | [P3](MicroPython/RP2040/P3/README.md) | [P4](MicroPython/RP2040/P4/README.md) | [P5](MicroPython/RP2040/P5/README.md) | [P6](MicroPython/RP2040/P6/README.md) | [P7](MicroPython/RP2040/P7/README.md) | [P8](MicroPython/RP2040/P8/README.md)

#### Manuales de laboratorio (LaTeX → PDF)
- [`docs/manuales/`](docs/manuales/) — P4, P5, P6, P7, P8. Cada uno incluye teoría,
  procedimiento experimental, **alternativa de trabajo en casa** (multímetro +
  simulación, para cuando no hay banco de laboratorio) y preguntas de discusión.
  Compilar con `cd docs/manuales && make`.

## Herramientas de recolección y visualización de datos

Cada práctica de P4 a P8 tiene al menos un modo que **emite CSV por el puerto serie**
en el formato `t_us,col1[,col2,...]` — idéntico entre la implementación MicroPython y
la C++ de la misma práctica, así que la misma herramienta y el mismo comando sirven
sin importar qué firmware tenga cargado la placa.

| Práctica | Modo(s) que emiten datos | Tipo de captura |
|---|---|---|
| P4 | 6 (ruido/muestreo), 7 (filtro en vivo) | Bloque a Fs fija |
| P5 | 6 (aliasing), 7 (escalón) — bloque · **8 (vista en vivo)** — continuo | Bloque / continuo |
| P6 | **5 (registro CSV: barrido + ADC)** | Continuo (vivo) |
| P7 | **6 (registro CSV: jitter de paso)** | Continuo (vivo) |
| P8 | 9→2 (muestreo multicanal) | Continuo (vivo) |

```bash
# Capturar a archivo y analizar después
python -m sisela_signal capture --port COM5 --menu 6 --out cap.csv
python -m sisela_signal spectrum --file cap.csv --col v --metrics --full-scale 3.3
python -m sisela_signal characterize --file cap.csv --col v --mode adc

# Vista en vivo — gráfica actualizándose en tiempo real, sin capturar primero
python -m sisela_signal live --port COM5 --menu 5 --cols duty_pct,adc_raw   # P6
python -m sisela_signal live --port COM5 --menu 6 --cols dt_us              # P7
python -m sisela_signal live --port COM5 --menu 8 --cols angle_deg,adc_raw  # P5
```

Instalación: `pip install -r tools/sisela_signal/requirements.txt` (numpy, scipy,
matplotlib, pyserial). Detalle completo de comandos, formato CSV y configuración del
banco (generador/osciloscopio) en
[`tools/sisela_signal/README.md`](tools/sisela_signal/README.md).

## Conexiones y mapeo de pines

Las conexiones y pines de cada práctica están documentados en los archivos `PINES.md` y diagramas `assets/wiring.mmd`/`wiring.svg` dentro de cada carpeta de práctica. El proyecto C++ unificado usa tablas de pines centralizadas (`include/pins/pins_esp32.h`, `pins_rp2040.h`) y macros para acceso rápido.

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

### Sin laboratorio (multímetro + simulación)
Si no tienes acceso a un banco con osciloscopio/generador de funciones, cada manual de
P4–P8 (`docs/manuales/`) incluye una sección **"Alternativa de Trabajo en Casa"**: qué
se puede verificar con un multímetro común, qué se puede simular (NI Multisim, Proteus,
Wokwi — incluidas fallas que nunca deben probarse en hardware real), y qué mediciones
requieren honestamente laboratorio presencial (p. ej. jitter de PWM en nanosegundos o
aliasing con un generador real).

## Documentación y recursos

- [SISELA-CPP/README.md](C++/SISELA-CPP/README.md): detalles del proyecto C++ unificado
- [QUICK_START.md](C++/SISELA-CPP/QUICK_START.md): guía rápida de uso, compilación y validación
- [docs/VERIFICACION_PRACTICAS.md](docs/VERIFICACION_PRACTICAS.md): estado y bitácora de verificación (todas las prácticas, ambas arquitecturas, herramientas de datos)
- [docs/manuales/](docs/manuales/): manuales de laboratorio en LaTeX (P4–P8)
- [tools/sisela_signal/README.md](tools/sisela_signal/README.md): toolkit PC de captura, análisis y vista en vivo
- [docs/materiales/SISELA_Materiales.xlsx](docs/materiales/SISELA_Materiales.xlsx): lista de materiales por práctica, clasificación y reutilización entre prácticas
- [CHECKLIST_PRACTICAS.md](MicroPython/ESP32/CHECKLIST_PRACTICAS.md): checklist para prácticas MicroPython
- Plantillas y ejemplos en `_template/` de cada plataforma
- Diagramas y documentación técnica en cada carpeta de práctica

## Créditos y licencia

Material académico para prácticas de instrumentación y sistemas embebidos. Uso libre con atribución. Consulta los archivos de cada práctica para créditos específicos de sensores, drivers y recursos externos.
