# Reporte de verificación — Prácticas P1–P8 (SISELA-Init)

**Fecha:** 2026-09-10 (Fase 1) · 2026-09-14 (Fase 2, solo P8) · 2026-09-17 (verificación
mayor: PlatformIO real, manuales p6–p8, alternativa de trabajo en casa — §6; herramientas
de recolección/despliegue de datos — §7; revisión de integridad completa — §8)
**Alcance:** auditoría de consistencia entre los **manuales** (`~/Descargas/manuales/Manuales/pN.pdf`,
generados con LaTeX/MiKTeX, sin fuentes `.tex` en el repo) y las **cuatro implementaciones**:
MicroPython/ESP32, MicroPython/RP2040, C++/PlatformIO (ESP32) y C++/PlatformIO (RP2040).
**Metodología:** lectura de los 8 PDF, de `main.py`/`pN.cpp` de cada práctica, de los drivers
(`lib/*.py`, `src/common/*.h`), de `README.md`, `REPORTE_FUNCIONES.md` y de los `PINES.md`/`docs/`.

> **Regla de trabajo del proyecto:** P1–P3 se consideran **cerradas** (no se modifica su código;
> solo se documentan inconsistencias y se pueden añadir *tools* opcionales). P4–P8 se actualizan
> para incorporar los paradigmas de análisis de señales. **Excepción puntual (2026-09-17,
> §8.5):** a petición explícita del usuario ("haz que todo el código funcione") se extendió a
> P1/P2 el mismo *guard* de importación PC (D-39) ya aplicado en P4–P8 — un cambio
> estrictamente aditivo que no altera el comportamiento en hardware real.

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
| D-11 | 🟠 | `MicroPython/{ESP32,RP2040}/P6/main.py` | Sin *guard* `try/except`; no importa en PC | 8 (revisión de integridad) | ✅ *guard* + polyfills (`Pin`/`PWM`/`ADC`/`time`/`uselect`) añadidos, mismo patrón que P4/P5 |
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
| D-12 | 🟡 | `MicroPython/ESP32/P6/lib/actuator_pwm.py` | Reinterpretado: **no** es una asimetría ESP32-tiene/RP2040-no-tiene — es código **muerto** en ambos: `main.py` de P6 nunca lo importa (construye el PWM inline), duplica `_set_duty_percent()` | 8 | ✅ archivo eliminado (huérfano, sin referencias en todo el repo) |
| D-13 | 🟡 | `MicroPython/ESP32/P6/docs/SSD1306.md` | Doc no referenciado por el `main.py` | — | 📝 revisado: es un *stub* de redirección correcto ("Documento reemplazado"), no confunde — sin acción necesaria |
| D-16 | 🟡 | `MicroPython/{ESP32,RP2040}/P7/main.py` | `mode_info`: `_setup_endstop()` en *f-string*, efecto colateral + el ternario `"(configurado)" if _setup_endstop() else ...` **nunca** podía dar `else` (`_setup_endstop()` siempre devolvía un `Pin` truthy o lanzaba excepción) | 8 | ✅ `_setup_endstop()` ahora captura la excepción y devuelve `None` en fallo; `mode_info()` recibe el `endstop` ya creado por `main()` en vez de recrearlo |
| D-17 | 🟡 | `MicroPython/RP2040/P7/main.py` | ULN2003 en GP26–28 (pines ADC) | — | 📝 ampliado: nota añadida en `PINES.md` explicando la restricción para quien extienda P7 con un modo ADC futuro |
| D-19 | 🟡 | `README.md` | Enlaces truncados en «Acceso rápido» | 8 | ✅ lista completa de enlaces a las 16 combinaciones (P1–P8 × ESP32/RP2040), todas verificadas |
| D-20 | 🟠 | `MicroPython/ESP32/P5/{docs/BMP280.md,tools/live_plot.py}` | Restos de plantilla de otra práctica (sensor barométrico en una práctica de servos): `live_plot.py` esperaba CSV `t_ms,temp_C,press_hPa,press_kPa,altitude_m`, formato que P5 (servo) nunca emite; el propio `tools/README.md` lo documentaba como "legacy" pero luego incluía ejemplos de uso (`--alt-zero`) que lo presentaban como válido. | 1 (reabierto y cerrado en la pasada de herramientas, ver §7) | ✅ `BMP280.md` eliminada (Fase 1); `live_plot.py` **eliminado** y `tools/README.md` reescrito para apuntar a `tools/sisela_signal` (§7) |
| D-21 | 🟡 | `MicroPython/RP2040/{P5,P6}/{README.md,PINES.md,docs/oscilograma.md}`, `SCRIPTS_UTILIDAD.md` | Ampliado: `GUIA_MIGRACION.md` no existe **en ningún lado** del repo (no solo mal enlazado — el archivo nunca existió), referenciado desde **6 archivos**; además la ruta relativa de P5/README.md línea 14 tenía un nivel de más (`../../` en vez de `../../../`) | 8 | ✅ los 6 enlaces corregidos a `docs/VERIFICACION_PRACTICAS.md` (comparativa real y mantenida); alias de PowerShell en `SCRIPTS_UTILIDAD.md` actualizado |
| D-22 | 🔴 | `MicroPython/{ESP32,RP2040}/P4/docs/oscilograma.md` | Todo el documento describía el MPX5500DP (CSV `pressure_kPa`, `adc_raw`) — sensor obsoleto | 1 | ✅ reescrito para BMP180 + modos 6–7 |
| D-23 | 🟠 | `MicroPython/ESP32/P2/tools/live_plot.py` | **Archivo Python roto de origen**: líneas 2–3 eran `"""` seguido de `"""Live plotter...` → `SyntaxError` (docstring vacío + apertura de cadena sin cerrar). El script nunca se había podido ejecutar. `main.py` de P2 no se ve afectado (P2 sigue sin cambios de firmware — la regla de "P1–P3 congeladas" solo aplica al código de la placa; el plan siempre permitió *tools* opcionales). | 3 → resuelto en la pasada de herramientas (§7) | ✅ línea duplicada eliminada; de paso se corrigió un `SyntaxWarning` (`\l` sin escapar) en la misma docstring. Verificado: compila, `--help` funciona, y su formato CSV esperado coincide exactamente con el que emite `P2/main.py` (`t_ms,raw,avg,voltage_v,angle_deg,flap_deg,ssm,arinc_hex`) |
| D-32 | 🔴 | `tools/sisela_signal/scopeio.py::_parse_generic` | La ruta "genérica" para CSV de osciloscopio (usada cuando el archivo no coincide con las firmas Rigol/Siglent/Tektronix) **ignoraba el sufijo de unidad del encabezado de tiempo** (`t_us`, `t_ms`) y asumía siempre segundos — a diferencia de `dataio.load_capture`, que sí lo detecta. Con un CSV `t_us,v` de 1 kHz real, `scope`/`--scope` reportaba Fs≈0.2 Hz y duración≈20000 s (¡1250× fuera!) **sin error**, solo un número silenciosamente incorrecto — riesgo real de que un reporte de laboratorio quede con una Fs o un ancho de banda mal calculado sin que nadie lo note. | 4 (pasada de herramientas, §7) | ✅ reutiliza el mismo `_time_scale()` de `dataio.py`; test de regresión `test_scope_generic_two_column_time_in_microseconds` añadido (38/38 en verde) |
| D-33 | 🔴 | `MicroPython/ESP32/P8/lib/landing_gear.py` (RP2040 **no** estaba afectado — ver nota) | **Bug funcional severo, nunca antes detectado, específico de ESP32/P8**: (a) `HAS_ULN2003` se ponía en `False` dentro de la propia rama `try` de éxito (typo — debía ser `True`), así que el driver ULN2003 del tren de aterrizaje jamás podía seleccionarse aunque el archivo existiera; (b) **los archivos `stepper_a4988.py`/`stepper_uln2003.py` no existían en absoluto** en `ESP32/P8/lib/` (ni se documentaba copiarlos desde P7) — en hardware real, `LandingGear.__init__()` con driver A4988 (el *default* de `main.py`) **siempre lanzaba `RuntimeError`**; (c) aun con los archivos presentes, `landing_gear.py` llamaba a una API que no existe en ningún driver real del repo: `self.driver.set_direction(1/0)` (ningún driver tiene ese método; el real es `set_dir(cw)`) y `self.driver.step()` sin argumentos (el real exige `step(steps, interval_us=None)`), además del *kwarg* `en_pin=` que no coincide con ningún constructor real (`pin_en` en la variante ESP32/P7, `enable_pin` en la RP2040/P7). El subsistema de tren de aterrizaje de **ESP32**/P8 estaba roto de origen. **Nota:** `RP2040/P8/lib/landing_gear.py` es una implementación *independiente y ya correcta* — ya tenía `HAS_ULN2003=True`, los drivers ya existían en `RP2040/P8/lib/`, y ya usaba un adaptador `_step_once()`/`_set_direction()` con `hasattr()` para tolerar cualquiera de las dos APIs de driver; solo le faltaba el *guard* de importación de `Pin` (ver D-34). | 8 (revisión de integridad) | ✅ copiados `stepper_a4988.py`/`stepper_uln2003.py` (variante RP2040/P7) a `ESP32/P8/lib/`; `HAS_ULN2003` corregido a `True`; llamadas reescritas a la API real (`step(1)`/`step(-1)`, kwarg `enable_pin=`); los mismos 2 archivos en `RP2040/P8/lib/` se sincronizaron a la misma variante (cambio cosmético, la API ya coincidía) además de recibir el mismo *upgrade* de polyfill. Probado de extremo a extremo instanciando `LandingGear` con ambos drivers en ambas plataformas y ejecutando `extend()`/`retract()`/`homing()` con éxito |
| D-34 | 🟠 | `MicroPython/{ESP32,RP2040}/P7/main.py`, `MicroPython/{ESP32,RP2040}/P8/main.py` + `P8/lib/{sensors,flight_controls,propulsion,esc}.py` | Mismo defecto que D-11 pero nunca catalogado para P7/P8: imports de `machine`/`utime`/`uselect` sin *guard*, y en P8 además 4 módulos de `lib/` con `from machine import ...` directo — nada de P7/P8 podía importarse fuera de la placa (ni siquiera para verificación estática). El polifill de `Pin` en `stepper_a4988.py`/`stepper_uln2003.py` (`Pin = None`) tampoco alcanzaba en cuanto algo instanciaba realmente esas clases. | 8 | ✅ *guard* + polyfills añadidos en los 2 archivos `main.py` de P7 y en `main.py` + 5 archivos de `lib/` de P8 (ambas plataformas, 14 archivos en total); polyfill de `Pin` en los drivers de stepper mejorado a clase completa (antes `Pin = None`, ahora clase con `IN/OUT/PULL_UP` y `value()`) |
| D-35 | 🟡 | `README.md` (raíz) | Enlaces muertos a `C++/SISELA-CPP/COMPILE_TEST.md`, `IMPLEMENTATION_STATUS.md` y mención de `STATUS.txt` — ninguno de los 3 existe en el repo | 8 | ✅ reemplazados por referencias a `QUICK_START.md` (ya cubre compilación) y `docs/VERIFICACION_PRACTICAS.md` (ya cubre estado/bitácora) |
| D-36 | 🟡 | `MicroPython/RP2040/README.md` | Listaba `RESUMEN_TRADUCCION.md` y `CHECKLIST_PRACTICAS.md` como documentos "✅" existentes — ninguno de los dos existe en el repo (además de `GUIA_MIGRACION.md`, ver D-21); también describía P4 como "Presión MPX5500DP" (mismo problema que D-3/D-4, pero en este README específico nunca se corrigió) | 8 | ✅ quick-start, tabla de documentación y diagrama de carpetas corregidos para no listar archivos inexistentes (apuntan a `../../README.md` y `../../docs/VERIFICACION_PRACTICAS.md`); descripción de P4 corregida a BMP180 |
| D-37 | 🟡 | `docs/manuales/p7.tex` §"Caso 3" | El manual recreado en la verificación mayor (§6) describía en tiempo presente "El firmware recibe una trama hexadecimal (simulando Label 204)..." para ARINC 429 — pero P7 **no tiene ninguna línea de código relacionada con ARINC** (grep vacío). Inconsistencia manual↔firmware introducida al recrear el manual desde el PDF original (que sí lo presentaba así). | 8 | ✅ reencuadrado como "Caso 3 (ejercicio de diseño)" con una nota explícita aclarando que no está implementado en el firmware actual; recompilado sin errores (16 pág., sin cambios en warnings) |
| D-38 | 🟡 | `REPORTE_FUNCIONES.md` | Dos problemas de staleness: (a) comparativa RP2040 vs ESP32 de P4 todavía decía "MPX5500DP funciona mejor con 5V" como si fuera el sensor actual; (b) la sección de P8 solo documenta los Modos 1–7 (base), sin mención de los Modos 8 (dron) y 9 (análisis de señales) añadidos en la Fase 2 | 8 | ✅ comparativa de P4 corregida a BMP180/I2C; nota añadida en P8 señalando los Modos 8–9 y apuntando a `docs/dron_2212.md`/`docs/analisis_senales.md` |
| D-39 | 🟡 | `MicroPython/{ESP32,RP2040}/P1`, `P2` | **P1 y P2 tampoco importan fuera de la placa** (mismo patrón que D-11/D-34: `machine`/`utime`/`time.ticks_*` sin *guard*, y en P1/P2 además con instanciación de hardware a nivel de módulo — `led1 = make_led(...)`, `adc = ADC(Pin(...))` — que se ejecuta inmediatamente al importar). | 8 (ampliado a petición explícita: "haz que todo el código funcione") | ✅ el usuario autorizó explícitamente extender la corrección a P1/P2 pese a la regla de congelamiento, dado que el *guard* es puramente aditivo (try/except alrededor del import; en la placa real nunca se activa la rama de *fallback*, cero cambio de comportamiento). Aplicado el mismo patrón de *polyfills* que en D-11/D-34 a los 4 archivos (`ESP32/P1`, `RP2040/P1`, `ESP32/P2`, `RP2040/P2`). Las **16 combinaciones** (P1–P8 × ESP32/RP2040) importan limpio en PC. |
| D-26 | 🔴 | `C++/.../include/pins/pins_types.h`, `pins_esp32.h`, `pins_rp2040.h` | **Todo el C++ nunca había compilado con PlatformIO real** (solo se había verificado con un *stub* de `g++`, ver §5). `Pins`/`StepperA4988Pins`/`StepperULN2003Pins` tienen inicializadores de miembro por defecto, lo que en `-std=gnu++11` (el estándar por defecto de los cores Arduino ESP32/RP2040) les quita la condición de *agregado* → las tablas de pines de **las 8 prácticas** fallaban con `error: could not convert ... to 'Pins'`. | 4 (verificación mayor) | ✅ `-std=gnu++17` en `platformio.ini` |
| D-27 | 🟠 | `C++/.../src/practices/p1.cpp`, `p7.cpp` | `loop()` llama a `mode_blink/mode_chaser/mode_monitor/mode_integrated` (p1) y `mode_jog/mode_move_n/mode_sweep/mode_homing` (p7) **antes** de su definición en el archivo, sin *forward declaration* → `error: 'mode_X' was not declared in this scope`. Nunca se había compilado realmente. | 4 | ✅ *forward declarations* añadidas |
| D-28 | 🔴 | `C++/.../src/practices/p4.cpp` | Las variables `B1`/`B2` (coeficientes de calibración BMP180) colisionan con las macros `B0..B11111111` de `binary.h` del core Arduino (`#define B1 1`) → `error: expected unqualified-id before numeric constant` en la propia declaración. Nunca se había compilado realmente. | 4 | ✅ renombradas a `Bc1`/`Bc2` |
| D-29 | 🔴 | `C++/.../src/common/siglab.h`, y `Serial.printf(...)` directo en `p1–p8.cpp` (53 llamadas) | El core Arduino-mbed de RP2040 (el que trae `platform = raspberrypi` por defecto) **no implementa `Stream::printf`/`Serial.printf`** (a diferencia del core ESP32) → `error: 'class arduino::...' has no member named 'printf'`. Afectaba a **todas** las prácticas que se compilaran con ese `PRACTICE` activo (P1 confirmado; P4/P5/P8 vía `siglab.h`, incluido *siempre*, aunque el resto del archivo esté apagado por `#if PRACTICE==N`, porque `Stats`/`BlockResult` no son plantillas y se compilan igual). Nunca se había compilado con PlatformIO de verdad para `pico`. | 4 (verificación mayor) | ✅ helper `serialPrintf(Stream&, fmt, ...)` (vsnprintf + print) en `include/board_config.h`, usado por las 8 prácticas y por `siglab.h` |
| D-30 | 🔴 | `C++/.../src/common/flight_controls.h`, `esc.h` | `analogWriteFreq()`/`analogWriteRange()` (fijan 50 Hz para servos/ESC) son API del core **earlephilhower** (arduino-pico), no del core Arduino-mbed oficial que `platformio.ini` estaba resolviendo por defecto para `board = pico` → `error: 'analogWriteFreq' was not declared in this scope`. Bug de configuración de plataforma, no de código: el firmware siempre asumió earlephilhower (macros `GPx`, esta API de PWM), pero el `.ini` nunca lo fijó explícitamente. | 4 | ✅ `board_build.core = earlephilhower` en `[env:pico]` de `platformio.ini` |
| D-31 | 🔴 | `C++/.../src/practices/p4.cpp` | `Wire.begin(SDA_P, SCL_P)` (forma de 2 argumentos, estilo ESP32) no existe en `TwoWire` del core RP2040 earlephilhower, que solo acepta `begin()`/`begin(address)` — los pines se fijan antes con `setSDA()`/`setSCL()`. | 4 | ✅ `#ifdef ARDUINO_ARCH_ESP32` con rama RP2040 (`setSDA/setSCL` + `begin()`) |

