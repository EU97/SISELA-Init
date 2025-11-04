# Oscilogramas — Práctica 8 (RP2040)

Este documento resume las señales clave a medir con osciloscopio o analizador lógico: servos (PWM 50 Hz), potencia (PWM kHz) y motor a pasos (STEP/DIR o secuencia ULN2003).

## Servo PWM (50 Hz)

- Periodo: 20 ms (50 Hz)
- Ancho de pulso:
  - 0° ≈ 1000 µs
  - 90° ≈ 1500 µs
  - 180° ≈ 2000 µs
- Señal medida en GP14 (Alerón) y GP15 (Elevador)

Relación ángulo → pulso:

$\text{pulse}_\mu s = 1000 + (\frac{\text{ángulo}}{180})\times 1000$

Y conversión a duty_u16 de RP2040 (0–65535) a 50 Hz:

$\text{duty}_{u16} = \left(\frac{\text{pulse}_\mu s}{20000}\right) \times 65535$

Espera observar tren de pulsos estable de 20 ms, variando el ancho conforme cambia el ángulo.

## PWM de potencia (motor)

- Frecuencia por defecto: 1 kHz
- Duty: 0–100 %
- Señal medida en GP13 (gate del MOSFET)

Conversión:

$\text{duty}_{u16} = \left(\frac{\text{\%}}{100}\right) \times 65535$

Recomendaciones:
- Con carga inductiva, mide también el drenaje y verifica el diodo flyback.
- Evita saturar el MOSFET con gate inadecuado; preferir MOSFET logic-level.

## STEP/DIR (A4988)

- `STEP` en GP18, `DIR` en GP19, `EN` en GP5 (LOW activo)
- Ancho mínimo de pulso `STEP`: > 1 µs (usamos 5 µs)
- Intervalo entre pasos: depende de RPM objetivo

Relación RPM ↔ intervalo de pasos (pasos/rev = 200):

$\text{SPS} = \frac{\text{RPM} \times 200}{60}$  ,  $T_{step} = \frac{1}{\text{SPS}}$  ,  $T_{step,\mu s} = T_{step} \times 10^6$

Ejemplo: 30 RPM → SPS ≈ 1000 → $T_{step}$ ≈ 1 ms → 1000 µs entre flancos de `STEP`.

Oscilograma esperado:
- Señal `STEP` periódica con pulsos de ~5 µs y periodo ≈ intervalo calculado.
- `DIR` constante durante un movimiento; cambia sólo al invertir.
- `EN` en LOW durante el movimiento; HIGH para desactivar.

## Secuencia ULN2003 (28BYJ-48)

- Entradas en GP26–GP28 y GP22
- Modo half-step por defecto (8 estados), delay típico 3 ms/estado

Secuencia de 8 pasos (representación conceptual):

```
1: 1000
2: 1100
3: 0100
4: 0110
5: 0010
6: 0011
7: 0001
8: 1001
```

Oscilograma esperado:
- En cada INx, señal tipo cuadrada con duty bajo (activación por fase)
- Periodo por paso ≈ delay configurado (p. ej. 3 ms) × número de estados

## Notas de medición

- Usa GND común entre instrumento y circuito.
- Para servos, evita medir en la línea de alimentación de 5 V (ruido y picos). Mide la línea de señal.
- En motores, cuida la disipación del MOSFET y revisa la forma de onda en el drenaje para confirmar que el diodo está en sentido correcto.
