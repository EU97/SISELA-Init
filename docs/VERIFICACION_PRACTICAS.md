# Reporte de verificación — Prácticas P1–P8 (SISELA-Init)

**Fecha:** 2026-09-10
**Alcance:** auditoría de consistencia entre los **manuales** (`~/Descargas/manuales/Manuales/pN.pdf`,
generados con LaTeX/MiKTeX, sin fuentes `.tex` en el repo) y las **cuatro implementaciones**:
MicroPython/ESP32, MicroPython/RP2040, C++/PlatformIO (ESP32) y C++/PlatformIO (RP2040).
**Metodología:** lectura de los 8 PDF, de `main.py`/`pN.cpp` de cada práctica, de los drivers
(`lib/*.py`, `src/common/*.h`), de `README.md`, `REPORTE_FUNCIONES.md` y de los `PINES.md`/`docs/`.

> **Regla de trabajo del proyecto:** P1–P3 se consideran **cerradas** (no se modifica su código;
> solo se documentan inconsistencias y se pueden añadir *tools* opcionales). P4–P8 se actualizan
> para incorporar los paradigmas de análisis de señales.

---

## 1. Estado global

| Práctica | Tema | MP ESP32 | MP RP2040 | C++ ESP32 | C++ RP2040 | Manual coincide |
|---|---|:--:|:--:|:--:|:--:|:--:|
| P1 | GPIO, temporización, menú | ✅ | ✅ | ✅ | ✅ | ✅ |
| P2 | ADC + media móvil + ARINC 429 BNR | ✅ | ✅ | ✅ | ✅ | ⚠️ (ADC RP2040 10 vs 16 bit) |
| P3 | NTC + LM35 + ecuación Beta | ✅ | ✅ | ✅ | ✅ | ⚠️ (README dice solo NTC) |
| P4 | **BMP180** altímetro I2C | ✅ (5 modos) | ✅ (5 modos) | ⚠️ (3 modos, sin CSV) | ⚠️ (3 modos) | ❌ README/REPORTE dicen MPX5500DP |
| P5 | Servo PWM 50 Hz | ✅ (4 modos) | ✅ (4 modos) | ⚠️ (2 modos) | ⚠️ (2 modos) | ⚠️ (manual reconoce 2 modos en C++) |
| P6 | Conmutación PWM (BJT/MOSFET) | ✅ (4 modos) | ✅ (4 modos) | ✅ | ✅ | ⚠️ (sin *guard* PC; `actuator_pwm` solo ESP32) |
| P7 | Motor a pasos A4988/ULN2003 | ✅ (5 modos) | ✅ (5 modos) | ✅ | ✅ | ⚠️ (sin rampa de aceleración ni ARINC L204) |
| P8 | Integración ARINC 429 + dron opcional (2212) | ✅ (9 modos) | ✅ (9 modos) | ✅ (9 modos) | ✅ (9 modos) | ⚠️ (manual describe 4 variantes; no implementadas — ver D-18) |

Leyenda: ✅ completo y consistente · ⚠️ funcional con divergencias · ❌ contradicción documental.

---

## 2. Verificación por práctica

### P1 — Fundamentos de MCU / GPIO
- **Manual:** GPIO, temporización, menú interactivo, pull-ups, panel de tren de aterrizaje
  (tabla de verdad), marco normativo DO-178C/254/160.
- **Repo:** `MicroPython/{ESP32,RP2040}/P1/main.py` y `C++/.../p1.cpp` implementan blink, chaser,
  monitor de entradas y modo integrado. Coherente con el manual.
- **Discrepancias:** ninguna relevante. `REPORTE_FUNCIONES.md` documenta solo la variante RP2040.
- **Acción:** *(Fase 3, opcional)* `tools/analyze_p1.py` para verificar con el osciloscopio el
  periodo/duty/jitter de la señal *heartbeat* (Gráfica 1 del manual).

