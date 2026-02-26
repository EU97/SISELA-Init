# Herramientas de visualización — Práctica 4

Scripts Python para visualizar datos del sensor BMP180 en tiempo real.

## Contenido

- `altimeter_gui.py`: Altímetro barométrico estilo aeronáutico (tkinter).
- `requirements.txt`: Dependencias Python necesarias.
- `live_plot.py`: Graficador legacy (formato anterior).

## Instalación

```bash
pip install -r requirements.txt
```

**Dependencias:**
- `pyserial`: Comunicación con puerto serie.
- `tkinter`: Interfaz gráfica (incluido con Python 3).

## Uso de altimeter_gui.py

### Sintaxis básica

```bash
python altimeter_gui.py --port COM5
```

El script **entra automáticamente al modo 4 (CSV)** del ESP32/RP2040 y muestra un altímetro tipo instrumento de avión.

### Argumentos principales

| Argumento | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `--port` | Puerto serie (COM5, /dev/ttyUSB0, etc.) | Autodetección |
| `--baud` | Velocidad en baudios | 115200 |
| `--save` | Archivo CSV para guardar datos | No guarda |
| `--unit` | Unidad de altitud (m o ft) | m |
| `--no-auto-start` | No entrar automáticamente al modo CSV | Auto ON |
| `--no-reset` | Evitar reset DTR/RTS al conectar | Reset normal |
| `--menu-choice` | Opción de menú a enviar | '4' |

### Ejemplos

**Uso más simple (recomendado):**
```bash
python altimeter_gui.py
# Autodetecta puerto, entra al modo 4, muestra altímetro
```

**Puerto específico guardando CSV:**
```bash
python altimeter_gui.py --port COM5 --save datos_vuelo.csv
```

**Modo manual (si ya iniciaste modo 4):**
```bash
python altimeter_gui.py --port COM5 --no-auto-start
```

**Linux/Mac:**
```bash
python3 altimeter_gui.py --port /dev/ttyUSB0
```

## Interfaz del altímetro

La interfaz incluye:

1. **Carátula circular** — Aguja giratoria que indica altitud (0–1000 m por revolución)
2. **Ventana de Kollsman** — Muestra presión QNH configurada
3. **Lecturas digitales** — Altitud (m/ft), presión (hPa), temperatura (°C)
4. **Slider QNH** — Ajuste de presión de referencia (980–1050 hPa)
5. **Strip chart** — Gráfica de altitud vs tiempo (últimos ~2 minutos)
6. **Botón CSV** — Iniciar/detener grabación de datos

## Flujo de uso

1. **Conecta** el ESP32/RP2040 con la Práctica 4 cargada
2. **Ejecuta** `python altimeter_gui.py --port COM5`
3. **Observa** la aguja del altímetro y las lecturas digitales
4. **Ajusta QNH** con el slider para calibrar altitud local
5. **Graba CSV** con el botón 💾 si necesitas datos para el reporte
6. **Cierra** la ventana — el programa regresa al menú del microcontrolador

## Formato CSV

```csv
timestamp_ms,temp_C,pressure_hPa,altitude_m
12345,23.4,1013.25,540.2
12545,23.4,1013.20,540.6
...
```

## Análisis post-captura

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('datos_vuelo.csv')
df['time_s'] = df['timestamp_ms'] / 1000.0

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True, figsize=(10, 8))

ax1.plot(df['time_s'], df['altitude_m'], 'g-')
ax1.set_ylabel('Altitud (m)')
ax1.grid(True)

ax2.plot(df['time_s'], df['pressure_hPa'], 'b-')
ax2.set_ylabel('Presión (hPa)')
ax2.grid(True)

ax3.plot(df['time_s'], df['temp_C'], 'r-')
ax3.set_ylabel('Temperatura (°C)')
ax3.set_xlabel('Tiempo (s)')
ax3.grid(True)

plt.tight_layout()
plt.show()
```

## Troubleshooting

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError: No module named 'serial'` | `pip install pyserial` |
| No se detecta puerto | Verifica conexión USB y drivers (CP2102/CH340) |
| ESP32 se reinicia al conectar | Usa `--no-reset` |
| Datos no aparecen | Espera ~3s para sincronización; verifica baudrate 115200 |
| Aguja no se mueve | Confirma que el modo 4 está activo (CSV) |
