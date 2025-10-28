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
python live_plot.py --port COM5 --baud 115200 --window 30
```

### Argumentos

| Argumento | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `--port` | Puerto serie (COM5, /dev/ttyUSB0, etc.) | Autodetección |
| `--baud` | Velocidad en baudios | 115200 |
| `--window` | Ventana de tiempo (segundos) | 30 |
| `--save` | Archivo CSV para guardar datos | No guarda |

### Ejemplos

**Autodetección de puerto:**
```bash
python live_plot.py
```

**Puerto específico con ventana de 60 segundos:**
```bash
python live_plot.py --port COM5 --window 60
```

**Guardar datos a archivo:**
```bash
python live_plot.py --port COM5 --save datos_presion.csv
```

**Linux/Mac:**
```bash
python3 live_plot.py --port /dev/ttyUSB0 --baud 115200
```

## Pasos de uso completo

1. **Conecta el ESP32** con la práctica 4 cargada.

2. **Ejecuta Modo 4** en la placa (CSV monitor):
   - Abre REPL en Pymakr o terminal serie.
   - Selecciona opción `4`.

3. **Corre live_plot.py** en otra terminal (PC):
   ```bash
   python live_plot.py --port COM5 --save datos.csv
   ```

4. **Observa la gráfica** en tiempo real:
   - Gráfica superior: Presión (kPa) vs tiempo.
   - Gráfica inferior: Voltaje (V) vs tiempo.
   - Título muestra último valor medido.

5. **Detener**:
   - Presiona `Ctrl+C` o cierra la ventana de matplotlib.
   - Si usaste `--save`, el archivo CSV quedará guardado.

## Troubleshooting

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError: No module named 'serial'` | `pip install pyserial` |
| `No se pudo abrir COM5` | Verifica puerto con "Administrador de dispositivos" (Windows) o `ls /dev/tty*` (Linux/Mac) |
| `No data received` | Asegúrate de ejecutar **Modo 4** en la placa primero |
| Gráfica no actualiza | Cierra otras apps que usen el puerto (PuTTY, minicom, etc.) |
| CSV con líneas extra | Normal, script filtra headers y mensajes de debug automáticamente |

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