### P2 — Adquisición analógica + ARINC 429 BNR
- **Manual:** ADC, función de transferencia, **filtro de media móvil**, indicador de flaps,
  codificación ARINC 429 Label 270 (BNR, paridad impar), simulador de falla de sensor,
  **muestreo ADC a 100 Hz**, gráfica «Señal ADC en tiempo real (ruido de LSB)».
- **Repo:** `p2.cpp` integra los 4 casos (media móvil N=8, flaps, ARINC BNR, SSM=Failure) a 100 Hz.
  MicroPython equivalente. Coherente en concepto.
- **Discrepancias:**
  - **D-1** *(baja)* `p2.cpp` trata el ADC del RP2040 como **10 bit** (`analogRead` → 0–1023,
    `ADC_MAX_VAL = 1023`) mientras MicroPython usa **16 bit** (`read_u16` → 0–65535). Varios textos
    del manual afirman «RP2040 ADC 16 bit». Falta `analogReadResolution(12)` en el `setup()`.
- **Acción:** no se modifica P2. Se documenta D-1 aquí y se corrige la política en P4–P8
  (llamar `analogReadResolution(12)` en C++). *(Fase 3, opcional)* `tools/analyze_p2.py` sobre la
  toolkit: histograma de ruido de LSB, PSD, respuesta en frecuencia de la media móvil, verificación
  de Fs=100 Hz y demo de aliasing con el generador — **sin tocar `main.py`**.

### P3 — Termistor NTC (+ LM35)
- **Manual:** NTC, modelo Beta, Steinhart–Hart (referencia), divisor de tensión, **sensor
  alternativo LM35**, gestión de salud del sensor (SSM en ARINC 429 Label 212), autocalentamiento.
- **Repo:** `p3.cpp` y MicroPython implementan NTC (Beta) **y LM35** (commit `702ff7b`), modos
  raw/resistencia/temperatura/CSV/calibración.
- **Discrepancias:**
  - **D-2** *(baja)* `README.md` (línea ~48) describe P3 como **«NTC, ecuación Beta»** sin
    mencionar el soporte LM35 que sí existe en el código y en el manual.
- **Acción:** no se modifica P3. Se corrige `README.md` en Fase 3. *(Fase 3, opcional)*
  `tools/analyze_p3.py`: PSD de ruido térmico, respuesta escalón por autocalentamiento, filtro
  para la NTC.

### P4 — Altímetro barométrico BMP180 ⚠️ **contradicción documental**
- **Manual (`p4.pdf`, 20 pág.):** sensor **BMP180** (I2C 0x77), 11 coeficientes, compensación
  entera de 32 bits, altitud ISA, altimetría QNH/QFE/QNE, ARINC 429 Label 203, herramienta
  `altimeter_gui.py`, 5 casos (crudos, T+P, altímetro+QNH, **CSV**, comparativa de alturas).
- **Repo:**
  - `MicroPython/{ESP32,RP2040}/P4/main.py` + `lib/bmp180.py`: **correcto y completo** — 5 modos,
    compensación entera idéntica al datasheet, `altimeter_gui.py` presente y consistente.
    Pines I2C: ESP32 GPIO21/22, RP2040 **GP0/GP1** (el manual §6.2 lista MP RP2040 GP0/GP1). ✅
  - `C++/.../p4.cpp`: implementa BMP180 con Wire (I2C ESP32 21/22, RP2040 **GP4/GP5** — el manual
    §6.2 lista C++ Pico en 4/5). Solo **3 modos** (crudos, T+P, altímetro); **falta el modo CSV**
    (Caso 4) del que depende `altimeter_gui.py`.