**Nota de alcance (Fase 2, histórica):** esa fase se acotó explícitamente a **solo P8**
(«genera la fase 2, solo vamos a cambiar la práctica 8»). Las acciones de P6/P7 previstas en el
plan original (D-11, D-12, D-14, D-16) seguían abiertas y se marcaban «no solicitada» — no se
tocó ningún archivo de P6/P7 salvo el efecto colateral de la corrección de `propulsion.h`
(D-24), que es un header compartido y no cambia el comportamiento correcto de P6 (lo corrige).
En la **verificación mayor** posterior (§0) se recrearon también los manuales `p6.tex`/`p7.tex`
(sin tocar su firmware) y se corrigieron D-26/D-27/D-28, que afectan a las 8 prácticas C++ por
igual.

🔴 contradicción documental / bug de compilación · 🟠 divergencia funcional · 🟡 menor / cosmético

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
find MicroPython -name '*.py' -exec python -m py_compile {} +
#   (D-23 corregido en la pasada de herramientas — P2/tools/live_plot.py ya no
#   necesita excluirse, ver §7)

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

---

## 6. Verificación mayor (2026-09-17)

A petición del usuario, antes de continuar con más manuales se hizo una pasada de
verificación de fondo sobre **las 8 prácticas**, con foco en tres cosas que no se habían
hecho hasta ahora: (a) compilar el C++ con el **PlatformIO real** (no solo un *stub* de
`g++`), incluyendo por primera vez una compilación real del entorno `pico` (RP2040);
(b) confirmar que cada práctica tiene las **herramientas** necesarias para
ejecutarse, y (c) añadir a los manuales P4–P8 una sección de **alternativa de trabajo en
casa** (multímetro + simulación) para cuando no hay osciloscopio/generador de banco.
Al final de la pasada, **las 8 prácticas compilan limpio en ambas arquitecturas**
(`esp32dev` y `pico`) y **los 5 manuales P4–P8 compilan sin errores ni referencias
indefinidas** (ver §6.2 y §6.5).

