# Visualización de datos — Práctica 4 (RP2040)

Guía para capturar y graficar datos del sensor MPX5500DP en tiempo real con **Raspberry Pi Pico (RP2040)**.

## 🔄 Diferencias con ESP32

| Aspecto | ESP32 | RP2040 (esta práctica) |
|---------|-------|------------------------|
| **Valor ADC** | 0–4095 (12 bits) | **0–65535 (16 bits)** ✅ |
| **Resolución presión** | ~0.12 kPa/bit | **~0.0076 kPa/bit** (16× mejor) |
| **Ruido típico ADC** | ±10 LSB | **±2 LSB** (mejor linealidad) |

## Formato CSV de salida

El **Modo 4** del programa genera datos en formato CSV por el puerto serie:

```csv
timestamp_ms,adc_raw,voltage_V,pressure_kPa
0,32768,1.650,270.00
100,32790,1.651,270.23
200,32746,1.649,269.77
...
```

### Descripción de columnas

| Columna | Tipo | Rango | Descripción |
|---------|------|-------|-------------|
| `timestamp_ms` | int | 0–∞ | Tiempo desde inicio del modo (ms) |
| `adc_raw` | int | **0–65535** | Valor ADC de **16 bits** sin procesar |
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
python tools/live_plot.py --port COM5 --save data_presion_rp2040.csv

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
screen /dev/ttyUSB0 115200 | tee data_rp2040.csv
```

Ejecuta **Modo 4**, presiona `Ctrl+A` luego `K` para salir.

## Análisis post-captura con Python

Una vez guardado el CSV:

```python
import pandas as pd
import matplotlib.pyplot as plt

# Leer datos
df = pd.read_csv("data_presion_rp2040.csv")

# Convertir timestamp a segundos
df['time_s'] = df['timestamp_ms'] / 1000.0

# Graficar presión vs tiempo
plt.figure(figsize=(10, 6))
plt.plot(df['time_s'], df['pressure_kPa'], label='Presión (kPa) - RP2040', linewidth=0.8)
plt.xlabel('Tiempo (s)')
plt.ylabel('Presión (kPa)')
plt.title('MPX5500DP + RP2040 — Presión vs Tiempo (16-bit ADC)')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()

# Estadísticas
print(f"Presión media: {df['pressure_kPa'].mean():.2f} kPa")
print(f"Desviación estándar: {df['pressure_kPa'].std():.3f} kPa")  # Menor que ESP32
print(f"Rango: {df['pressure_kPa'].min():.2f} - {df['pressure_kPa'].max():.2f} kPa")
print(f"Resolución ADC: {3.3 / 65535:.6f} V/bit")  # 50.35 µV/bit
```

## Interpretación de señales

### Presión atmosférica estable

**Señal esperada**: Línea horizontal con ruido **MUY bajo** (~±0.3 kPa) gracias al ADC de 16 bits.

```
Presión (kPa)
103.0 ┤─────────────────────────────────
102.5 ┤       ╭╮  ╭╮    ╭╮
102.0 ┤  ╭╮ ╭╯╰╮╭╯╰╮ ╭╯╰╮
101.5 ┤──╯╰─╯──╰╯──╰─╯──╰─────────────
    └────────────────────────────────
     0   5   10  15  20  25  30 (s)
```

**Verificación**: Media ≈ 101 kPa (nivel del mar) ± 10 kPa según altitud.  
**Ventaja RP2040**: Ruido ~3× menor que ESP32 (mejor linealidad ADC).

### Cambio de presión (soplido/succión)

**Señal esperada**: Pico o valle transitorio, retorno a línea base **más suave**.

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
**Observación**: Curva más definida que ESP32 (16 bits captura transitorios mejor).

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
**Detección mejorada**: El RP2040 permite detectar deriva más pequeña (~0.1 kPa).

### Ruido excesivo

**Señal NO deseada**: Fluctuaciones >±2 kPa sin causa física (raro en RP2040).

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
- Sensor sin condensador de filtro.

**Solución**: Verificar conexiones, agregar condensador de filtro (0.1 µF), aumentar `ADC_SAMPLES`.  
**Nota**: El RP2040 requiere **menos promediado** que ESP32 para misma SNR.

## Comparativa de ruido: ESP32 vs RP2040

```python
# Análisis estadístico de 1000 muestras en reposo

# ESP32 (12 bits)
# ADC: σ ≈ 10 LSB → ~8 mV → ~1.0 kPa ruido RMS

# RP2040 (16 bits)  
# ADC: σ ≈ 2 LSB → ~0.1 mV → ~0.13 kPa ruido RMS  ✅ 8× mejor