- **Discrepancias:**
  - **D-3** *(alta, documental)* `README.md` línea ~48: *«P4: Sensor presión MPX5500DP, conversión
    ADC a kPa»* — **obsoleto**. P4 pasó a BMP180 (commits `e4f6e33`, `c7b7709`).
  - **D-4** *(alta, documental)* `REPORTE_FUNCIONES.md` §«Práctica 4» (líneas ~212–289) describe
    íntegramente el **MPX5500DP** (funciones `voltage_to_pressure_kpa`, `read_adc_avg`, modos de
    presión…) que ya no existen. Además el documento solo cubre RP2040/MicroPython.
  - **D-5** *(media)* `MicroPython/{ESP32,RP2040}/P4/docs/MPX5500DP.md` sigue presente (residuo de
    la P4 anterior). El `main.py` ya no lo usa.
  - **D-6** *(baja)* `MicroPython/ESP32/P4/tools/README.md` menciona `live_plot.py` («graficador
    legacy») que **no existe** en `P4/tools/` (sí en P2 y P5).
  - **D-7** *(media)* `C++/.../p4.cpp` no tiene modo CSV → `altimeter_gui.py` y la toolkit de
    análisis no pueden usar la build C++.
  - **D-8** *(baja)* `MicroPython/ESP32/P4/RESUMEN_P4.md` existe sin equivalente en otras prácticas.
- **Acción (Fase 1):** corregir D-3, D-4, D-6; retirar `MPX5500DP.md` (D-5); añadir modo CSV +
  modos de análisis de señales a `p4.cpp` (D-7); integrar `siglab` y `docs/analisis_senales.md`;
  recrear `docs/manuales/p4.tex`.

### P5 — Control PWM de servomotores
- **Manual (`p5.pdf`, 18 pág.):** PWM 50 Hz, mapeo ángulo↔pulso↔`duty_u16`, clase `Servo`,
  alimentación dual, 4 modos (barrido, ángulo manual, pulso µs, potenciómetro), medición con
  osciloscopio (periodo, duty, ancho de pulso, jitter), `servo_cli.py`, contexto FBW/EMA/ARINC 429
  Label 101.
- **Repo:**
  - `MicroPython/{ESP32,RP2040}/P5/main.py` + `lib/servo.py`: **4 modos**, coherente con el manual.
    Pines: ESP32 GPIO18 (PWM) / GPIO34 (ADC); RP2040 GP18 / GP26. `tools/servo_cli.py` y
    `tools/live_plot.py` presentes (solo en ESP32/P5; RP2040/P5 no tiene `tools/`).
  - `C++/.../p5.cpp`: **2 modos** (barrido + ADC). El manual §7.7 lo reconoce explícitamente
    («`p5.cpp` implementa dos modos»). ADC RP2040 tratado como 10 bit (`map(raw,0,1023,...)`).
- **Discrepancias:**
  - **D-9** *(baja)* `RP2040/P5` carece de carpeta `tools/` (sin `servo_cli.py` ni `live_plot.py`);
    el `PINES.md` de RP2040/P5 remite a herramientas que no están en esa ruta.
  - **D-10** *(baja)* misma cuestión de resolución ADC RP2040 que D-1 en `p5.cpp`.
  - **D-20** *(media)* **contaminación de la carpeta P5 (ESP32) con material de un sensor
    barométrico**: `MicroPython/ESP32/P5/docs/BMP280.md` (ficha de un BMP280 que dice
    «…en la Práctica 5») y `MicroPython/ESP32/P5/tools/live_plot.py` («Live plot para
    Práctica 5 (BMP280)») — restos de copiar la plantilla de otra práctica. P5 es control
    de servos, no usa ningún sensor de presión. El propio `tools/README.md` ya admite que
    `live_plot.py` «permanece del ejercicio anterior».
- **Acción (Fase 1):** añadir modos de análisis de señales (jitter PWM, aliasing/ADC, respuesta
  escalón, Bode) a las 4 implementaciones; `siglab`; `RP2040/P5/tools/` con presets; recrear
  `docs/manuales/p5.tex`; `analogReadResolution(12)` en `p5.cpp`.