### 6.1 Firmware — py_compile (MicroPython, las 8 prácticas)
`find MicroPython -name '*.py' ! -path '*/P2/tools/live_plot.py' -exec python -m
py_compile {} +` → **OK** en las 4 combinaciones (ESP32/RP2040 × P1–P8). Único archivo
excluido: D-23 (roto de origen, fuera del alcance de esta pasada).

### 6.2 C++ — compilación real con PlatformIO (novedad de esta pasada)
Se instaló PlatformIO Core 6.2.0 en un entorno virtual y se compilaron **las 8
prácticas**, ambas variantes de *stepper* (A4988/ULN2003) donde aplica, en **ambos
entornos** (`esp32dev`, `pico`). Esto reveló **6 bugs de compilación reales que el
*stub* de `g++` no detectaba** (D-26 a D-31 — ver §3), presentes desde que se creó
el proyecto C++ unificado: **el código C++ nunca se había compilado de verdad con
PlatformIO**, y menos aún para RP2040 (el entorno `pico` nunca se había construido ni
una sola vez antes de esta sesión). Tres bugs (D-26/27/28) afectaban a `esp32dev` y
`pico` por igual; los otros tres (D-29/30/31) eran **específicos de RP2040**: el core
por defecto que PlatformIO resuelve para `platform = raspberrypi` + `board = pico`
(Arduino-mbed oficial) no es el que el firmware asume (earlephilhower/arduino-pico) —
le faltan `Stream::printf` y `analogWriteFreq/Range`, y su `Wire.begin()` no acepta
pines. Fijar `board_build.core = earlephilhower` en `platformio.ini` resuelve la
causa raíz de D-30 (y habría evitado D-29 también, aunque el *helper* `serialPrintf`
portátil se mantiene por ser más robusto frente a futuros cambios de core). Tras
corregir los seis:

