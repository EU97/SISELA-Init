# Oscilograma / Visualización de señal (P2)

La salida del script `main.py` es CSV con cabecera:

```
t_ms,raw,avg,voltage_v,angle_deg
12,2050,2048,1.650,150.0
...
```

Opciones para visualizar:

1) VS Code + Pymakr
- Ejecuta `main.py` (Run). Verás líneas CSV en la consola.
- Copia/pega a un archivo `.csv` y ábrelo en tu herramienta favorita para graficar.

2) Excel/LibreOffice
- Importa el archivo CSV (separador coma).
- Grafica `t_ms` en X y `voltage_v` o `angle_deg` en Y.

3) Python local (opcional)
- Puedes usar Matplotlib en tu PC para graficar el CSV exportado.

Consejos de medición:
- Evita mover cables al adquirir datos (ruido mecánico).
- Si hay mucho ruido, aumenta la ventana de media móvil `MA_WINDOW` en `main.py`.
- Para cambios más rápidos, sube `FS_HZ` (frecuencia de muestreo).