### P6 — Conmutación de potencia con PWM (transistor)
- **Manual (`p6.pdf`, 24 pág.):** BJT como interruptor, ODF, `R_B`, low-side/high-side,
  diodo *flyback*, disipación térmica, ARINC 429 discreto (Label 270), 4 modos de firmware
  (on/off, PWM manual, barrido, potenciómetro), verificación con osciloscopio (`V_CE(sat)`,
  transitorio de apagado, frecuencia PWM), guía de frecuencias por carga.
- **Repo:** `MicroPython/{ESP32,RP2040}/P6/main.py` implementan los 4 modos (PWM 1 kHz, ADC).
  `p6.cpp` con `PropulsionSystem`. Coherente en concepto.
- **Discrepancias:**
  - **D-11** *(media)* `MicroPython/{ESP32,RP2040}/P6/main.py` importan `from machine import ...`
    **sin `try/except`** y no tienen modo PC/polyfill (P4 y P5 sí) → no importan fuera de la placa,
    dificultan `py_compile` / análisis estático / la comprobación en CI.
  - **D-12** *(baja)* el manual (paso «Sincronizar los archivos … `lib/actuator_pwm.py`») da por
    hecho ese módulo; existe para **ESP32** (`MicroPython/ESP32/P6/lib/actuator_pwm.py`) pero **no
    para RP2040** (cuyo `main.py` construye el PWM *inline*).
  - **D-13** *(baja)* `MicroPython/ESP32/P6/docs/` contiene `SSD1306.md` (no usado por el `main.py`).
- **Acción (Fase 2):** añadir *guards* PC a P6 (D-11); crear `RP2040/P6/lib/actuator_pwm.py` o
  alinear el manual (D-12); modos de análisis (espectro/EMI, transitorio, PWM→DAC RC); recrear
  `docs/manuales/p6.tex`.

### P7 — Control de motores a pasos
- **Manual (`p7.pdf`, 26 pág.):** motor unipolar/bipolar, modos de excitación, resolución angular,
  RPM↔intervalo, ULN2003, STEP/DIR A4988, **ARINC 429 Label 204** (posicionamiento), 4 casos de
  estudio incluyendo **Caso 4: rampas de aceleración (perfil trapezoidal)**, verificación con
  osciloscopio y multímetro. Cuadro 9 de pines: ESP32 GPIO26/25/33/32, RP2040 GP26/27/28/22.
- **Repo:** `MicroPython/{ESP32,RP2040}/P7/main.py` + `lib/stepper_{a4988,uln2003}.py`: 5 modos
  (jog, N pasos, barrido, homing, info). Pines: ESP32 `[26,25,33,32]` ✅ (coincide con Cuadro 9),
  RP2040 `[26,27,28,22]` ✅. `p7.cpp` equivalente.
- **Discrepancias:**
  - **D-14** *(media)* el firmware **no implementa el perfil trapezoidal de aceleración** (Caso 4
    del manual): `mode_sweep`/`mode_homing`/`mode_move_n_steps` usan intervalo constante.
  - **D-15** *(media)* el firmware **no implementa la decodificación ARINC 429 Label 204** del
    manual (P7); solo P2 y P8 decodifican ARINC.
  - **D-16** *(baja, bug)* `mode_info` (ESP32 línea ~236 y RP2040 ~241) evalúa `_setup_endstop()`
    dentro de un *f-string* para decidir el texto «(configurado)/(no disponible)»: siempre devuelve
    un objeto `Pin` (verdadero) → siempre imprime «configurado» y crea un `Pin` como efecto
    colateral.
  - **D-17** *(baja)* `RP2040/P7` ULN2003 usa GP26–28 (pines ADC): al añadir modos que muestreen
    el ADC hay que remapear o advertir del conflicto (el manual ya lo nota).
- **Acción (Fase 2):** Modo 7 de análisis = **implementa el perfil de rampa trapezoidal** (cubre
  D-14 y da material de análisis de *jerk*/FFT); Modo 6 = jitter de intervalo STEP; Modo 8 =
  forma de onda de corriente de fase (THD micro-step vs full-step). Corregir D-16. Recrear
  `docs/manuales/p7.tex`. D-15 se cita como pregunta de discusión (no se implementa ARINC en P7).

