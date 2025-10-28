# Motores a pasos — Guía breve

## A4988/DRV8825 (NEMA 17)

- Control STEP/DIR (pulso en STEP avanza un micro-paso en la dirección indicada por DIR).
- ENABLE activo en LOW (opcional).
- Microstepping con MS1/MS2/MS3 (A4988: 1, 1/2, 1/4, 1/8, 1/16; DRV8825 hasta 1/32).
- Ajusta la corriente del driver (potenciómetro) según el motor para evitar pérdidas y sobrecalentamiento.

Tiempo mínimo entre flancos de STEP: respeta las hojas de datos (decenas de µs típicas). En MicroPython se logra con `time.sleep_us()`.

## ULN2003 + 28BYJ-48

- Secuencia de 4 bobinas (IN1..IN4). Soporta full-step y half-step.
- 28BYJ-48 tiene caja reductora (≈64:1); pasos por vuelta efectiva ≈ 2048 (half-step).
- Alimentación a 5 V; no uses 3.3 V para el motor.

## Homing (opcional)

- Fin de carrera a GND y entrada con pull-up. Mueve en una dirección hasta activar el switch y define posición 0.

## RPM y rampas

- Un perfil trapezoidal simple (acelerar, velocidad constante, desacelerar) reduce pérdidas de pasos.
- Parámetros clave: RPM objetivo, pasos por vuelta (incluido microstepping) y aceleración (pasos/s^2).
