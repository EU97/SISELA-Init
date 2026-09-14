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

---

## Análisis de señales (modos 5–7)

Guía completa: [analisis_senales.md](analisis_senales.md).

### Modo 5 — Jitter del PWM
- CH1 → GPIO18, 1 ms/div, trigger flanco de subida ~1.5 V.
- *Measure → Pulse Width* con estadística **Min/Max/Mean/StdDev**.
- Mantén el servo en 90° (pulso ~1500 µs) y captura ≥ 1000 periodos.
- Esperado: ESP32 **σ ≈ 100 ns** (LEDC). Exporta el CSV y en la PC:
  `python -m sisela_signal characterize --scope --file scopeCH1.csv --col CH1 --mode adc`.

### Modo 6 — Muestreo y aliasing (generador → ADC)
- Generador: seno, amplitud ≤ 2 Vpp, **offset +1.65 V**, hacia GPIO34.
- El firmware muestrea a Fs y emite `t_us,counts,v`. Barre la frecuencia del generador
  por encima de Fs/2 y observa el pico de **alias** en el espectro de la PC.

### Modo 7 — Respuesta al escalón del servo-lazo
- Potenciómetro de realimentación acoplado al eje → GPIO34.
- El firmware comanda un escalón de ángulo y registra la posición durante el transitorio.
- `python -m sisela_signal characterize --file step.csv --col v --mode step`
  → tiempo de subida, sobre-oscilación, τ, ancho de banda del actuador.

### Forma de onda: PWM visto como espectro
El tren de pulsos de 50 Hz con *duty* D tiene armónicos en n·50 Hz cuya envolvente es
`sinc(n·D)`. En el osciloscopio en modo FFT (o con `sisela_signal spectrum` sobre la
captura) se ven los armónicos; su número y amplitud dependen del ancho de pulso.
