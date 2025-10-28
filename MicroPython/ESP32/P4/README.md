# Práctica 4 — Sensor de Presión MPX5500DP (ESP32 + MicroPython)

Lectura analógica (ADC) de un sensor de presión piezoresistivo absoluto MPX5500DP, con conversión a kPa y salida CSV para visualización en tiempo real.

## Objetivos

- Configurar el ADC del ESP32 para leer señales analógicas de sensores.
- Implementar la conversión de voltaje a presión usando la función de transferencia del MPX5500DP.
- Aplicar calibración ADC opcional para mejorar precisión.
- Generar datos en formato CSV para graficado en tiempo real con Python.
- Desarrollar un sistema modular con menú interactivo REPL.

## Materiales

| Cantidad | Componente | Especificación |
|----------|------------|----------------|
| 1 | ESP32 DevKit | Cualquier modelo con ADC |
| 1 | Sensor MPX5500DP | Freescale/NXP, 20–520 kPa, SOT-223 |
| 1 | Resistencia | 10 kΩ (pull-down opcional para ADC) |
| 1 | Condensador | 0.1 µF cerámico (filtro de alimentación) |
| n | Cables Dupont | Macho-hembra / macho-macho |
| 1 | Fuente 5V | USB o externa regulada (recomendado) |

**NOTA IMPORTANTE**: El MPX5500DP funciona óptimamente con **VS = 4.75–5.25V**. Con VS=3.3V la sensibilidad disminuye pero el sensor sigue operativo. Para máxima precisión, alimenta el sensor con 5V y usa un divisor resistivo (10kΩ + 10kΩ) o buffer operacional para el ADC.

## Conexiones

Ver detalle completo de pines en [**PINES.md**](PINES.md) y diagrama en [**assets/wiring.svg**](assets/wiring.svg).

**Resumen rápido:**

| Señal ESP32 | Pin | Sensor MPX5500DP | Descripción |
|-------------|-----|------------------|-------------|
| GPIO34 | ADC1_CH6 | Vout (pin 3) | Salida analógica del sensor |
| 3V3 | — | VS (pin 2) | Alimentación del sensor (ver nota) |
| GND | — | GND (pin 1) | Tierra común |

**Configuración ADC:**
- 12 bits (0–4095)
- Atenuación 11dB (rango 0–3.3V)
- Promedio de 50 muestras para reducir ruido

## Uso (Pymakr)

1. **Abre la carpeta de la práctica** en VS Code:
   ```
   MicroPython/ESP32/P4/
   ```

2. **Conecta el ESP32** y selecciona el puerto COM en Pymakr.

3. **Sincroniza y ejecuta**:
   - Botón "Sync project to device" (sube boot.py, main.py).
   - Botón "Run" o reinicia la placa (botón EN).

4. **Interacción REPL**:
   - Aparecerá el menú con 5 opciones + salida.
   - Escribe el número de modo y presiona ENTER.
   - Durante la ejecución de un modo, escribe `m` + ENTER para regresar al menú.

## Modos de operación

| Modo | Descripción | Salida típica |
|------|-------------|---------------|
| **1** | Lectura ADC cruda | `ADC: 2048` (valor 0–4095) |
| **2** | Voltaje del sensor | `Voltaje: 1.65 V  (ADC: 2048)` |
| **3** | Presión en kPa | `Presión: 270.00 kPa  (V: 1.65, ADC: 2048)` |
| **4** | Monitor CSV continuo | `timestamp_ms,adc_raw,voltage_V,pressure_kPa` |
| **5** | Asistente de calibración ADC | Wizard interactivo (opcional) |
| **q** | Salir del programa | — |

### Detalles de cada modo

- **Modo 1 (ADC crudo)**: Lee el valor digital del ADC (0–4095) con promedio de 50 muestras. Útil para diagnóstico de ruido.

- **Modo 2 (Voltaje)**: Convierte ADC a voltaje (0–3.3V). Si calibración está activa, aplica corrección lineal.

- **Modo 3 (Presión kPa)**: Usa la función de transferencia del MPX5500DP para convertir voltaje a presión absoluta. Rango: 20–520 kPa.

- **Modo 4 (CSV)**: Imprime datos en formato `timestamp_ms,adc_raw,voltage_V,pressure_kPa` cada 100 ms (10 Hz). Ideal para capturar con `tools/live_plot.py` desde PC.

- **Modo 5 (Calibración)**: Wizard interactivo que mide ADC en GND y 3V3, guarda `calibration.json`. Ver sección [Calibración](#calibración-opcional).

## Parámetros ajustables (main.py)

```python
ADC_PIN = 34               # Pin GPIO del ADC
ADC_SAMPLES = 50           # Número de muestras para promedio
SAMPLE_RATE_MS = 100       # Periodo de muestreo (ms)

V_SUPPLY = 3.3             # Voltaje de alimentación del sensor (V)
P_MIN = 20.0               # Presión mínima del sensor (kPa)
P_MAX = 520.0              # Presión máxima del sensor (kPa)

AUTO_USE_CALIBRATION = False  # Activar calibración automática
```

## Verificación

1. **Arranque**: Mensaje `=== Práctica 4: Sensor de presión MPX5500DP ===` en REPL.
2. **Menú funcional**: Selección 1–5 y `q` responde correctamente.
3. **Modo ADC**: Valor estable (~2000–2500 ADC al aire libre, depende de presión atmosférica local).
4. **Modo presión**: Lectura ~101 kPa (presión atmosférica estándar a nivel del mar). Variación ±10 kPa según altitud.
5. **Modo CSV**: Flujo continuo de líneas con formato correcto, timestamp incremental.
6. **Comando 'm'**: Regresa al menú desde cualquier modo sin bloqueo.

**Criterio de éxito**: Lectura de presión atmosférica en rango 90–110 kPa (según altitud), sin deriva mayor a 2 kPa en 1 minuto.

## Calibración (opcional)

El ADC del ESP32 tiene **offset y no linealidad** inherentes. La calibración de dos puntos (GND y 3V3) mejora offset/ganancia pero NO corrige completamente la curva no lineal.

### Procedimiento rápido

1. Ejecuta **Modo 5** (Asistente de calibración).
2. Conecta GPIO34 a GND → presiona ENTER.
3. Conecta GPIO34 a 3V3 → presiona ENTER.
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

## Limitaciones y notas

- **No linealidad ADC**: El ESP32 ADC tiene ±5% de error. Calibración mejora pero no elimina curva.
- **Voltaje de alimentación**: MPX5500DP especifica VS=4.75–5.25V. Con VS=3.3V la sensibilidad baja a ~66% del nominal.
- **Divisor resistivo**: Si usas 5V para el sensor, **PROTEGE EL ADC** (máx 3.3V) con divisor 10kΩ+10kΩ o buffer.
- **Presión diferencial**: El MPX5500DP mide presión **absoluta**, no diferencial (no tiene puerto de referencia).
- **Temperatura**: Coeficiente térmico ±1% de escala completa. Para alta precisión, compensa temperatura.

## Recursos

- **Datasheet MPX5500DP**: [NXP Semiconductors](https://www.nxp.com/docs/en/data-sheet/MPX5500.pdf)
- **Documentación sensor**: [docs/MPX5500DP.md](docs/MPX5500DP.md)
- **Visualización de datos**: [docs/oscilograma.md](docs/oscilograma.md)
- **ESP32 ADC Guide**: [Espressif Docs](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/adc.html)
- **MicroPython machine.ADC**: [Docs oficiales](https://docs.micropython.org/en/latest/library/machine.ADC.html)