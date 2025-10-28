# Visualización de datos — Práctica 4

Guía para capturar y graficar datos del sensor MPX5500DP en tiempo real.

## Formato CSV de salida

El **Modo 4** del programa genera datos en formato CSV por el puerto serie:

```csv
timestamp_ms,adc_raw,voltage_V,pressure_kPa
0,2048,1.650,270.00
100,2050,1.651,270.23
200,2047,1.649,269.77
...
```

### Descripción de columnas

| Columna | Tipo | Rango | Descripción |
|---------|------|-------|-------------|
| `timestamp_ms` | int | 0–∞ | Tiempo desde inicio del modo (ms) |
| `adc_raw` | int | 0–4095 | Valor ADC de 12 bits sin procesar |
| `voltage_V` | float | 0.0–3.3 | Voltaje calculado (con o sin calibración) |
| `pressure_kPa` | float | 20.0–520.0 | Presión absoluta calculada (kPa) |

## Herramientas de visualización

La carpeta `tools/` incluye script Python para graficado en tiempo real:

### 1. Instalación de dependencias

```bash
pip install -r tools/requirements.txt
```

Dependencias:
- `pyserial`: Lectura del puerto serie.
- `matplotlib`: Graficado en tiempo real.
- `numpy` (opcional): Procesamiento numérico avanzado.

### 2. Uso básico

```bash
python tools/live_plot.py --port COM5 --baud 115200
```

**Parámetros disponibles:**

| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `--port` | Puerto serie (COM5, /dev/ttyUSB0, etc.) | Autodetección |
| `--baud` | Velocidad (baudios) | 115200 |
| `--window` | Ventana de tiempo (segundos) | 30 |
| `--save` | Guardar CSV en archivo | No guarda |

**Ejemplos:**

```bash
# Autodetectar puerto, ventana de 60s
python tools/live_plot.py --window 60

# Guardar datos a archivo
python tools/live_plot.py --port COM5 --save data_presion.csv

# Puerto Linux/Mac
python tools/live_plot.py --port /dev/ttyUSB0 --baud 115200
```

### 3. Captura manual con herramientas estándar

#### Windows (PuTTY)

1. Abre PuTTY, selecciona "Serial", configura puerto y 115200 baud.
2. En **Session → Logging**, selecciona "All session output" y archivo destino.
3. Ejecuta **Modo 4** en la placa.
4. Los datos CSV se guardan en el archivo de log.
5. Abre con Excel, LibreOffice o Python Pandas.

#### Linux/Mac (screen + tee)

```bash
screen /dev/ttyUSB0 115200 | tee data.csv
```

Ejecuta **Modo 4**, presiona `Ctrl+A` luego `K` para salir.

## Análisis post-captura con Python

Una vez guardado el CSV:

```python
import pandas as pd
import matplotlib.pyplot as plt

# Leer datos
df = pd.read_csv("data_presion.csv")

# Convertir timestamp a segundos
df['time_s'] = df['timestamp_ms'] / 1000.0

# Graficar presión vs tiempo
plt.figure(figsize=(10, 6))
plt.plot(df['time_s'], df['pressure_kPa'], label='Presión (kPa)')
plt.xlabel('Tiempo (s)')
plt.ylabel('Presión (kPa)')
plt.title('MPX5500DP — Presión vs Tiempo')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# Estadísticas
print(f"Presión media: {df['pressure_kPa'].mean():.2f} kPa")
print(f"Desviación estándar: {df['pressure_kPa'].std():.2f} kPa")
print(f"Rango: {df['pressure_kPa'].min():.2f} - {df['pressure_kPa'].max():.2f} kPa")
```

## Interpretación de señales

### Presión atmosférica estable

**Señal esperada**: Línea horizontal con ruido bajo (~±1 kPa).

```
Presión (kPa)
105 ┤─────────────────────────────────
104 ┤       ╭╮  ╭╮    ╭╮
103 ┤  ╭╮ ╭╯╰╮╭╯╰╮ ╭╯╰╮
102 ┤──╯╰─╯──╰╯──╰─╯──╰─────────────
    └────────────────────────────────
     0   5   10  15  20  25  30 (s)
```

**Verificación**: Media ≈ 101 kPa (nivel del mar) ± 10 kPa según altitud.

### Cambio de presión (soplido/succión)

**Señal esperada**: Pico o valle transitorio, retorno a línea base.

