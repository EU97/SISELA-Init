# Práctica 5 — Sensor Digital BMP280 I2C (ESP32 + MicroPython)

Lectura de sensor barométrico y de temperatura digital BMP280 mediante protocolo I2C, con compensación interna, cálculo de altitud y telemetría CSV.

## Objetivos

- Configurar comunicación I2C del ESP32 para sensores digitales.
- Implementar driver básico para BMP280 con lectura de registros y calibración.
- Aplicar algoritmos de compensación de temperatura y presión (Bosch).
- Calcular altitud usando fórmula barométrica internacional.
- Generar datos CSV para análisis y visualización.
- Comprender ventajas de sensores digitales vs analógicos (P3, P4).

## Materiales

| Cantidad | Componente | Especificación |
|----------|------------|----------------|
| 1 | ESP32 DevKit | Cualquier modelo con I2C |
| 1 | Sensor BMP280 | Bosch Sensortec, módulo breakout con regulador 3.3V |
| 2 | Resistencias pull-up | 4.7kΩ (si el módulo no las incluye) |
| n | Cables Dupont | Macho-hembra / macho-macho |

**NOTA**: La mayoría de módulos BMP280 comerciales (GY-BMP280, etc.) ya incluyen resistencias pull-up en SDA/SCL y regulador de voltaje. Verifica tu módulo específico.

## Conexiones

Ver detalle completo de pines en [**PINES.md**](PINES.md) y diagrama en [**assets/wiring.svg**](assets/wiring.svg).

**Resumen rápido:**

| Señal ESP32 | Pin | Sensor BMP280 | Descripción |
|-------------|-----|---------------|-------------|
| GPIO21 | SDA (I2C) | SDA | Datos bidireccionales |
| GPIO22 | SCL (I2C) | SCL | Reloj generado por master (ESP32) |
| 3V3 | — | VCC/VIN | Alimentación 3.3V |
| GND | — | GND | Tierra común |

**Configuración I2C:**
- **Frecuencia**: 400 kHz (Fast Mode)
- **Dirección**: 0x76 (default) o 0x77 (configurable con pin SDO)
- **Pull-ups**: 4.7kΩ en SDA/SCL (internos ESP32 + externos recomendados)

## Uso (Pymakr)

1. **Abre la carpeta de la práctica** en VS Code:
	```
	MicroPython/ESP32/P5/
	```

2. **Conecta el ESP32** y selecciona el puerto COM en Pymakr.

3. **Sincroniza y ejecuta**:
	- Botón "Sync project to device" (sube boot.py, main.py).
	- Botón "Run" o reinicia la placa (botón EN).

4. **Interacción REPL**:
	- Aparecerá el menú con 6 opciones + salida.
	- Escribe el número de modo y presiona ENTER.
	- Durante la ejecución de un modo, escribe `m` + ENTER para regresar al menú.

## Modos de operación

| Modo | Descripción | Salida típica |
|------|-------------|---------------|
| **1** | Lectura ADC cruda | `ADC_TEMP: 524288  ADC_PRESS: 328192` |
| **2** | Temperatura compensada | `Temperatura: 23.45 °C` |
| **3** | Presión compensada | `Presión: 1013.25 hPa  (101.33 kPa)` |
| **4** | Altitud estimada | `Altitud: 150.5 m  (T: 23.45°C, P: 1013.25 hPa)` |
| **5** | Monitor CSV continuo | `timestamp_ms,temp_C,press_hPa,press_kPa,altitude_m` |
| **6** | Información del sensor | Muestra calibración y configuración |
| **q** | Salir del programa | — |

### Detalles de cada modo

- **Modo 1 (ADC crudo)**: Lee valores ADC de 20 bits sin compensar. Útil para diagnóstico de hardware.

- **Modo 2 (Temperatura)**: Aplica compensación con coeficientes de calibración de fábrica. Rango: -40 a +85°C, precisión típica ±1°C.

