# Checklist de generación de prácticas — MicroPython ESP32 (SISELA-Init)

Flujo compacto para crear una práctica completa desde el `_template`, basado en P1–P3.

## 1. Preparación

- [ ] Identifica el número de práctica (PN) y el objetivo principal.
- [ ] Lista materiales (placa, sensores/actuadores, resistencias, cables).
- [ ] Define pines GPIO a usar (ADC, digital, I2C, SPI, etc.).
- [ ] Revisa si necesitas calibración ADC (opcional); si sí, consulta `_template/CALIBRACION.md`.

## 2. Estructura de archivos (copia desde _template)

- [ ] Crea carpeta `MicroPython/ESP32/PN/`.
- [ ] Copia desde `_template/` o genera:
  - `boot.py` — mensaje de arranque.
  - `main.py` — lógica principal (config, utilidades, clases, modos, menú).
  - `pymakr.conf` — configuración mínima (name, safe_boot_on_upload, py_ignore).
  - `.gitignore` — artefactos comunes.
  - `lib/.gitkeep` — carpeta de módulos.
  - `README.md` — guía de uso (objetivos, materiales, conexiones, modos, verificación).
  - `PINES.md` — tabla de pines y notas.
  - `assets/wiring.mmd` — diagrama Mermaid.
  - `assets/wiring.svg` — diagrama estático.
  - `docs/oscilograma.md` — descripción de señales/CSV (si aplica).

## 3. Código principal (main.py)

- [ ] Importa módulos base (machine, utime/time, uselect, ujson/json, sys, math si necesitas).
- [ ] Polyfills para análisis fuera de la placa (sleep_ms, ticks_ms, ticks_diff).
- [ ] Define parámetros hardcodeados al inicio (pines, constantes, sample rate).
- [ ] Inicializa HW (ADC con atenuación 11dB si usas ADC, Pin, PWM, I2C, etc.).
- [ ] Utilidades: lectura con promedio, conversión, filtros simples.
- [ ] (Opcional) Funciones de calibración: load_calibration(), save_calibration(), adc_to_voltage().
- [ ] Modos separados en funciones (ej: mode_raw, mode_converted, mode_csv, mode_calibration_wizard).
- [ ] Menú por REPL con timeout (menu_select) y tecla `m` para volver (check_menu_break).
- [ ] main() que llama al menú en bucle.

## 4. README.md

- [ ] Título: "Práctica PN — [Descripción] (ESP32 + MicroPython)"
- [ ] Objetivos (3–5 bullets).
- [ ] Materiales (placa, sensores, R, cables).
- [ ] Conexiones: enlace a `PINES.md` y diagrama `assets/wiring.svg`.
- [ ] Mapa de pines (resumen rápido).
- [ ] Uso con Pymakr (pasos 1–4).
- [ ] Modos (descripción breve de cada uno).
- [ ] Parámetros ajustables en `main.py`.
- [ ] Verificación (criterios de éxito).
- [ ] (Opcional) Sección "Calibración (opcional)" si aplica.
- [ ] Notas y limitaciones (no linealidad ADC, voltajes, etc.).
- [ ] Visualización: enlace a `docs/oscilograma.md` o scripts en `tools/`.
- [ ] Recursos (links oficiales, datasheets, ecuaciones).

## 5. PINES.md

- [ ] Tabla con: Señal | Pin ESP32 | Descripción.
- [ ] Notas de atenuación ADC, entrada‑solo, pull-ups, etc.
- [ ] Diagrama de conexiones: enlace a `assets/wiring.svg` y `assets/wiring.mmd`.
- [ ] Relación con los modos del programa.
- [ ] (Opcional) Subsección "Calibración rápida (opcional)" con pasos GND/3V3 si aplica.

## 6. Diagramas (assets/)

- [ ] `wiring.mmd` — flowchart/graph Mermaid con nodos, GPIOs y dispositivos.
- [ ] `wiring.svg` — versión estática (genera con `mmdc -i wiring.mmd -o wiring.svg -b transparent`).
- [ ] Incluye notas visuales (resistencias, pull-ups, atenuación).

## 7. Docs adicionales

- [ ] `docs/oscilograma.md` — formato CSV, ondas esperadas, consejos de medida.
- [ ] (Opcional) `docs/[SENSOR].md` — ficha técnica del sensor/actuador (rango, sensibilidad, offset, ecuaciones).

## 8. Herramientas de visualización (opcional, tools/)

- [ ] Script Python para PC: `tools/live_plot.py` (lee puerto serie, grafica con Matplotlib).
- [ ] `tools/requirements.txt` con pyserial, matplotlib, etc.
- [ ] README o comentarios en el script con uso rápido.

## 9. Pymakr y prueba

- [ ] Abre carpeta `MicroPython/ESP32/PN` en VS Code.
- [ ] Conecta ESP32, selecciona puerto COM y "Connect" en Pymakr.
- [ ] "Sync project" → "Run" o reinicia la placa.
- [ ] Verifica menú en REPL, selecciona modos, escribe `m` + ENTER para volver.
- [ ] Valida lectura de sensores/actuadores según criterios de verificación.

## 10. Control de calidad

- [ ] Lint/Typecheck: avisos de módulos MicroPython son esperables en PC.
- [ ] Ejecuta en placa: verifica arranque, menú, modos, señales.
- [ ] (Opcional) Ejecuta calibración (modo 5 o similar) si implementaste.
- [ ] (Opcional) Prueba herramientas de visualización en PC con datos reales.

## Reutilización para PN+1

- Duplica carpeta PN → PN+1.
- Ajusta parámetros, pines, sensores en `main.py`.
- Actualiza README, PINES, diagramas según nueva práctica.
- Mantén estructura de modos, menú y calibración si aplican.

---

Consulta `_template/CALIBRACION.md` para detalles de calibración ADC opcional.
