# Práctica 4 — Sensor de Presión MPX5500DP (RP2040 + MicroPython)

Lectura analógica (ADC) de un sensor de presión piezoresistivo absoluto MPX5500DP, con conversión a kPa y salida CSV para visualización en tiempo real.

## 🔄 Versión RP2040

Esta es la **adaptación para RP2040** (Raspberry Pi Pico) de la práctica original ESP32. Los cambios principales son:
- **Pin ADC**: GP26 (ADC0) en lugar de GPIO34
- **Resolución ADC**: 16 bits (0–65535) en lugar de 12 bits (0–4095)
- **Sin configuración especial**: No requiere `atten()` ni `width()`
- **Función de lectura**: `adc.read_u16()` en lugar de `adc.read()`

Ver [**GUIA_MIGRACION.md**](../../GUIA_MIGRACION.md) para detalles completos de traducción ESP32→RP2040.

## Objetivos

- Configurar el ADC del RP2040 para leer señales analógicas de sensores.
- Implementar la conversión de voltaje a presión usando la función de transferencia del MPX5500DP.
- Aplicar calibración ADC opcional para mejorar precisión.
- Generar datos en formato CSV para graficado en tiempo real con Python.
- Desarrollar un sistema modular con menú interactivo REPL.

## Materiales

| Cantidad | Componente | Especificación |
|----------|------------|----------------|
| 1 | Raspberry Pi Pico | RP2040 con MicroPython |
| 1 | Sensor MPX5500DP | Freescale/NXP, 20–520 kPa, SOT-223 |
| 1 | Resistencia | 10 kΩ (pull-down opcional para ADC) |
| 1 | Condensador | 0.1 µF cerámico (filtro de alimentación) |
| n | Cables Dupont | Macho-hembra / macho-macho |
| 1 | Fuente 5V | USB (VSYS disponible en Pico) |

**NOTA IMPORTANTE**: El MPX5500DP funciona óptimamente con **VS = 4.75–5.25V**. Con VS=3.3V la sensibilidad disminuye pero el sensor sigue operativo. El RP2040 puede usar **VSYS** (5V del USB) con divisor resistivo (10kΩ + 10kΩ) para proteger el ADC (máx 3.3V).

## Conexiones

Ver detalle completo de pines en [**PINES.md**](PINES.md) y diagrama en [**assets/wiring.svg**](assets/wiring.svg).

**Resumen rápido:**

| Señal RP2040 | Pin | Sensor MPX5500DP | Descripción |
|--------------|-----|------------------|-------------|
| GP26 | ADC0 | Vout (pin 3) | Salida analógica del sensor |
| 3V3(OUT) | — | VS (pin 2) | Alimentación del sensor |
| GND | — | GND (pin 1) | Tierra común |

**Configuración ADC:**
- 16 bits (0–65535) — **Mayor resolución que ESP32**
- Rango fijo 0–3.3V (sin atenuación configurable)
- Promedio de 50 muestras para reducir ruido

## Uso (Pymakr)

1. **Abre la carpeta de la práctica** en VS Code:
   ```
   MicroPython/RP2040/P4/
   ```

2. **Conecta el Raspberry Pi Pico** y selecciona el puerto COM en Pymakr.

3. **Sincroniza y ejecuta**:
   - Botón "Sync project to device" (sube boot.py, main.py).
   - Botón "Run" o reinicia la placa (botón RUN/BOOTSEL doble tap).

4. **Interacción REPL**:
   - Aparecerá el menú con 5 opciones + salida.
   - Escribe el número de modo y presiona ENTER.
   - Durante la ejecución de un modo, escribe `m` + ENTER para regresar al menú.

## Modos de operación

| Modo | Descripción | Salida típica |
|------|-------------|---------------|
| **1** | Lectura ADC cruda | `ADC: 32768` (valor 0–65535) |
| **2** | Voltaje del sensor | `Voltaje: 1.65 V  (ADC: 32768)` |
| **3** | Presión en kPa | `Presión: 270.00 kPa  (V: 1.65, ADC: 32768)` |
| **4** | Monitor CSV continuo | `timestamp_ms,adc_raw,voltage_V,pressure_kPa` |
| **5** | Asistente de calibración ADC | Wizard interactivo (opcional) |
| **q** | Salir del programa | — |

### Detalles de cada modo

- **Modo 1 (ADC crudo)**: Lee el valor digital del ADC (0–65535) con promedio de 50 muestras. **16 bits = mayor precisión que ESP32**.

- **Modo 2 (Voltaje)**: Convierte ADC a voltaje (0–3.3V). Si calibración está activa, aplica corrección lineal.

- **Modo 3 (Presión kPa)**: Usa la función de transferencia del MPX5500DP para convertir voltaje a presión absoluta. Rango: 20–520 kPa.

- **Modo 4 (CSV)**: Imprime datos en formato `timestamp_ms,adc_raw,voltage_V,pressure_kPa` cada 100 ms (10 Hz). Ideal para capturar con `tools/live_plot.py` desde PC.

