# Calibración (opcional) — Plantilla ESP32 + MicroPython

Esta guía describe cómo añadir una calibración básica para mediciones por ADC. El objetivo es corregir offset/ganancia mapeando el rango `[low..high]` del ADC a `[0..Vref]` (p. ej., `0..3.3V`). No corrige la no linealidad intrínseca del ADC del ESP32.

## Flujo propuesto (wizard por REPL)

1) Conectar el nodo analógico a GND y confirmar en el REPL (escribir `ok` + ENTER): medir `low`.
2) Conectar el nodo a 3V3 y confirmar (escribir `ok` + ENTER): medir `high`.
3) Guardar `calibration.json` en la placa con los valores medidos.
4) Mantener deshabilitada por defecto la aplicación de la calibración; habilitarla manualmente con una bandera en `main.py`.

## Bandera y archivo

- Bandera sugerida en `main.py`:
  - `AUTO_USE_CALIBRATION = False` (por defecto)
  - `CAL_FILE = "calibration.json"`
- Archivo JSON (en la raíz del proyecto en la placa):
```json
{
  "low": 123,         // promedio de lecturas con el nodo a GND
  "high": 3987,       // promedio de lecturas con el nodo a 3V3
  "enabled": true     // marca que los datos son válidos
}
```

## Conversión adc → voltaje (con calibración)

Pseudocódigo:
```python
# adc_val: lectura promedio (entero)
# Vref: voltaje de referencia (p. ej., 3.3)
# cal: dict con {"low": int, "high": int, "enabled": bool}

def adc_to_voltage(adc_val, Vref, cal=None, width_bits=12):
    if cal and cal.get("enabled") and cal.get("high", 0) > cal.get("low", 0):
        low = float(cal["low"])
        high = float(cal["high"])
        span = high - low
        ratio = (adc_val - low) / span
        ratio = 0.0 if ratio < 0 else (1.0 if ratio > 1 else ratio)
        return ratio * Vref
    # Mapeo estándar sin calibración
    maxcount = (1 << width_bits) - 1
    return (adc_val / maxcount) * Vref
```

## Wizard de calibración (pseudocódigo)

```python
import sys
try:
    import uselect
except ImportError:
    uselect = None

NS = 64  # número de muestras para promediar

def poll_stdin():
    if not uselect:
        return None
    p = uselect.poll()
    try:
        p.register(sys.stdin, uselect.POLLIN)
    except Exception:
        return None
    return p

def readline_timeout(ms, p=None):
    if not uselect:
        return None
    p = p or poll_stdin()
    if not p:
        return None
    if p.poll(ms):
        try:
            return sys.stdin.readline().strip()
        except Exception:
            return None
    return None

# 1) GND
print("Une el nodo a GND y escribe 'ok' + ENTER")
p = poll_stdin()
while True:
    if (readline_timeout(200, p) or '').lower() in ('ok', 'ok.'):
        break
low = 0
for _ in range(NS):
    low += adc.read()  # o adc_read_avg()
low //= NS

# 2) 3V3
print("Une el nodo a 3V3 y escribe 'ok' + ENTER")
while True:
    if (readline_timeout(200, p) or '').lower() in ('ok', 'ok.'):
        break
high = 0
for _ in range(NS):
    high += adc.read()
high //= NS

if high <= low:
    print("Valores inválidos; repite la calibración.")
else:
    cal = {"low": int(low), "high": int(high), "enabled": True}
    # persistir cal con json/ujson: open(CAL_FILE, 'w').write(json.dumps(cal))
    print("Calibración medida: low={}, high={}".format(low, high))
```

## Recomendaciones

- Incrementa `NS` (muestras) si observas ruido excesivo.
- Usa cables cortos y fuente estable; desconecta cargas que metan ruido.
- Repite la calibración si cambias la topología (divisor), el pin o el rango de tensión.
- Documenta en el README cómo activar des/activar esta calibración y su alcance.

## Limitaciones y alternativas

- La corrección es lineal (offset/ganancia). La no linealidad del ADC del ESP32 permanece.
- Para mayor precisión, considera una tabla de puntos intermedios o una curva de corrección empírica, o usa un ADC externo calibrado.
