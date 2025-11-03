# P6 — Formas de onda y mediciones (PWM con transistor)

## Qué medir

- Señal PWM en la compuerta/base del transistor (GPIO18): frecuencia y ciclo de trabajo.
- Tensión en la carga (lado bajo). Para cargas resistivas, el promedio ≈ D·V+ (D = duty). Para inductivas, notar la suavización por inercia.
- Transitorios al apagar en cargas inductivas: el diodo flyback debe limitar el sobrevoltaje.

## Parámetros de prueba sugeridos

- Frecuencia PWM: 1 kHz (ajustable en `main.py` → `PWM_FREQ`).
- Duty: 0%, 25%, 50%, 75%, 100%.
- Carga: tira LED o motor DC pequeño con fuente de 5–12 V.

## Capturas esperadas

- Gate/Base: onda cuadrada 0–3.3 V a la frecuencia seleccionada.
- Nodo de la carga (drenador/colector): tren de pulsos con nivel bajo cerca de 0 V cuando el transistor conduce. En cargas inductivas, pendiente al apagado controlada por el diodo.

## Notas

- Verifica GND común entre ESP32 y fuente externa.
- Para motores, ajustes de frecuencia pueden cambiar el ruido audible; probar 500 Hz–2 kHz.
- No alimentes la carga desde 3V3 del ESP32.
