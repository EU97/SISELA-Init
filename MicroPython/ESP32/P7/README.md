# Práctica P7 — MicroPython · ESP32 · Motores a pasos (Stepper)

Control de motores a pasos con ESP32 y MicroPython. Se incluyen dos configuraciones de hardware:

- A4988/DRV8825 (NEMA 17): control por STEP/DIR, microstepping opcional
- ULN2003 + 28BYJ-48: control por 4 bobinas (full-step/half-step)

## Objetivos

- Generar trenes de pulsos precisos (STEP/DIR) y secuencias de bobinas
- Implementar giros CW/CCW, movimientos por pasos y rampas de aceleración simple
- (Opcional) Homing con final de carrera y control de velocidad (RPM)

## Requisitos previos

- ESP32 con MicroPython
- Driver de potencia según motor:
	- A4988/DRV8825 + NEMA 17 (alimentación externa, GND común)
	- ULN2003 + 28BYJ-48 (5 V, GND común)

## Material y conexiones

Consulta `PINES.md` y los diagramas en `assets/` para ambas configuraciones (A4988/DRV8825 y ULN2003).

## Modos

1. Jog CW/CCW: gira continuamente a la velocidad seleccionada
2. Mover N pasos: solicita pasos y dirección, con rampa de aceleración/deceleración básica
3. Sweep de velocidades: recorre un rango de RPM para observar límites
4. Homing (opcional): usa un fin de carrera para definir referencia
5. Información/Parámetros: muestra pines, tipo de driver y microstepping

Para volver al menú: escribe `m` + ENTER.

## Archivos

- `boot.py`, `main.py`
- `lib/stepper_a4988.py`, `lib/stepper_uln2003.py`
- `PINES.md`, `assets/wiring_a4988.mmd`/`wiring_a4988.svg`, `assets/wiring_uln2003.mmd`/`wiring_uln2003.svg`
- `docs/STEPPER.md`

## Verificación

- Modo 1: sentido y velocidad acordes; ajustar RPM si hay pérdida de pasos
- Modo 2: el motor avanza exactamente N pasos (marca de referencia)
- Modo 3: identificar RPM máximas estables para tu carga
- Modo 4: homing define la referencia de forma repetible (si se cablea)

## Seguridad

- Usa fuente adecuada para el motor (no alimentes NEMA 17 desde USB)
- Comparte GND entre fuente del driver y ESP32
- Ajusta la corriente del A4988/DRV8825 según el motor para evitar sobrecalentamiento

## Recursos

- Datasheets: A4988, DRV8825, 28BYJ-48, ULN2003
- Prácticas previas para configuración de pines y temporización