- **Modo 3 (Presión)**: Aplica compensación con calibración. Rango: 300–1100 hPa (30–110 kPa), precisión típica ±1 hPa.

- **Modo 4 (Altitud)**: Usa fórmula barométrica internacional. Requiere presión de referencia a nivel del mar (101325 Pa por defecto). Precisión ~±1m por cada ±0.12 hPa.

- **Modo 5 (CSV)**: Imprime datos en formato `timestamp_ms,temp_C,press_hPa,press_kPa,altitude_m` cada 500 ms (2 Hz). Ideal para captura con `tools/live_plot.py`.

- **Modo 6 (Info)**: Muestra dirección I2C, chip ID y 12 coeficientes de calibración dig_T1–T3, dig_P1–P9.

## Parámetros ajustables (main.py)

```python
I2C_SCL_PIN = 22           # Pin GPIO de SCL (clock)
I2C_SDA_PIN = 21           # Pin GPIO de SDA (data)
I2C_FREQ = 400000          # Frecuencia I2C (400 kHz)

BMP280_I2C_ADDR = 0x76     # Dirección I2C (0x76 o 0x77)
SAMPLE_RATE_MS = 500       # Periodo de muestreo (ms)

ALTITUDE_REF_M = 0.0       # Altitud de referencia (m, nivel del mar)
```

**Cambiar dirección I2C**: Si tu módulo usa 0x77, cambia `BMP280_I2C_ADDR = 0x77`.

**Ajustar altitud de referencia**: Si conoces tu altitud local (ej: Ciudad de México ~2240m), configura `ALTITUDE_REF_M = 2240.0` para mejorar precisión de cálculo barométrico.

## Verificación

1. **Arranque**: Mensaje `=== Práctica 5: Sensor digital BMP280 (I2C) ===` en REPL.
2. **Detección I2C**: `[I2C] Dispositivos detectados: ['0x76']` (o '0x77').
3. **Chip ID**: `[BMP280] Detectado en dirección 0x76 (Chip ID: 0x58)`.
4. **Calibración**: `[BMP280] Calibración cargada (dig_T1=..., dig_P1=...)`.
5. **Menú funcional**: Selección 1–6 y `q` responde correctamente.
6. **Temperatura**: Lectura coherente con ambiente (~20–30°C en interiores).
7. **Presión**: Valor ~1013 hPa (nivel del mar) ±100 hPa según altitud.
8. **Altitud**: Cálculo coherente con altitud geográfica local.
9. **CSV**: Flujo continuo con formato válido, timestamp incremental.
10. **Comando 'm'**: Regresa al menú desde cualquier modo sin bloqueo.

**Criterio de éxito**: 
- Temperatura estable ±0.5°C en 1 minuto.
- Presión estable ±0.5 hPa en 1 minuto (sin cambios ambientales).
- Altitud coherente ±10m con altitud geográfica real.

## Protocolo I2C: conceptos clave

### ¿Qué es I2C?

**I2C (Inter-Integrated Circuit)** es un protocolo de comunicación serial síncrono de dos hilos:
- **SDA (Serial Data)**: Línea bidireccional de datos.
- **SCL (Serial Clock)**: Reloj generado por el maestro (ESP32).

**Características**:
- Multi-maestro, multi-esclavo (típicamente 1 maestro, múltiples esclavos).
- Direccionamiento por 7 bits (128 direcciones posibles).
- Velocidades: 100 kHz (Standard), 400 kHz (Fast), 1 MHz (Fast Plus).
- Requiere resistencias pull-up (típicamente 4.7kΩ) en SDA/SCL.

### Ventajas sobre sensores analógicos (P3/P4)

| Aspecto | Analógico (ADC) | Digital (I2C) |
|---------|-----------------|---------------|
| **Calibración** | Manual (dos puntos) | De fábrica (automática) |
| **Precisión** | ±5% (ADC ESP32) | ±1% típico |
| **Ruido** | Alto (requiere promedio) | Bajo (digital) |
| **Linealidad** | Depende de ADC/sensor | Compensada internamente |
| **Cables** | 1 señal analógica + GND/VCC | 2 señales digitales + GND/VCC |
| **Múltiples sensores** | 1 pin ADC por sensor | 1 bus I2C para todos (direcciones únicas) |