| Práctica | esp32dev | pico (RP2040) | Variante adicional |
|---|:--:|:--:|---|
| P1 | ✅ | ✅ | — |
| P2 | ✅ | ✅ | — |
| P3 | ✅ | ✅ | — |
| P4 | ✅ | ✅ | — |
| P5 | ✅ | ✅ | — |
| P6 | ✅ | ✅ | — |
| P7 | ✅ | ✅ | ✅ `-DSTEPPER_ULN2003` (esp32dev y pico) |
| P8 | ✅ | ✅ | — |

Las 8 prácticas compilan sin error ni advertencia de compilación (más allá de los
`warning: "PRACTICE" redefined` cosméticos que emite `PLATFORMIO_BUILD_FLAGS` al
duplicar el `-DPRACTICE` del `.ini`, inocuos) en ambas arquitecturas. `pico` bajó de
~700 s (con el core mbed, que reconstruye el framework RP2040 completo) a ~3 s por
práctica (con earlephilhower, usando caché de compilación incremental).

**Cómo se reprodujo** (no requiere instalar PlatformIO globalmente):
```bash
python3 -m venv .venv-pio && .venv-pio/bin/pip install platformio
cd C++/SISELA-CPP
.venv-pio/bin/pio run -e esp32dev                              # PRACTICE=1 (default del .ini)
PLATFORMIO_BUILD_FLAGS="-DPRACTICE=4" .venv-pio/bin/pio run -e esp32dev   # cualquier práctica N
PLATFORMIO_BUILD_FLAGS="-DPRACTICE=4" .venv-pio/bin/pio run -e pico      # ídem para RP2040
PLATFORMIO_BUILD_FLAGS="-DPRACTICE=7 -DSTEPPER_ULN2003" .venv-pio/bin/pio run -e pico  # variante ULN2003
```