### P8 — Integración de sistemas (ARINC 429) + módulo opcional de dron ✅ Fase 2
- **Manual (`p8.pdf`, 18 pág.):** proyecto final, protocolo ARINC 429, palabra de 32 bits, BNR,
  SSM, **4 variantes** (indicador de velocidad, alerta de temperatura, indicador de altitud,
  control de superficie FBW), arquitectura de 2 MCU vs 1 MCU, inyección de fallos, análisis de
  latencia.
- **Repo (antes de Fase 2):** `MicroPython/{ESP32,RP2040}/P8/main.py` + `lib/{sensors,
  flight_controls,propulsion,landing_gear}.py`: panel de instrumentos, control manual, potencia,
  tren, piloto automático, diagnóstico, configuración. `p8.cpp` marcado como **Template** en
  `README.md`.
- **Discrepancias (previas a Fase 2):**
  - **D-18** *(media)* `README.md` marca C++ P8 como *«⚠️ Template»* mientras el manual describe un
    proyecto completo de 4 variantes; la implementación MicroPython no está estructurada por las
    4 variantes del manual sino por modos de panel.
  - **D-19** *(baja)* enlaces truncados en la sección «Acceso rápido» de `README.md`
    (`| [P2](...) | ...`).
  - **D-24** *(alta, bug)* `C++/.../common/propulsion.h::setThrottle(float pct)` esperaba una
    **fracción 0–1**, pero su único llamador (`p6.cpp`) ya le pasaba **0–100** (porcentaje) — todo
    `duty ≥ 1` se recortaba a `pct=1.0` → el PWM de P6 en C++ quedaba siempre al 100 % (control
    de potencia no proporcional, aunque el manual y el firmware MicroPython sí lo son).
  - **D-25** *(baja, documental)* `MicroPython/{ESP32,RP2040}/P8/README.md` describía un menú con
    un modo 6 «Registro de telemetría a CSV» que **nunca existió** en `main.py` (el modo 6 real
    siempre fue «Diagnóstico»).
- **Acción (Fase 2 — alcance acotado por el usuario a solo P8):**
  - Módulo opcional **dron con motores 2212**: `lib/esc.py` + `lib/quad_mixer.py`
    (MicroPython) y `common/esc.h` + `common/quad_mixer.h` (C++) — driver de ESC con máquina de
    armado fail-safe y mezclador de cuadricóptero en X (lazo abierto, sin IMU/PID). Nuevo modo 8
    del menú (armar / test individual / mezclador / jitter PWM / parada de emergencia),
    deshabilitado por defecto (`ENABLE_DRONE = False`). Documentado en
    `docs/dron_2212.md` (specs del motor 2212, presupuesto de potencia, cableado, seguridad,
    y la ruta de extensión a vuelo estabilizado con IMU+PID, fuera de alcance de esta práctica).
  - Modos de análisis de señales del plan original (nuevo modo 9): «latencia de la cadena
    sensor→actuador» y «muestreo multicanal + anti-alias», usando `lib/siglab.py` /
    `common/siglab.h`. Documentado en `docs/analisis_senales.md`.
  - **D-18 resuelto**: `p8.cpp` dejó de ser un *template*; ahora replica los 9 modos de la versión
    MicroPython (incluido el módulo de dron) usando `Serial` en modo bloqueante análogo a
    `input()`. Sigue sin implementar las «4 variantes» ARINC 429 del manual — ese enfoque
    (panel de instrumentos único vs 4 variantes independientes) es una decisión de diseño
    documentada, no un defecto.
  - **D-24 resuelto**: `propulsion.h` reescrito con API en porcentaje (0–100) consistente
    (`setThrottle`, `getThrottle`, `emergencyStop`, `rampTo`); corrige `p6.cpp` como efecto
    colateral (se resincronizó sin tocar `p6.cpp`) y es la base del modo 3/9 de `p8.cpp`.
  - **D-25 resuelto**: `README.md` de P8 (ambas plataformas) corregido para reflejar los modos
    reales 1–9.
  - **P6 y P7 quedan sin cambios de firmware/manual en esta fase** (el usuario acotó
    explícitamente la Fase 2 a P8). `docs/manuales/p6.tex`/`p7.tex` y las acciones D-11, D-12,
    D-14, D-16, D-17 quedan pendientes para una fase futura si se solicita.