```
Presión (kPa)
110 ┤         ╭─╮
108 ┤        ╭╯ ╰╮
106 ┤       ╱     ╲
104 ┤──────╯       ╰──────────────
102 ┤
100 ┤
    └────────────────────────────
     0   5   10  15  20  25  30 (s)
```

**Causa**: Soplido aumenta presión local (~+5–10 kPa), succión disminuye.

### Deriva térmica

**Señal esperada**: Tendencia lineal lenta (±1 kPa en 5 min).

```
Presión (kPa)
106 ┤                          ╱
105 ┤                      ╱─╯
104 ┤                  ╱─╯
103 ┤              ╱─╯
102 ┤──────────╱─╯
    └─────────────────────────────
     0  60  120 180 240 300 (s)
```

**Causa**: Calentamiento del sensor o ambiente. Compensar con temperatura si crítico.

### Ruido excesivo

**Señal NO deseada**: Fluctuaciones >±3 kPa sin causa física.

```
Presión (kPa)
110 ┤  ╭╮   ╭╮  ╭╮
105 ┤╭╯╰╮ ╭╯╰╮╭╯╰╮
100 ┤│  │╭╯  ╰╯  │
 95 ┤╯  ╰╯        ╰╮
 90 ┤               ╰╮
    └─────────────────
     0   5   10  15 (s)
```

**Causas posibles**:
- Cables sueltos / mal contacto.
- Fuente de alimentación ruidosa.
- ADC sin promedio de muestras.

**Solución**: Verificar conexiones, agregar condensador de filtro (0.1 µF), aumentar `ADC_SAMPLES`.

## Tasa de muestreo

**Configurado por defecto**: 10 Hz (100 ms por muestra).

**Modificar en `main.py`**:
```python
SAMPLE_RATE_MS = 50   # 20 Hz
SAMPLE_RATE_MS = 10   # 100 Hz (máximo práctico para promedio de 50 muestras)
```

**Nota**: Bajar SAMPLE_RATE_MS requiere reducir `ADC_SAMPLES` para evitar retraso acumulado.

## Troubleshooting

| Problema | Causa probable | Solución |
|----------|----------------|----------|
| "No data received" | Puerto incorrecto o placa no conectada | Verificar puerto COM y conexión USB |
| Lecturas en 0 o 4095 | Cable Vout desconectado o en corto | Revisar conexión GPIO34 ↔ MPX5500DP |
| Deriva constante | Temperatura ambiente cambiante | Esperar estabilización (5 min) o compensar |
| Ruido >5 kPa | Alimentación ruidosa o sin filtro | Agregar 0.1 µF entre VS y GND |
| CSV malformado | Datos corruptos en REPL | Ejecutar solo Modo 4 sin otros prints |

## Proyectos avanzados

### 1. Altímetro barométrico

Usa la fórmula barométrica internacional:

$$
h = \left(1 - \left(\frac{P}{P_0}\right)^{0.1903}\right) \times 44330
$$

Donde:
- $h$: Altitud (metros)
- $P$: Presión medida (Pa)
- $P_0$: Presión a nivel del mar (101325 Pa estándar)

**Implementación**:
```python
def pressure_to_altitude(p_kpa, p0_kpa=101.325):
    """Convierte presión (kPa) a altitud (m)."""
    return (1 - (p_kpa / p0_kpa) ** 0.1903) * 44330
```

### 2. Detección de cambios bruscos

Alerta cuando $|\Delta P| > umbral$ en ventana de tiempo:

```python
def detect_pressure_spike(pressures, threshold=5.0):
    """Detecta cambios mayores a threshold kPa."""
    diffs = [abs(pressures[i] - pressures[i-1]) 
             for i in range(1, len(pressures))]
    return any(d > threshold for d in diffs)
```

### 3. Compensación térmica

Mide temperatura con sensor adicional (ej: DHT22) y aplica corrección:

```python
TEMP_COEFF = 0.01  # 1% FS por grado C (típico)

def compensate_pressure(p, temp, temp_ref=25.0):
    """Compensa deriva térmica."""
    delta_t = temp - temp_ref
    return p * (1 - TEMP_COEFF * delta_t)
```

## Referencias

- **Tutorial pyserial**: https://pyserial.readthedocs.io/
- **Matplotlib Live Plotting**: https://matplotlib.org/stable/tutorials/advanced/blitting.html
- **Pandas CSV**: https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