### 6.3 Herramientas por práctica
Revisión de `MicroPython/{ESP32,RP2040}/P*/tools/`: P4, P5 (ambas plataformas) y, de
forma transversal, `tools/sisela_signal/` cubren las necesidades de P4–P8. P1, P3, P6,
P7 y P8 no tienen una carpeta `tools/` local — no es un defecto: no dependen de un
*preset* de PC para ejecutarse (P1/P3/P6/P7 se verifican con multímetro/osciloscopio
directamente; P8 usa `tools/sisela_signal` igual que P4/P5). Único hueco real: D-23
(script roto en P2, ya documentado).

### 6.4 Alternativa de trabajo en casa (nueva sección en los manuales P4–P8)
Se añadió una sección **«Alternativa de Trabajo en Casa (Multímetro + Simulación)»** a
`p4.tex`–`p8.tex`, con tres bloques por práctica: qué se puede verificar con multímetro
(voltaje promedio de PWM, continuidad, resistencia, modo Hz/Duty% si el equipo lo tiene),
qué se puede verificar con simulación (NI Multisim/Proteus/Wokwi — incluida la
posibilidad de simular fallas peligrosas, como quitar el diodo *flyback*, que nunca deben
probarse en hardware real), y qué **requiere** laboratorio presencial de forma honesta
(el *jitter* de PWM en nanosegundos y el *aliasing* con generador real no tienen
sustituto de multímetro/simulación idealizada). Cada sección cierra con una tabla
resumen por caso/modo.