---

## 3. Lista consolidada de discrepancias

Estado: ✅ corregido · ⏳ pendiente (fase indicada) · 📝 solo se documenta

| ID | Sev. | Archivo(s) | Descripción | Fase | Estado |
|---|:--:|---|---|:--:|:--:|
| D-3 | 🔴 | `README.md` | P4 descrito como MPX5500DP (es BMP180) | 1 | ✅ |
| D-4 | 🔴 | `REPORTE_FUNCIONES.md` | §P4 describe el sensor MPX5500DP obsoleto | 1 | ✅ |
| D-7 | 🟠 | `C++/.../src/practices/p4.cpp` | Falta el modo CSV (Caso 4) → `altimeter_gui.py` no funciona en C++ | 1 | ✅ |
| D-11 | 🟠 | `MicroPython/{ESP32,RP2040}/P6/main.py` | Sin *guard* `try/except`; no importa en PC | 2 | ⏳ (2, no solicitada) |
| D-14 | 🟠 | `MicroPython/{ESP32,RP2040}/P7/main.py` | Sin perfil trapezoidal de aceleración (Caso 4 manual) | 2 | ⏳ (2, no solicitada) |
| D-15 | 🟠 | P7 firmware | Sin decodificación ARINC 429 Label 204 | — | 📝 |
| D-18 | 🟠 | `README.md`, `p8.cpp` | C++ P8 «Template»; MP P8 no sigue las 4 variantes del manual | 2 | ✅ `p8.cpp` ya no es template (9 modos); las 4 variantes ARINC quedan como decisión de diseño documentada |
| D-24 | 🔴 | `C++/.../common/propulsion.h`, `p6.cpp` | `setThrottle()` esperaba fracción 0–1 pero recibía 0–100 → PWM de P6 en C++ saturaba siempre a 100 % | 2 | ✅ (hallado y corregido al tocar `propulsion.h` para P8) |
| D-25 | 🟡 | `MicroPython/{ESP32,RP2040}/P8/README.md` | Menú documentado con un modo 6 «Registro CSV» que nunca existió en `main.py` | 2 | ✅ |
| D-1 | 🟡 | `C++/.../p2.cpp` | ADC RP2040 a 10 bit (MP usa 16 bit); falta `analogReadResolution(12)` | 3 | 📝 |
| D-2 | 🟡 | `README.md` | P3 sin mencionar el soporte LM35 | 1 | ✅ |
| D-5 | 🟡 | `MicroPython/{ESP32,RP2040}/P4/docs/MPX5500DP.md` | Ficha del sensor obsoleto aún presente | 1 | ✅ (eliminada) |
| D-6 | 🟡 | `MicroPython/ESP32/P4/tools/README.md` | Referencia a `live_plot.py` inexistente | 1 | ✅ |
| D-8 | 🟡 | `MicroPython/ESP32/P4/RESUMEN_P4.md` | Doc sin equivalente en otras prácticas | 1 | 📝 (se conserva; su contenido es correcto) |
| D-9 | 🟡 | `MicroPython/RP2040/P5/` | Sin carpeta `tools/` | 1 | ✅ |
| D-10 | 🟡 | `C++/.../p5.cpp` | ADC RP2040 a 10 bit; falta `analogReadResolution(12)` | 1 | ✅ |
| D-12 | 🟡 | `MicroPython/RP2040/P6/` | Sin `lib/actuator_pwm.py` (sí en ESP32) | 2 | ⏳ (2, no solicitada) |
| D-13 | 🟡 | `MicroPython/ESP32/P6/docs/SSD1306.md` | Doc no referenciado por el `main.py` | 2 | ⏳ (2, no solicitada) |
| D-16 | 🟡 | `MicroPython/{ESP32,RP2040}/P7/main.py` | `mode_info`: `_setup_endstop()` en *f-string* | 2 | ⏳ (2, no solicitada) |
| D-17 | 🟡 | `MicroPython/RP2040/P7/main.py` | ULN2003 en GP26–28 (pines ADC) | 2 | 📝 |
| D-19 | 🟡 | `README.md` | Enlaces truncados en «Acceso rápido» | 3 | ⏳ 3 |
| D-20 | 🟠 | `MicroPython/ESP32/P5/{docs/BMP280.md,tools/live_plot.py}` | Restos de plantilla de otra práctica (sensor barométrico en una práctica de servos) | 1 | ✅ `BMP280.md` eliminada; `live_plot.py` se conserva (documentado como *legacy*) |
| D-21 | 🟡 | `MicroPython/RP2040/P5/{README.md,docs/oscilograma.md}` | Enlaces a `../../GUIA_MIGRACION.md` (no existe en el repo) | 1 | ✅ (oscilograma corregido; README pendiente Fase 3) |
| D-22 | 🔴 | `MicroPython/{ESP32,RP2040}/P4/docs/oscilograma.md` | Todo el documento describía el MPX5500DP (CSV `pressure_kPa`, `adc_raw`) — sensor obsoleto | 1 | ✅ reescrito para BMP180 + modos 6–7 |
| D-23 | 🟠 | `MicroPython/ESP32/P2/tools/live_plot.py` | **Archivo Python roto de origen**: líneas 2–3 son `"""` seguido de `"""Live plotter...` → `SyntaxError` (docstring vacío + apertura de cadena sin cerrar). El script nunca se ha podido ejecutar. `main.py` de P2 no se ve afectado. | 3 (P2 congelada; pendiente de autorización) | ⏳ |

