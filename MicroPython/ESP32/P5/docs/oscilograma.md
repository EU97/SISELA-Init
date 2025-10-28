# Visualización y CSV — Práctica 5 (BMP280)

Este documento explica el formato de datos CSV emitido por el modo 5 del firmware y cómo visualizar las señales de temperatura, presión y altitud en tiempo real desde el PC.

---

## Formato CSV

Encabezado (1ª línea):

```
timestamp_ms,temp_C,press_hPa,press_kPa,altitude_m
```

- `timestamp_ms`: tiempo relativo desde que se inició el modo (milisegundos).
- `temp_C`: temperatura en °C (float con 2 decimales).
- `press_hPa`: presión en hPa (hectopascales), 1 hPa = 100 Pa.
- `press_kPa`: presión en kPa (kilopascales), 1 kPa = 1000 Pa.
- `altitude_m`: altitud estimada en metros, según fórmula barométrica con P0=101325 Pa.

Ejemplo de líneas:

```
0,25.31,1012.56,101.26,116.2
500,25.32,1012.54,101.25,116.3
1000,25.32,1012.52,101.25,116.3
```

---

## Visualización en vivo

En la carpeta `tools/` se incluye `live_plot.py`, que abre el puerto serie y grafica en tiempo real:

- Temperatura (°C)
- Presión (hPa)
- Altitud (m)

Características:

- Auto‑detección de puerto en Windows/Linux/macOS (puedes forzar con `--port COMx`).
- Ventana deslizante en segundos (`--window 60` por defecto).
- Guardado opcional de CSV en disco (`--save datos.csv`).
- Cero relativo de altitud (`--alt-zero` toma la primera muestra como referencia 0 m).

Consulta `tools/README.md` para instalación de dependencias y uso detallado.

---

## Análisis offline en Python (opcional)

Si ya guardaste un CSV, puedes analizarlo con pandas/matplotlib. Por ejemplo:

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('datos.csv')
df['t_s'] = df['timestamp_ms'] / 1000.0

fig, ax = plt.subplots(3, 1, figsize=(9, 7), sharex=True)
ax[0].plot(df['t_s'], df['temp_C'], label='Temp (°C)')
ax[0].set_ylabel('°C'); ax[0].grid(True)

ax[1].plot(df['t_s'], df['press_hPa'], label='Presión (hPa)', color='tab:orange')
ax[1].set_ylabel('hPa'); ax[1].grid(True)

ax[2].plot(df['t_s'], df['altitude_m'], label='Altitud (m)', color='tab:green')
ax[2].set_ylabel('m'); ax[2].set_xlabel('Tiempo (s)'); ax[2].grid(True)

plt.tight_layout(); plt.show()
```

---

## Consejos

- Para mejorar estabilidad de altitud, aumenta oversampling y activa filtro IIR en el sensor (ver `BMP280._configure`).
- Ajusta la presión de referencia a nivel del mar si buscas altitud absoluta precisa.
- Asegúrate de que el cable USB está en buen estado (errores de frame/ruido pueden romper el CSV).