### Funcionamiento del BMP280

1. **Inicialización**: ESP32 verifica chip ID (0x58) por I2C.
2. **Calibración**: Lee 24 bytes de registros 0x88–0xA1 con coeficientes dig_T1–T3, dig_P1–P9.
3. **Configuración**: Establece oversampling (x2 temp/press) y modo normal.
4. **Lectura**: Lee 6 bytes de registros 0xF7–0xFC (ADC presión + temperatura).
5. **Compensación**: Aplica algoritmo de Bosch con coeficientes para obtener valores físicos.

## Visualización de datos

La práctica incluye herramienta Python adaptada para BMP280:

1. **Instala dependencias** (PC):
	```bash
	pip install -r tools/requirements.txt
	```

2. **Ejecuta Modo 5** (CSV) en la placa.

3. **Corre el script de visualización** (PC):
	```bash
	python tools/live_plot.py --port COM5 --baud 115200
	```

4. **Verás 3 gráficas en tiempo real**:
	- Temperatura (°C) vs tiempo
	- Presión (hPa) vs tiempo
	- Altitud (m) vs tiempo

Ver [**tools/README.md**](tools/README.md) para más opciones.

## Limitaciones y notas

- **Presión relativa**: El BMP280 mide presión absoluta. Para presión relativa (respecto a nivel del mar), aplica corrección por altitud.
- **Deriva térmica**: ±1 hPa por cada ±10°C de cambio térmico. El sensor compensa internamente.
- **Altitud QNH**: Para aviación, usa QNH local (presión ajustada a nivel del mar) en lugar de estándar (101325 Pa).
- **Pull-ups I2C**: Si el bus I2C no funciona, verifica resistencias pull-up (4.7kΩ típico). Algunos módulos las incluyen, otros no.
- **Dirección I2C**: Por defecto 0x76. Si el pin SDO está conectado a VCC, la dirección cambia a 0x77.
- **Interferencia EMI**: I2C es sensible a cables largos (>30 cm). Usa cables cortos y blindados si es necesario.

## Recursos

- **Datasheet BMP280**: [Bosch Sensortec](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf)
- **Documentación sensor**: [docs/BMP280.md](docs/BMP280.md)
- **Visualización de datos**: [docs/oscilograma.md](docs/oscilograma.md)
- **I2C Protocol**: [NXP I2C Specification](https://www.nxp.com/docs/en/user-guide/UM10204.pdf)
- **MicroPython machine.I2C**: [Docs oficiales](https://docs.micropython.org/en/latest/library/machine.I2C.html)
- **Fórmula barométrica**: [Wikipedia](https://en.wikipedia.org/wiki/Barometric_formula)

## Comparación con P4 (MPX5500DP analógico)

| Aspecto | P4 (MPX5500DP) | P5 (BMP280) |
|---------|----------------|-------------|
| **Interfaz** | ADC (analógico) | I2C (digital) |
| **Rango presión** | 20–520 kPa | 30–110 kPa |
| **Precisión** | ±5% (ADC) | ±1 hPa típico |
| **Calibración** | Opcional (dos puntos) | De fábrica (automática) |
| **Temperatura** | No incluida | Sí (-40 a +85°C) |
| **Altitud** | No calculada | Sí (fórmula barométrica) |
| **Compensación** | Lineal simple | Algoritmo complejo (Bosch) |
| **Cables** | 3 (Vout, VCC, GND) | 4 (SDA, SCL, VCC, GND) |
| **Múltiples sensores** | 1 pin ADC por sensor | 1 bus I2C compartido |

**Conclusión**: BMP280 es superior en precisión, rango y funcionalidad, pero requiere protocolo I2C. MPX5500DP es más simple (ADC directo) pero menos preciso.