**Nota de alcance (Fase 2):** el usuario acotó explícitamente esta fase a **solo P8**
(«genera la fase 2, solo vamos a cambiar la práctica 8»). Las acciones de P6/P7 previstas en el
plan original (D-11, D-12, D-14, D-16) siguen abiertas y se marcan «no solicitada» — no se tocó
ningún archivo de P6/P7 salvo el efecto colateral de la corrección de `propulsion.h` (D-24), que
es un header compartido y no cambia el comportamiento correcto de P6 (lo corrige).

🔴 contradicción documental · 🟠 divergencia funcional · 🟡 menor / cosmético

## 4-bis. Cambios aplicados en la Fase 1

| Área | Detalle |
|---|---|
| Toolkit PC | Nuevo paquete `tools/sisela_signal/` (spectrum, sampling, filters, characterize, bode, capture, scopeio, report, CLI). 37 pruebas `pytest` en verde; *fixtures* sintéticas en `examples/`. |
| Firmware embebido | `lib/siglab.py` (MicroPython) en P4×2 y P5×2; `src/common/siglab.h` (C++, header-only). Adquisición a Fs fija (`BlockSampler`, `stream_csv`), `Stats`, filtros mínimos, `goertzel`. |
| P4 (MicroPython ESP32+RP2040) | Modos **6** (ruido/muestreo) y **7** (filtro en vivo). Compilan e importan en CPython. |
| P4 (C++) | Añadido el **modo 4 (CSV)** que faltaba (D-7) + modos 6/7. Sintaxis verificada (`g++ -fsyntax-only`) para ESP32 y RP2040. |
| P5 (MicroPython ESP32+RP2040) | Modos **5** (jitter PWM), **6** (muestreo/aliasing con generador), **7** (respuesta al escalón). |
| P5 (C++) | Modos 5/6/7 + `analogReadResolution(12)` (D-10). Sintaxis verificada. |
| P5 (RP2040) | Creada la carpeta `tools/` que faltaba (D-9): `servo_cli.py`, `requirements.txt`, `README.md`. |
| Docs por práctica | Nuevo `docs/analisis_senales.md` (P4×2, P5×2); `README.md`, `PINES.md` y `docs/oscilograma.md` de P4–P5 actualizados. |
| Docs globales | `README.md` (P3/P4), `REPORTE_FUNCIONES.md` §P4/§P5; retiradas `MPX5500DP.md`×2 y `BMP280.md`; `tools/README.md` de P4. |

