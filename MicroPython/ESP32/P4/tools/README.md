# Herramientas de visualización — Práctica 4

Scripts Python para graficar datos del sensor MPX5500DP en tiempo real.

## Contenido

- `live_plot.py`: Graficador en tiempo real con matplotlib.
- `requirements.txt`: Dependencias Python necesarias.

## Instalación

```bash
pip install -r requirements.txt
```

**Dependencias:**
- `pyserial`: Comunicación con puerto serie.
- `matplotlib`: Graficado en tiempo real.
- `numpy`: Operaciones numéricas.

## Uso de live_plot.py

### Sintaxis básica

```bash
python live_plot.py --port COM5
```

Por defecto, el script **entra automáticamente al modo 4 (CSV)** del programa en el ESP32 y regresa al menú al salir.

### Argumentos principales

| Argumento | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `--port` | Puerto serie (COM5, /dev/ttyUSB0, etc.) | Autodetección |
| `--baud` | Velocidad en baudios | 115200 |
| `--window` | Ventana de tiempo (segundos) | 30 |
| `--save` | Archivo CSV para guardar datos | No guarda |
| `--no-auto-start` | Desactiva auto-inicio del modo 4 | Auto-inicio ON |
| `--no-stop-on-exit` | No regresar al menú al salir | Regresa al menú |
| `--no-reset` | Evita reset del ESP32 al abrir puerto | Reset normal |
| `--menu-choice` | Opción de menú a enviar (si cambias el número) | '4' |

### Ejemplos

**Uso más simple (recomendado):**
```bash
python live_plot.py
# Autodetecta puerto, entra al modo 4 automáticamente, y grafica
```

**Puerto específico con ventana de 60 segundos:**
```bash
python live_plot.py --port COM5 --window 60
```

**Guardar datos a archivo:**
```bash
python live_plot.py --port COM5 --save datos_presion.csv
```

**Modo manual (si ya iniciaste modo 4 en el ESP32):**
```bash
python live_plot.py --no-auto-start
```

**Linux/Mac:**
```bash
python3 live_plot.py --port /dev/ttyUSB0
```

## Pasos de uso completo

**Flujo automático (recomendado):**

1. **Conecta el ESP32** con la práctica 4 cargada.

2. **Ejecuta live_plot.py** (en PC):
   ```bash
   python live_plot.py --port COM5 --save datos.csv
   ```
   El script selecciona automáticamente el modo 4 y comienza a graficar.

3. **Observa la gráfica** en tiempo real:
   - Gráfica superior: Presión (kPa) vs tiempo.
   - Gráfica inferior: Voltaje (V) vs tiempo.
   - Título muestra último valor medido.

4. **Detener**:
   - Presiona `Ctrl+C` o cierra la ventana de matplotlib.
   - El script envía 'm' al ESP32 para regresar al menú.
   - Si usaste `--save`, el archivo CSV quedará guardado.

**Flujo manual (alternativo):**

1. Conecta el ESP32 y abre terminal/REPL (Pymakr, Thonny, etc.).
2. Selecciona opción `4` en el menú de P4.
3. En otra terminal (PC), ejecuta: `python live_plot.py --no-auto-start`

## Troubleshooting

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError: No module named 'serial'` | `pip install pyserial` |
| `No se pudo abrir COM5` | Verifica puerto con "Administrador de dispositivos" (Windows) o `ls /dev/tty*` (Linux/Mac) |
| ESP32 se reinicia al conectar | Usa `--no-reset` para evitar toggle de DTR/RTS |
| `No data received` | Espera unos segundos; el auto-inicio tarda ~3s en sincronizar |
| Gráfica no actualiza | Cierra otras apps que usen el puerto (PuTTY, minicom, Pymakr) |
| CSV con líneas extra | Normal, script filtra headers y mensajes de debug automáticamente |
| Menú aparece en ventana de plot | El script está enviando comandos; es temporal hasta que se reciba el header CSV |

## Análisis post-captura

Una vez guardado el CSV:

```python
import pandas as pd
import matplotlib.pyplot as plt

# Leer CSV
df = pd.read_csv('datos_presion.csv')

# Convertir a segundos
df['time_s'] = df['timestamp_ms'] / 1000.0

# Graficar
plt.plot(df['time_s'], df['pressure_kPa'])
plt.xlabel('Tiempo (s)')
plt.ylabel('Presión (kPa)')
plt.title('Presión vs Tiempo')
plt.grid(True)
plt.show()

# Estadísticas
print(f"Media: {df['pressure_kPa'].mean():.2f} kPa")
print(f"Desv. estándar: {df['pressure_kPa'].std():.2f} kPa")
```

## Referencias

- **Documentación pyserial**: https://pyserial.readthedocs.io/
- **Matplotlib Animation**: https://matplotlib.org/stable/api/animation_api.html
- **Pandas CSV**: https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
