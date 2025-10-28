# Herramientas de visualización — P5 (BMP280)

Este directorio contiene un script para graficar en tiempo real los datos enviados por el ESP32 (modo 5: CSV).

## Instalación (Windows)

1) Abre PowerShell en esta carpeta.
2) Crea (opcional) un entorno virtual y/o instala dependencias:

```powershell
# Opción A: usar el lanzador de Python en Windows
py -m pip install -r requirements.txt

# Opción B: si el comando `python` está configurado
python -m pip install -r requirements.txt
```

## Uso básico

Conecta el ESP32, abre el modo 5 en el dispositivo y ejecuta:

```powershell
py live_plot.py
```

El script intentará detectar el puerto serie automáticamente.

## Opciones útiles

```powershell
# Elegir puerto serie explícitamente
py live_plot.py --port COM5

# Ventana de 120 s y guardar CSV
py live_plot.py --window 120 --save datos.csv

# Tomar la primera altitud como cero relativo
py live_plot.py --alt-zero
```

## Notas

- Si ves la ventana vacía, verifica que el firmware esté en Modo 5 y que
  el encabezado CSV coincida con: `timestamp_ms,temp_C,press_hPa,press_kPa,altitude_m`.
- Si hay varios dispositivos serie, indica el puerto manualmente con `--port`.
