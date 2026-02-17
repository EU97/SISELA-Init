# P2 — Visualización de datos (ADC Potenciómetro) — RP2040

Esta práctica emite datos en formato CSV. Úsalos para verificar el correcto funcionamiento del ADC y graficar posición.

---

## CSV de salida

### Cabecera y ejemplo:
```csv
t_ms,raw,avg,voltage_v,angle_deg
0,32768,32768,1.6500,150.0
100,33000,32884,1.6580,151.5
200,33200,33000,1.6640,153.0
```

### Campos:
- **`t_ms`**: Tiempo relativo desde el arranque (milisegundos)
- **`raw`**: Lectura directa ADC (0-65535, 16-bit)
- **`avg`**: Lectura promediada (media móvil)
- **`voltage_v`**: Voltaje calculado (0-3.3V)
- **`angle_deg`**: Ángulo estimado del potenciómetro (0-300°)

---

## Diferencias vs ESP32

| Aspecto            | ESP32             | RP2040            |
|--------------------|-------------------|-------------------|
| **Rango ADC**      | 0-4095 (12-bit)   | 0-65535 (16-bit)  |
| **Función lectura**| `adc.read()`      | `adc.read_u16()`  |
| **Configuración**  | `atten()`, `width()` | No requiere     |
| **Pin ADC**        | GPIO34             | GP26 (ADC0)      |

---

## Visualización rápida

### Opción 1: Copiar CSV
1. Copia las líneas del REPL a un archivo `.csv`
2. Abre en Excel/LibreOffice
3. Grafica `t_ms` vs `voltage_v` o `angle_deg`

### Opción 2: Python (PC)
```python
import matplotlib.pyplot as plt
import csv

with open('datos_p2.csv') as f:
    reader = csv.DictReader(f)
    data = list(reader)

t = [float(r['t_ms']) for r in data]
v = [float(r['voltage_v']) for r in data]
a = [float(r['angle_deg']) for r in data]

fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
ax1.plot(t, v); ax1.set_ylabel('Voltaje (V)')
ax2.plot(t, a); ax2.set_ylabel('Ángulo (°)')
ax2.set_xlabel('Tiempo (ms)')
plt.tight_layout(); plt.show()
```

---

## Observaciones típicas

### Movimiento suave del potenciómetro
- Voltaje varía linealmente entre 0 y 3.3V
- Ángulo varía proporcionalmente entre 0° y ~300°
- Ruido ADC típico: ±20-50 cuentas (16-bit)

### Potenciómetro fijo
- Las lecturas deben ser estables (±30 cuentas)
- Si oscila mucho, verificar conexiones o aumentar ventana de media móvil
