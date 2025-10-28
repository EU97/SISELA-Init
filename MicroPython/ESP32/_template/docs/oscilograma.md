# Visualización de datos (oscilograma) — Plantilla

Si tu práctica emite CSV, usa este esquema para graficar rápidamente.

## Formato recomendado (ejemplo)
```
t_ms,field1,field2
12,123,456
...
```
- Cabecera con nombres de columnas.
- Separador coma.

## Opciones de visualización

1) Consola + CSV manual
- Copia la salida de la consola a `datos.csv` y ábrelo en Excel/LibreOffice.

2) Python en PC
- Crea un script en `tools/` (p. ej., `live_plot.py`) que lea del puerto serie (pyserial) o de un CSV y grafique con Matplotlib.
- Añade `requirements.txt` en `tools/` para facilitar instalación.

## Consejos
- Evita saturar la consola: imprime cada N iteraciones si no necesitas cada muestra.
- Para señales ruidosas, usa media móvil o filtros sencillos.
- Documenta claramente el significado de cada columna.