### 6.5 Manuales — recompilación completa
Los 5 manuales (`p4.tex`–`p8.tex`) se recompilaron desde cero tras los cambios:

| Manual | Páginas | Advertencias |
|---|:--:|---|
| p4.pdf | 13 | ninguna |
| p5.pdf | 12 | 1 *underfull hbox* (cosmético, celda de tabla angosta) |
| p6.pdf | 15 | ninguna |
| p7.pdf | 16 | 2 *underfull hbox* (cosmético, celdas de tabla angostas) |
| p8.pdf | 15 | ninguna |

Sin referencias indefinidas en ningún manual. `p6.tex` y `p7.tex` son recreaciones
completas de los manuales originales (firmware sin cambios) **más** la nueva sección de
trabajo en casa; `p8.tex` añade además las secciones de Análisis de Señales y del
módulo opcional de dron ya implementadas en el firmware (Fase 2).

---

## 7. Verificación de herramientas de recolección/despliegue de datos (2026-09-17)

A petición del usuario, se auditaron **todos** los scripts PC de recolección/visualización
de datos por práctica (`MicroPython/{ESP32,RP2040}/P*/tools/*.py`) y la toolkit compartida
`tools/sisela_signal/`, no solo su sintaxis sino su **ejecución real** (`--help`, y para la
toolkit, cada subcomando contra los *fixtures* sintéticos de `examples/`, generando las
gráficas de verdad con backend `Agg`).