print("Resolución efectiva:")
print(f"ESP32:  {3.3 / 4095:.4f} V/bit = {0.806:.3f} mV/bit")
print(f"RP2040: {3.3 / 65535:.4f} V/bit = {0.050:.3f} mV/bit")  # 16× mejor
```

## Tasa de muestreo

**Configurado por defecto**: 10 Hz (100 ms por muestra).

**Modificar en `main.py`**:
```python
SAMPLE_RATE_MS = 50   # 20 Hz
SAMPLE_RATE_MS = 10   # 100 Hz (RP2040 puede manejar sin problema)
SAMPLE_RATE_MS = 1    # 1 kHz (para análisis espectral)
```

**Ventaja RP2040**: Puede muestrear más rápido sin degradar SNR (ADC más lineal).  
**Nota**: Bajar SAMPLE_RATE_MS requiere reducir `ADC_SAMPLES` para evitar retraso acumulado.

## Troubleshooting

| Problema | Causa probable | Solución |
|----------|----------------|----------|
| "No data received" | Puerto incorrecto o placa no conectada | Verificar puerto COM y conexión USB |
| Lecturas en 0 o 65535 | Cable Vout desconectado o en corto | Revisar conexión GP26 ↔ MPX5500DP |
| Deriva constante | Temperatura ambiente cambiante | Esperar estabilización (5 min) o compensar |
| Ruido >2 kPa | Alimentación ruidosa o sin filtro | Agregar 0.1 µF entre VS y GND |
| CSV malformado | Datos corruptos en REPL | Ejecutar solo Modo 4 sin otros prints |

## Proyectos avanzados

### 1. Altímetro barométrico de alta precisión

Usa la fórmula barométrica internacional con **16 bits de resolución**:

$$
h = \left(1 - \left(\frac{P}{P_0}\right)^{0.1903}\right) \times 44330
$$

Donde:
- $h$: Altitud (metros)
- $P$: Presión medida (Pa)
- $P_0$: Presión a nivel del mar (101325 Pa estándar)

**Implementación optimizada para RP2040**:
```python
def pressure_to_altitude(p_kpa, p0_kpa=101.325):
    """Convierte presión (kPa) a altitud (m).
    
    RP2040 16-bit ADC permite resolución ~0.1m vertical.
    """
    return (1 - (p_kpa / p0_kpa) ** 0.1903) * 44330

# Ejemplo: RP2040 detecta cambio de 1 metro
# Δh = 1m → ΔP ≈ 0.012 kPa (detectable con 16 bits)
```

### 2. Detección de cambios bruscos con mayor sensibilidad

Alerta cuando $|\Delta P| > umbral$ en ventana de tiempo:

```python
def detect_pressure_spike(pressures, threshold=2.0):  # RP2040: umbral más bajo
    """Detecta cambios mayores a threshold kPa.
    
    RP2040 permite umbral 2× más sensible que ESP32.
    """
    diffs = [abs(pressures[i] - pressures[i-1]) 
             for i in range(1, len(pressures))]
    return any(d > threshold for d in diffs)
```

### 3. Compensación térmica

Mide temperatura con sensor adicional (ej: DHT22) y aplica corrección:

```python
TEMP_COEFF = 0.01  # 1% FS por grado C (típico)

def compensate_pressure(p, temp, temp_ref=25.0):
    """Compensa deriva térmica.
    
    RP2040 ADC más estable permite detectar deriva < 0.5%
    """
    delta_t = temp - temp_ref
    return p * (1 - TEMP_COEFF * delta_t)
```

### 4. Análisis de frecuencias (FFT)

**Solo posible con RP2040** a alta tasa de muestreo (>100 Hz):

```python
import numpy as np
from scipy.fft import fft, fftfreq

# Captura 1000 muestras a 200 Hz
fs = 200  # Hz
pressures = [...]  # Datos de Modo 4

# FFT para detectar vibraciones periódicas
yf = fft(pressures)
xf = fftfreq(len(pressures), 1/fs)

plt.plot(xf[:len(xf)//2], np.abs(yf[:len(yf)//2]))
plt.xlabel('Frecuencia (Hz)')
plt.ylabel('Amplitud')
plt.title('Espectro de presión — RP2040 16-bit')
plt.show()
```

## Ventajas del RP2040 para aplicaciones exigentes

| Aplicación | ESP32 (12-bit) | RP2040 (16-bit) | Mejora |
|------------|----------------|-----------------|--------|
| **Altimetría** | ±5m resolución vertical | **±0.3m resolución** | 16× |
| **Monitoreo respiración** | Señal ruidosa (~1 kPa pico) | **Señal limpia (~0.15 kPa ruido)** | 7× |
| **Control neumático** | Requiere filtrado pesado | **Filtrado ligero suficiente** | — |
| **Muestreo rápido** | <50 Hz práctico | **>500 Hz sin degradación** | 10× |

## Referencias

- **Tutorial pyserial**: https://pyserial.readthedocs.io/
- **Matplotlib Live Plotting**: https://matplotlib.org/stable/tutorials/advanced/blitting.html
- **Pandas CSV**: https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
- **RP2040 ADC Guide**: https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf (Sección 4.9)
- **Scipy FFT**: https://docs.scipy.org/doc/scipy/reference/tutorial/fft.html
