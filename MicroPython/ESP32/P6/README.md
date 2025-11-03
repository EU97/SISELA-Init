# Práctica 6 — Conmutación de potencia por PWM (transistor)

En esta práctica controlarás la potencia aplicada a una carga usando un transistor como etapa de conmutación gobernada por PWM desde el ESP32.

## Objetivos

- Comprender la conmutación de potencia con transistores (MOSFET/BJT) en configuración de bajo lado.
- Generar PWM desde el ESP32 y relacionar ciclo de trabajo con potencia media en la carga.
- Seleccionar una frecuencia PWM adecuada según el tipo de carga.
- Implementar medidas de protección (diodo flyback para cargas inductivas) y cableado correcto (GND común).

## Material

- ESP32 DevKit (MicroPython)
- MOSFET canal N de compuerta lógica (ej. AO3400, IRLZ44N) o BJT NPN equivalente
- Resistencia a compuerta/base ~220 Ω
- Diodo flyback (1N5819 o 1N4007) si la carga es inductiva (motor, rele, bobina)
- Carga: tira LED, motor DC pequeño, lámpara 12 V, etc.
- Fuente externa adecuada a la carga (5–12 V típicamente)
- Cables y protoboard
- Potenciómetro (opcional) para control analógico (GPIO34)

## Conexiones (pines)

Consulta `PINES.md` para el detalle. Resumen:

- GPIO18 → Resistencia 220 Ω → compuerta/base del transistor (PWM)
- GPIO34 (opcional) → cursor de potenciómetro (extremos a 3V3 y GND)
- GND del ESP32 y GND de la fuente externa unidos (GND común)

Diagrama de cableado en `assets/wiring.mmd` (bajo lado con MOSFET N y diodo flyback).

## Uso

1) Copia los archivos a la tarjeta (Pymakr o ampy). Al reiniciar verás el banner de P6.
2) En el REPL se muestra un menú con modos:
	- 1) Encendido/Apagado: alterna 0%/100% cada segundo para validar la etapa de potencia
	- 2) PWM manual: ingresa un porcentaje (0–100) para fijar el duty
	- 3) Barrido: duty de 0 a 100 y regreso continuo
	- 4) Potenciómetro: lee ADC (GPIO34) y mapea a duty
3) En cualquier modo, presiona `m` + ENTER para volver al menú.

Parámetros por defecto:

- PWM en GPIO18 a 1 kHz (ajustable en `main.py` → `PWM_FREQ`)
- Duty 0–100 % (se adapta a `duty_u16` o `duty` según firmware)

## Verificación y medición

- Mide la señal en la compuerta/base con el osciloscopio: PWM a la frecuencia configurada.
- Mide la tensión en la carga (lado bajo) para observar la conmutación y, en promedio, la relación con el duty.
- En cargas inductivas, verifica el diodo flyback (la forma de la tensión al apagar debe ser limitada por el diodo).
- Documenta capturas en `docs/oscilograma.md`.

## Seguridad y buenas prácticas

- No alimentes la carga desde el 3V3 del ESP32. Usa fuente externa adecuada.
- GND común entre ESP32 y la fuente externa es obligatorio.
- Para MOSFET, usa modelos de compuerta lógica; para BJT considera la corriente de base y disipación.
- Empieza con frecuencias bajas (500–1 kHz) y sube si es necesario; evita zumbidos audibles si es un motor.

## Estructura

- `boot.py`: banner de práctica.
- `main.py`: menú y modos de control PWM.
- `PINES.md`: mapeo de pines y notas de cableado.
- `assets/wiring.mmd`: diagrama Mermaid de conexiones.
- `docs/oscilograma.md`: guía de medición/registro.

> Tip: Si tu carga no responde, confirma el GND común y que el transistor sea adecuado (Vgs(th) no es Vgs@on).
