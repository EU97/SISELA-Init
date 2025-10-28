# P3 — Visualización de datos (NTC)

Esta práctica emite datos en distintos modos. Úsalos para verificar forma y estabilidad de la medida.

## CSV en modo 4

Cabecera y ejemplo:
```
t_ms,adc,v_node_v,r_ntc_ohm,t_c
12,1850,1.4920,11234.5,24.10
```
- `t_ms`: tiempo relativo desde el arranque del modo.
- `adc`: lectura promedio (12 bits típico: 0..4095).
- `v_node_v`: tensión en el nodo del divisor (V).
- `r_ntc_ohm`: resistencia estimada de la NTC (Ω).
- `t_c`: temperatura estimada (°C) con la ecuación Beta.

## Observaciones típicas

- Al calentar la NTC (dedo), la resistencia baja → `v_node_v` sube → la `t_c` calculada aumenta.
- Al dejarla enfriar, la `t_c` baja gradualmente.
- El ruido del ADC puede reducirse aumentando `SAMPLES` o usando media móvil.

## Consejos de medida

- Toma una referencia a temperatura ambiente para validar el offset del cálculo.
- Si conoces la `V_SUPPLY` real, ajústala en `main.py` para mejorar el cálculo.
- Evita cables largos o fuentes ruidosas; el ADC del ESP32 es sensible.
