# P2 — Visualización de datos (ADC + Flap + ARINC 429) — RP2040

Esta práctica emite datos en formato CSV con 8 columnas. Incluye lectura ADC,
conversión a ángulo, mapeo de posición de flap, validación SSM y palabra
ARINC 429. Usa estos datos para verificar la cadena completa de procesamiento.

---

## CSV de salida

### Cabecera y ejemplo

```csv
t_ms,raw,avg,voltage_v,angle_deg,flap_deg,ssm,arinc_hex
0,32768,32768,1.6500,150.0,15,3,0x18C56003
100,33000,32884,1.6580,151.5,15,3,0x18C5E003
200,33200,33000,1.6640,153.0,15,3,0x18C66003
```

### Campos

| #  | Campo        | Tipo   | Descripción                                      |
|----|-------------|--------|--------------------------------------------------|
| 1  | `t_ms`      | int    | Tiempo relativo desde el arranque (ms)           |
| 2  | `raw`       | int    | Lectura directa ADC (0-65535, 16-bit)            |
| 3  | `avg`       | int    | Lectura promediada (media móvil)                 |
| 4  | `voltage_v` | float  | Voltaje calculado (0-3.3 V)                      |
| 5  | `angle_deg` | float  | Ángulo del potenciómetro (0-300°)                |
| 6  | `flap_deg`  | int    | Posición de flap mapeada (0, 1, 2, 5, 10, 15, 25, 30, 40) |
| 7  | `ssm`       | int    | Sign/Status Matrix: 0 = FW, 1 = NCD, 2 = FT, 3 = NO |
| 8  | `arinc_hex` | hex    | Palabra ARINC 429 completa (32 bits, hex)        |

---

## Diferencias vs ESP32

| Aspecto            | ESP32              | RP2040             |
|--------------------|--------------------|--------------------|
| **Rango ADC**      | 0-4095 (12-bit)    | 0-65535 (16-bit)   |
| **Función lectura**| `adc.read()`       | `adc.read_u16()`   |
| **Configuración**  | `atten()`, `width()` | No requiere      |
| **Pin ADC**        | GPIO34             | GP26 (ADC0)        |

---

## Visualización en tiempo real

La herramienta `live_plot.py` (ubicada en `ESP32/P2/tools/`) funciona
igualmente con la RP2040. Conecta el puerto serie y ejecuta:

```bash
cd MicroPython/ESP32/P2/tools
pip install -r requirements.txt   # solo la primera vez
python live_plot.py --port COMX --baud 115200
```

Se abrirá una ventana con gráficas en tiempo real de voltaje, ángulo y
posición de flap.

---

## Visualización offline

### Opción 1: Excel / LibreOffice

1. Copia las líneas del REPL a un archivo `.csv`.
2. Abre en Excel o LibreOffice Calc (delimitador: coma).
3. Grafica `t_ms` vs `voltage_v`, `angle_deg` o `flap_deg`.

### Opción 2: Python (PC)

```python
import matplotlib.pyplot as plt, csv

with open('datos_p2.csv') as f:
    data = list(csv.DictReader(f))

t = [float(r['t_ms']) for r in data]
v = [float(r['voltage_v']) for r in data]
flap = [int(r['flap_deg']) for r in data]

fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
ax1.plot(t, v);    ax1.set_ylabel('Voltaje (V)')
ax2.step(t, flap); ax2.set_ylabel('Flap (°)')
ax2.set_xlabel('Tiempo (ms)')
plt.tight_layout(); plt.show()
```

---

## Verificación ARINC 429

Para confirmar que la palabra es coherente, descompón `arinc_hex`:

| Bits   | Campo   | Significado            |
|--------|---------|------------------------|
| 1-8    | Label   | Etiqueta (octal 0213)  |
| 9-10   | SDI     | Source/Dest Identifier  |
| 11-29  | Data    | Dato codificado (BNR)  |
| 30-31  | SSM     | Sign/Status Matrix     |
| 32     | Parity  | Paridad impar          |

---

## Observaciones típicas

### Movimiento suave del potenciómetro
- Voltaje varía linealmente entre 0 y 3.3 V.
- Ángulo varía proporcionalmente entre 0° y ~300°.
- `flap_deg` cambia en escalones discretos (0, 1, 2, 5 … 40).
- Ruido ADC típico: ±20-50 cuentas (16-bit).

### Potenciómetro fijo
- Las lecturas deben ser estables (±30 cuentas).
- Si `ssm` muestra 0 (Failure Warning), verificar conexiones.
- Si oscila mucho, aumentar la ventana de media móvil.
