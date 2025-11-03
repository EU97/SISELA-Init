# Oscilograma — PWM para Servomotores (Práctica 5)

Los servos R/C esperan un tren de pulsos de ~50 Hz (periodo 20 ms). El ángulo se codifica en el ancho de pulso:

- ~1.0 ms  → cerca de 0°
- ~1.5 ms  → cerca de 90° (centro)
- ~2.0 ms  → cerca de 180°

Algunos servos aceptan rangos extendidos (p.ej. 0.5–2.4 ms), pero no es universal. Si escuchas zumbidos fuertes o el servo se fuerza al extremo, reduce el rango.

## Forma de onda esperada

```
Nivel alto:  ┌──────┐                     ┌──────────┐
				 │      │                     │          │
				 │      │                     │          │
Nivel bajo: ─┘      └─────────────────────┘          └────────
				 ↑      ↑                                 ↑
				 t=0    t=1.0–2.0 ms                      t=20 ms (periodo)
```

## Medición con osciloscopio

1. Conecta la punta del canal CH1 a la señal de servo (GPIO18) y la pinza a GND.
2. Configura base de tiempo a 2 ms/div aprox. y trigger en flanco de subida.
3. Verifica:
	- Periodo ≈ 20 ms (50 Hz).
	- Ancho alto ≈ 1.0–2.0 ms según el modo (barrido/manual).
4. Si el pulso es inestable, revisa la alimentación del servo (ruido) y la tierra común.

## Notas de alimentación

- Usa una fuente 5V capaz de suministrar el pico de corriente del servo.
- Coloca un capacitor electrolítico (470–1000 µF) cerca del servo entre 5V y GND si notas caídas.
- GND del ESP32 y de la fuente del servo deben estar unidas.