**Inventario:** `P4` (ESP32: `altimeter_gui.py`), `P5` (ESP32: `servo_cli.py`;
RP2040: `servo_cli.py`), `P2` (ESP32: `live_plot.py`) tienen *tools/* propias; el resto
(P1, P3, P6, P7, P8) usa multímetro/osciloscopio directo o `tools/sisela_signal` — no es
un hueco, ya estaba así documentado en §6.3.

**Hallazgos:**

- **D-32 (🔴 nuevo, corregido):** `scopeio.py::_parse_generic` no convertía el sufijo de
  unidad del encabezado de tiempo (`t_us`/`t_ms`) a segundos — a diferencia de
  `dataio.load_capture`. Con un CSV genérico de 1 kHz en microsegundos, `scope`/`--scope`
  calculaba Fs≈0.2 Hz (1250× menor a la real) **sin ningún error**, solo un número
  silenciosamente equivocado. Corregido reutilizando `dataio._time_scale()`; se añadió
  `test_scope_generic_two_column_time_in_microseconds` (suite ahora en **38/38**).
- **D-23 (🟠, finalmente corregido):** `P2/tools/live_plot.py` tenía una línea `"""`
  duplicada que rompía el módulo desde su creación (nunca se había podido ejecutar). Se
  eliminó la línea sobrante y se corrigió de paso un `SyntaxWarning` de escape inválido.
  Verificado que su formato CSV esperado coincide exactamente con el que emite
  `P2/main.py`.
- **D-20 (🟠, finalmente corregido):** `P5/tools/live_plot.py` era un resto de plantilla
  de una práctica de sensor barométrico (BMP280) — P5 es la práctica del servo y **nunca**
  emite el CSV `temp_C,press_hPa,...` que ese script esperaba. El propio `tools/README.md`
  lo llamaba "legacy" pero acto seguido incluía ejemplos de uso con `--alt-zero`,
  contradicción confusa para el estudiante. Se eliminó el script (era código muerto e
  incorrecto, no solo no-usado) y se reescribió `tools/README.md` para apuntar a
  `tools/sisela_signal capture`/`spectrum`, que sí cubre el análisis real de los Modos 5–7
  de P5. `requirements.txt` de P5 (ESP32) también se limpió (`matplotlib` ya no hace falta).

**Confirmado en buen estado (sin cambios):**

- `altimeter_gui.py` (P4): `--help` funciona, *imports* de `tkinter`/`pyserial` con
  *guards* correctos, no requiere cambios.
- `servo_cli.py` (P5, ESP32 y RP2040): idénticos entre sí, `--help` funciona, subcomandos
  `angle`/`pulse`/`sweep` bien definidos.
- `tools/sisela_signal`: los 7 subcomandos (`capture`, `spectrum`, `alias`, `filter`,
  `characterize`, `bode`, `scope`) se probaron contra los *fixtures* de `examples/` y
  producen gráficas correctas y bien etiquetadas (verificado visualmente: espectro con
  pico limpio en la frecuencia esperada, respuesta al escalón con τ/tr/overshoot
  anotados, PWM con forma de onda correcta tras el fix de D-32).
- `RP2040/P4` no tiene carpeta `tools/` propia — **no es un hueco**: su propio `README.md`
  apunta explícitamente a `MicroPython/ESP32/P4/tools/altimeter_gui.py`, que es agnóstico
  de placa (script de PC, se conecta por puerto serie sin importar qué MCU corre el
  firmware).

**Cómo se reprodujo:**
```bash
python3 -m venv .venv-tools
.venv-tools/bin/pip install pyserial matplotlib numpy scipy pytest

# sintaxis + --help de cada script por práctica
find MicroPython -path "*/tools/*.py" -exec python -m py_compile {} \;
MPLBACKEND=Agg .venv-tools/bin/python MicroPython/ESP32/P4/tools/altimeter_gui.py --help
MPLBACKEND=Agg .venv-tools/bin/python MicroPython/ESP32/P2/tools/live_plot.py --help
.venv-tools/bin/python MicroPython/ESP32/P5/tools/servo_cli.py --help

# toolkit compartida: pruebas + smoke test de cada subcomando
PYTHONPATH=tools .venv-tools/bin/python -m pytest tools/sisela_signal/tests -q
MPLBACKEND=Agg PYTHONPATH=tools .venv-tools/bin/python -m sisela_signal spectrum \
  --file tools/sisela_signal/examples/sine_1k.csv --col v --metrics --full-scale 3.3 \
  --save /tmp/spectrum.png
```

---

## 8. Revisión de integridad completa (2026-09-17, pasada final)

A petición explícita del usuario ("ejecuta una revisión completa de todos los detalles
para verificar completa integridad del proyecto y ejecuciones, así como corregir todo"),
se hizo una auditoría exhaustiva de **todas** las discrepancias pendientes (⏳/📝) de §3,
más un escaneo sistemático de enlaces y una verificación de instanciación real (no solo
importación) de los módulos de P8. Todo lo encontrado se corrigió, incluida una extensión
posterior a P1/P2 pedida explícitamente por el usuario (ver §8.5).

### 8.1 Discrepancias de firmware resueltas
D-11 (P6 sin *guard* PC), D-12 (`actuator_pwm.py` muerto), D-16 (bug lógico en
`mode_info`/`_setup_endstop` de P7) — ver detalle en la tabla de §3. Además se descubrió
que **P7 y P8 tampoco tenían *guard* de importación** (D-34, nunca antes catalogado) y se
corrigió en los 14 archivos afectados.

### 8.2 Bug funcional severo en ESP32/P8 — tren de aterrizaje roto de origen (D-33)
Al probar instanciación real (no solo `import main`, sino crear objetos `LandingGear`,
`FlightSensors`, etc. y ejercitar sus métodos), se encontró que **el subsistema de tren de
aterrizaje de ESP32/P8 nunca pudo haber funcionado en hardware real**: los archivos de
driver (`stepper_a4988.py`/`stepper_uln2003.py`) no existían en `ESP32/P8/lib/`, un
*typo* dejaba `HAS_ULN2003` siempre en `False`, y las llamadas usaban una API
(`set_direction()`, `step()` sin argumentos, *kwarg* `en_pin=`) que no coincide con ningún
driver real del repositorio. **RP2040/P8 no tenía este problema**: es una implementación
independiente que ya usaba la API correcta con un adaptador tolerante
(`_step_once`/`_set_direction` vía `hasattr`) — solo le faltaba el *guard* de importación
de `Pin` para poder verificarse fuera de la placa (D-34). Corregido en ESP32 y
**verificado de extremo a extremo** en ambas plataformas: se instanció `LandingGear` con
ambos tipos de driver y se ejecutaron `extend()`, `retract()` y `homing()` con éxito. Esta
clase de bug (funciona al importar, falla al usar) es precisamente lo que motivó ir más
allá de `py_compile`/`import` en esta pasada.

### 8.3 Enlaces documentales
Escaneo automatizado de los 82 archivos `.md` del repo (patrón `]("(...)")`, resolviendo
rutas relativas): se encontraron y corrigieron **13 enlaces rotos** repartidos en 9
archivos, incluyendo una "guía de migración" (`GUIA_MIGRACION.md`) referenciada desde 6
lugares que **nunca existió en el repositorio**, y dos documentos más
(`RESUMEN_TRADUCCION.md`, `CHECKLIST_PRACTICAS.md`) listados con estado "✅" en
`MicroPython/RP2040/README.md` que tampoco existen. Al cierre de esta pasada: **0 enlaces
internos rotos** en todo el repo (los placeholders `path/to/screenshotN.png` de la hoja de
trabajo de P7/RP2040 se revisaron y son una plantilla intencional para que el estudiante
inserte su propia captura, no un enlace roto).

### 8.4 Honestidad manual↔firmware (D-37)
`p7.tex` (recreado en la verificación mayor, §6) describía en tiempo presente una
funcionalidad ARINC 429 que el firmware actual no implementa. Reencuadrado como ejercicio
de diseño explícito, con una nota aclaratoria. Recompilado sin errores.

### 8.5 Extensión a P1/P2 (a petición explícita del usuario)
Tras entregar esta pasada, el usuario pidió explícitamente "corrige todo lo que sea
necesario... haz que todo el código funcione", lo que se interpretó como autorización
para extender el *guard* de importación (D-39) también a P1/P2, pese a que están
"congeladas" — el cambio es puramente aditivo (un `try/except` alrededor de imports que
en la placa real nunca activa su rama de repuesto) y no altera el comportamiento en
hardware. Con esto, **las 16 combinaciones (P1–P8 × ESP32/RP2040) importan limpio en
PC**, no solo P3–P8.

### 8.6 Nota de entorno: *flakiness* del directorio de build de PlatformIO
Durante la re-verificación final de la matriz C++, compilar hacia el directorio por
defecto del proyecto (`.pio/build/`) empezó a fallar de forma intermitente y no
determinista (`fatal error: opening dependency file ...: No such file or directory`,
distinto archivo cada vez) — confirmado **no relacionado con el código**: (a) se
descartaron procesos `pio`/`scons` huérfanos concurrentes (había dos, quedaron de una
interrupción de sesión previa, y se mataron); (b) persistía incluso en compilación
totalmente secuencial (`-j 1`) y con el *sandbox* de ejecución desactivado; (c)
**redirigir la salida a `/tmp`** (`PLATFORMIO_BUILD_DIR=/tmp/...`) con el mismo código
fuente compiló **de forma 100% confiable, las 16 combinaciones**. Causa más probable:
algún proceso externo (sincronización de la carpeta de `Documentos`, indexador, etc.)
interfiriendo con la escritura rápida de muchos archivos pequeños dentro del árbol del
repositorio. **No es necesario ningún cambio en el repo** — si esto se repite, compilar
con `PLATFORMIO_BUILD_DIR=/tmp/algún_directorio pio run ...` es la solución de
contorno.

### 8.7 Verificación final
```
py_compile (MicroPython, las 8 prácticas × 2 plataformas):        OK
import main.py sin guard adicional (16 combinaciones):            16/16 OK
Instanciación real de LandingGear/FlightSensors/... (P8 × 2):     OK
pytest tools/sisela_signal:                                        38/38
C++ pio run -e {esp32dev,pico} × 8 prácticas (+ variante ULN2003): 16/16 OK (vía
  PLATFORMIO_BUILD_DIR=/tmp — ver nota de entorno §8.6)
Enlaces internos en *.md (82 archivos):                            0 rotos
docs/materiales/SISELA_Materiales.xlsx (openpyxl):                 íntegro, 6 hojas
```

**Archivos tocados en esta pasada** (además de los ya listados en §3):
`MicroPython/{ESP32,RP2040}/{P6,P7}/main.py`,
`MicroPython/{ESP32,RP2040}/P8/{main.py,lib/{sensors,flight_controls,propulsion,esc,
landing_gear,stepper_a4988,stepper_uln2003}.py}`,
`MicroPython/RP2040/P7/PINES.md`, `MicroPython/RP2040/{README.md,SCRIPTS_UTILIDAD.md,
P5/README.md,P6/{README.md,PINES.md,docs/oscilograma.md}}`, `README.md` (raíz),
`REPORTE_FUNCIONES.md`, `docs/manuales/p7.tex`.
