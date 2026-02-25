# Oscilograma / Visualización de señal (P2 — ESP32)

La salida del script `main.py` es CSV con cabecera (8 columnas):

```
t_ms,raw,avg,voltage_v,angle_deg,flap_deg,ssm,arinc_hex
0,2048,2048,1.650,150.0,22.5,OK,0x6008C0B8
10,2052,2050,1.653,150.2,22.5,OK,0x6008D0B8
```

### Campos:
- **`t_ms`**: Tiempo relativo desde el arranque (milisegundos)
- **`raw`**: Lectura directa ADC (0–4095, 12-bit)
- **`avg`**: Lectura promediada (media móvil, N=8)
- **`voltage_v`**: Voltaje reconstruido (0–3.3 V)
- **`angle_deg`**: Ángulo del potenciómetro (0–300°)
- **`flap_deg`**: Posición de flaps escalada (0–45°)
- **`ssm`**: Estado del sensor: `OK` (Normal) / `FAIL` (Falla)
- **`arinc_hex`**: Trama ARINC 429 codificada en hexadecimal (32 bits)

Opciones para visualizar:

1) **Graficado en tiempo real** (recomendado)
   ```
   cd MicroPython/ESP32/P2/tools
   pip install -r requirements.txt
   python live_plot.py --port COM3 --baud 115200 --y voltage_v
   ```
   Opciones de Y: `raw`, `avg`, `voltage_v`, `angle_deg`, `flap_deg`.

2) **VS Code + Pymakr**
   - Ejecuta `main.py` (Run). Verás líneas CSV en la consola.
   - Copia/pega a un archivo `.csv` y ábrelo en tu herramienta favorita para graficar.

3) **Excel/LibreOffice**
   - Importa el archivo CSV (separador coma).
   - Grafica `t_ms` en X y `voltage_v` o `flap_deg` en Y.

4) **Python local (offline)**
   ```python
   import matplotlib.pyplot as plt
   import csv

   with open('datos_p2.csv') as f:
       reader = csv.DictReader(f)
       data = list(reader)

   t = [float(r['t_ms']) for r in data]
   v = [float(r['voltage_v']) for r in data]
   flap = [float(r['flap_deg']) for r in data]

   fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
   ax1.plot(t, v); ax1.set_ylabel('Voltaje (V)')
   ax2.plot(t, flap); ax2.set_ylabel('Flaps (°)')
   ax2.set_xlabel('Tiempo (ms)')
   plt.tight_layout()
   plt.show()
   ```

Consejos de medición:
- Evita mover cables al adquirir datos (ruido mecánico).
- Si hay mucho ruido, aumenta la ventana de media móvil `MA_WINDOW` en `main.py`.
- Para cambios más rápidos, sube `FS_HZ` (frecuencia de muestreo).
- Para verificar ARINC 429, usa la columna `arinc_hex` y decodifica manualmente a binario.