---

## 4. Aspectos correctos verificados

- Algoritmo de compensación del BMP180 (`lib/bmp180.py` y `p4.cpp`): idéntico al datasheet Bosch,
  aritmética entera, coincide con el ejemplo del manual (T=15.0 °C, h≈3139 m).
- Mapeo pulso↔ángulo de la clase `Servo` (`lib/servo.py`): coincide con el Cuadro 2 del manual p5
  (90° → 1450 µs → `duty_u16` ≈ 4751).
- Pines ULN2003 P7: ESP32 y RP2040 coinciden con el Cuadro 9 del manual p7.
- ARINC 429 BNR de P2 (`generarArincWord`): SSM en bits 30–31, dato en 11–29, Label 1–8, paridad
  impar en el bit 32 — conforme al manual.
- Estructura de carpetas por práctica (`boot.py`, `main.py`, `pymakr.conf`, `PINES.md`, `README.md`,
  `assets/wiring.{mmd,svg}`, `docs/oscilograma.md`) uniforme y conforme a
  `MicroPython/ESP32/CHECKLIST_PRACTICAS.md`.

---

## 5. Cómo se re-verifica

```bash
# Toolkit PC — 37 pruebas, sin hardware
pip install -r tools/sisela_signal/requirements.txt
PYTHONPATH=tools python -m pytest tools/sisela_signal/tests -q

# Sintaxis MicroPython (los archivos deben compilar/importar en CPython)
find MicroPython -name '*.py' ! -path '*/P2/tools/live_plot.py' -exec python -m py_compile {} +
#   (P2/tools/live_plot.py está roto de origen — ver D-23)

# C++ — con PlatformIO instalado
cd C++/SISELA-CPP && pio run -e esp32dev && pio run -e pico
#   ... con -DPRACTICE=N en platformio.ini para cada práctica
#   Sin PlatformIO: g++ -std=c++17 -fsyntax-only contra un stub de Arduino
#   valida common/siglab.h y src/practices/p{4,5}.cpp (hecho en Fase 1).

# Manuales LaTeX
cd docs/manuales && make          # -> build/p4.pdf (13 pág.), build/p5.pdf (12 pág.)
```

### Estado de la re-verificación (Fase 1, 2026-09-10)

| Comprobación | Resultado |
|---|---|
| `pytest tools/sisela_signal/tests` | **37 passed** |
| `py_compile` de todo `MicroPython/**/*.py` (salvo D-23) | **OK** |
| `g++ -fsyntax-only` de `p4.cpp`, `p5.cpp` (ESP32 y RP2040) + `siglab.h` | **OK** |
| `make` en `docs/manuales/` | **OK** (p4.pdf 13 pág., p5.pdf 12 pág.) |

### Estado de la re-verificación (Fase 2, 2026-09-14 — solo P8)

| Comprobación | Resultado |
|---|---|
| `py_compile` de todo `MicroPython/**/*.py` (salvo D-23) | **OK**, incluye `lib/esc.py`, `lib/quad_mixer.py` en P8 |
| `g++ -fsyntax-only` de `p4.cpp`…`p8.cpp` (ESP32 y RP2040) + `esc.h`/`quad_mixer.h`/`siglab.h` | **OK** para p4–p6 y p8 (ambas arquitecturas); p7 no se re-verificó (fuera de alcance, stub de `String` incompleto, no relacionado con el código de p7) |
| Regresión de `propulsion.h` sobre `p6.cpp` | **OK** (compila; corrige el comportamiento, D-24) |