- **Modo 5 (Calibración)**: Wizard interactivo que mide ADC en GND y 3V3, guarda `calibration.json`. Ver sección [Calibración](#calibración-opcional).

## Parámetros ajustables (main.py)

```python
ADC_PIN = 26               # Pin GPIO del ADC (GP26 = ADC0)
ADC_SAMPLES = 50           # Número de muestras para promedio
SAMPLE_RATE_MS = 100       # Periodo de muestreo (ms)

V_SUPPLY = 3.3             # Voltaje de alimentación del sensor (V)
P_MIN = 20.0               # Presión mínima del sensor (kPa)
P_MAX = 520.0              # Presión máxima del sensor (kPa)

AUTO_USE_CALIBRATION = False  # Activar calibración automática
```

## Verificación

1. **Arranque**: Mensaje `=== Práctica 4: Sensor de presión MPX5500DP (RP2040) ===` en REPL.
2. **Menú funcional**: Selección 1–5 y `q` responde correctamente.
3. **Modo ADC**: Valor estable (~32000–40000 ADC al aire libre, depende de presión atmosférica local).
4. **Modo presión**: Lectura ~101 kPa (presión atmosférica estándar a nivel del mar). Variación ±10 kPa según altitud.
5. **Modo CSV**: Flujo continuo de líneas con formato correcto, timestamp incremental.
6. **Comando 'm'**: Regresa al menú desde cualquier modo sin bloqueo.

**Criterio de éxito**: Lectura de presión atmosférica en rango 90–110 kPa (según altitud), sin deriva mayor a 2 kPa en 1 minuto. **Resolución mejorada** respecto a ESP32 gracias al ADC de 16 bits.

## Calibración (opcional)

El ADC del RP2040 tiene mejor linealidad que el ESP32, pero aún presenta **offset menor**. La calibración de dos puntos (GND y 3V3) mejora la precisión.

### Procedimiento rápido

1. Ejecuta **Modo 5** (Asistente de calibración).
2. Conecta GP26 a GND → presiona ENTER.
3. Conecta GP26 a 3V3(OUT) → presiona ENTER.
4. El wizard guarda `calibration.json` con los valores ADC medidos.
5. Para usar automáticamente, cambia `AUTO_USE_CALIBRATION = True` en `main.py`.

Ver [**_template/CALIBRACION.md**](../_template/CALIBRACION.md) para teoría completa.

## Visualización de datos

La práctica incluye herramienta Python para graficar presión en tiempo real:

1. **Instala dependencias** (PC):
   ```bash
   pip install -r tools/requirements.txt
   ```

2. **Ejecuta Modo 4** (CSV) en la placa.

3. **Corre el script de visualización** (PC):
   ```bash
   python tools/live_plot.py --port COM5 --baud 115200
   ```
   Reemplaza `COM5` con tu puerto.

4. **Verás una gráfica en tiempo real** de presión (kPa) vs tiempo.

Ver [**tools/README.md**](tools/README.md) para más opciones (guardar CSV, configurar ventana de tiempo, etc.).

## 🆚 Diferencias con ESP32

| Aspecto | ESP32 | RP2040 (esta práctica) |
|---------|-------|------------------------|
| **Pin ADC** | GPIO34 (ADC1_CH6) | GP26 (ADC0) |
| **Resolución** | 12 bits (0–4095) | **16 bits (0–65535)** ✅ |
| **Configuración** | `atten(11dB)`, `width(12bit)` | **No requiere** ✅ |
| **Lectura** | `adc.read()` | `adc.read_u16()` |
| **Linealidad** | ±5% error típico | **~±1% error** ✅ |
| **Conversión voltaje** | `v = raw/4095*3.3` | `v = raw/65535*3.3` |

**Ventajas RP2040**: Mayor resolución, mejor linealidad, configuración más simple.

## Limitaciones y notas

- **Resolución superior**: El RP2040 ADC de 16 bits ofrece ~16× más resolución que ESP32 (12 bits).
- **Voltaje de alimentación**: MPX5500DP especifica VS=4.75–5.25V. Con VS=3.3V la sensibilidad baja a ~66% del nominal.
- **Divisor resistivo**: Si usas VSYS (5V) para el sensor, **PROTEGE EL ADC** (máx 3.3V) con divisor 10kΩ+10kΩ.
- **Presión diferencial**: El MPX5500DP mide presión **absoluta**, no diferencial (no tiene puerto de referencia).
- **Temperatura**: Coeficiente térmico ±1% de escala completa. Para alta precisión, compensa temperatura.

## Recursos

- **Datasheet MPX5500DP**: [NXP Semiconductors](https://www.nxp.com/docs/en/data-sheet/MPX5500.pdf)
- **Documentación sensor**: [docs/MPX5500DP.md](docs/MPX5500DP.md)
- **Visualización de datos**: [docs/oscilograma.md](docs/oscilograma.md)
- **RP2040 Datasheet**: [Raspberry Pi](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf)
- **MicroPython RP2040**: [Docs oficiales](https://docs.micropython.org/en/latest/rp2/quickref.html#adc-analog-to-digital-conversion)
- **Guía de migración ESP32→RP2040**: [GUIA_MIGRACION.md](../../GUIA_MIGRACION.md)
