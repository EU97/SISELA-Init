# Práctica 3 — Medición de Temperatura con NTC o LM35 (ESP32 + MicroPython)

Esta práctica mide temperatura usando un termistor NTC en divisor resistivo o un sensor LM35 conectado al ADC del ESP32. Incluye selección de sensor, modos por sensor y monitores CSV para graficar.

## Objetivos
- Cablear y leer desde el ADC del ESP32 tanto un divisor NTC como un LM35.
- Calcular temperatura con ecuación Beta (NTC) o lineal (LM35: 10 mV/°C).
- Registrar datos en CSV para analizar dinámica térmica y ruido (10 Hz).

## Materiales
- ESP32 DevKit.
- Opción NTC: NTC 10kΩ @25°C (Beta≈3950) + resistencia serie 10kΩ (1%).
- Opción LM35: LM35DZ o similar (Vout proporcional a °C).
- Protoboard, cables, multímetro (opcional).

## Conexiones

![Wiring](./assets/wiring.svg)

- Ver `PINES.md` para tabla de pines y notas.
- Esquema Mermaid editable: `assets/wiring.mmd`.

### Mapa de pines (resumen)
- ADC: GPIO34 (ADC1, entrada‑solo)
- NTC: 3V3 → 10kΩ (R_SERIES) → nodo → NTC 10kΩ → GND; nodo → GPIO34
- LM35: Vout → GPIO34, Vs → 3V3, GND → GND

## Uso (Pymakr)
1) Abre `MicroPython/ESP32/P3` en VS Code.
2) Conecta el ESP32, selecciona el puerto COM en Pymakr y “Connect”.
3) “Sync project” para subir archivos; “Run” o reinicia la placa.
4) En el REPL:
   - Primero elige el sensor (1=NTC, 2=LM35). Timeout 5s (por defecto NTC).
   - Luego elige el modo del sensor actual. Timeout 6s (por defecto: NTC→3, LM35→2).
   - Teclea `m` + ENTER para volver al menú de modos del sensor ACTUAL (no re‑selecciona sensor). CTRL+C reinicia.

## Modos por sensor

### NTC (termistor, R0=10kΩ, Beta=3950)
1. ADC crudo: imprime `adc` y `V(nodo)`.
2. Resistencia: estima `Rntc`.
3. Temperatura: calcula `T(°C)` con Beta.
4. Monitor CSV: `t_ms,adc,v_node_v,r_ntc_ohm,t_c`

### LM35 (10 mV/°C)
1. ADC crudo: imprime `adc` y `V(nodo)`.
2. Temperatura: `T(°C) = V * 100`.
3. Monitor CSV: `t_ms,adc,v_node_v,t_c`

Notas CSV:
- Frecuencia aprox.: 10 Hz (cada 100 ms).
- Presiona `m` para regresar al menú del sensor actual sin perder la selección.

### Calibración (opcional — NTC)
- Modo 5 dentro de NTC: Calibración ADC (guía). Deshabilitada por defecto.
- Procedimiento desde el REPL:
  1) Conecta el nodo (GPIO34) a GND y escribe `ok` + ENTER.
  2) Conecta el nodo a 3V3 y escribe `ok` + ENTER.
  3) Se guardará `calibration.json` con `low` y `high`.
- Para usar la calibración, edita en `main.py`:
  - Cambia `AUTO_USE_CALIBRATION = True` (por defecto `False`).
  - Al iniciar, se cargará `calibration.json` y se usará en el mapeo `adc → voltaje`.

## Parámetros ajustables (en `main.py`)
- `ADC_PIN=34`, `SAMPLES=16` (promedio por lectura).
- `V_SUPPLY=3.3`, `R_SERIES=10000`, `NTC_R0=10000`, `NTC_BETA=3950`, `T0_K=273.15+25`.

## Verificación
- A temperatura ambiente (~20–30°C), la `t_c` debe estar cerca de esa referencia.
- NTC: al tocar la NTC, `t_c` sube; al soltar, baja.
- LM35: respuesta lineal con el voltaje leído (`V * 100 = °C`).

## Notas y limitaciones
- El ADC del ESP32 presenta no linealidad; sin calibración, las lecturas son aproximadas.
- Para mejores resultados, mide la `V_SUPPLY` real y actualízala.
- Evita saturar 3.3V: usa 11dB de atenuación (configurado en el código).
- La calibración low/high mejora offset/ganancia pero no corrige no linealidades.
- El menú `m` retorna al menú de modos del sensor actual (no cambia de sensor).

## Visualización
- `docs/oscilograma.md` describe el CSV y las formas esperadas.
- Puedes graficar con Python (Matplotlib/Pandas) o Excel.

## Recursos
- MicroPython ADC (ESP32): https://docs.micropython.org/en/latest/esp32/quickref.html#adc-analog-to-digital-conversion
- Termistores NTC — Ecuación Beta/Steinhart‑Hart (referencia general)
- LM35 (overview): https://www.ti.com/lit/ds/symlink/lm35.pdf
