# Práctica 7 — Control de Motores a Pasos

En esta práctica controlarás motores a pasos usando drivers A4988/DRV8825 (NEMA 17) o ULN2003 (28BYJ-48), implementando movimientos precisos, barridos y homing.

## Objetivos

- Comprender el funcionamiento de motores a pasos bipolares (NEMA) y unipolares (28BYJ-48).
- Controlar drivers A4988/DRV8825 mediante señales STEP/DIR y ULN2003 con secuencias de paso.
- Implementar modos de control: jog manual, movimiento por número de pasos, barrido con fin de carrera y homing.
- Relacionar RPM, pasos por revolución e intervalo de tiempo entre pasos.

## Material

- ESP32 DevKit (MicroPython)
- **Opción A:** Motor NEMA 17 + driver A4988 o DRV8825
- **Opción B:** Motor 28BYJ-48 + driver ULN2003
- Fuente externa para el motor (12 V típico para NEMA, 5 V para 28BYJ-48)
- Fin de carrera (microswitch) opcional para homing
- Cables y protoboard

## Conexiones (pines)

Consulta `PINES.md` para detalle completo. Resumen:

**A4988/DRV8825 (NEMA 17):**
- STEP → GPIO18
- DIR → GPIO19
- ENABLE → GPIO5 (opcional, activo en LOW)
- VMOT con fuente externa; GND común con ESP32

**ULN2003 (28BYJ-48):**
- IN1 → GPIO26
- IN2 → GPIO25
- IN3 → GPIO33
- IN4 → GPIO32
- VCC 5 V motor; GND común

**Fin de carrera (opcional):**
- ENDSTOP → GPIO4 (pull-up interno, contacto a GND)

Diagramas de cableado en `assets/wiring_*.mmd`.

## Uso

1) Edita `main.py` para seleccionar el driver:
   - `DRIVER_TYPE = "A4988"` para NEMA 17
   - `DRIVER_TYPE = "ULN2003"` para 28BYJ-48
2) Copia los archivos a la tarjeta (Pymakr o ampy). Al reiniciar verás el banner de P7.
3) En el REPL se muestra un menú con modos:
   - 1) **Jog**: presiona `+` para avanzar o `-` para retroceder paso a paso
   - 2) **Mover N pasos**: ingresa número de pasos (positivo/negativo) y RPM
   - 3) **Barrido**: avanza hasta fin de carrera (o límite fijo), retrocede, repite
   - 4) **Homing**: retrocede hasta encontrar fin de carrera, luego libera
   - 5) **Info**: muestra configuración del driver
4) En cualquier modo, presiona `m` + ENTER para volver al menú.

Parámetros por defecto:

- RPM: 60 (ajustable por modo)
- Pasos por revolución: 200 (NEMA 1/1 microstepping), 4096 (28BYJ-48 half-step)

## Verificación y medición

- Observa las señales STEP y DIR (A4988) o secuencias IN1-IN4 (ULN2003) en el osciloscopio.
- Mide el intervalo entre pulsos STEP y verifica que corresponda al RPM seleccionado.
- Documenta capturas en `docs/oscilograma.md`.
- Verifica el comportamiento del fin de carrera (homing) y el barrido.

## Seguridad y buenas prácticas

- Usa fuente externa adecuada al motor (12 V/2 A para NEMA típico, 5 V para 28BYJ-48).
- GND común obligatorio entre ESP32 y fuente del motor.
- En A4988/DRV8825, configura VREF del driver para limitar corriente al motor (evita sobrecalentamiento).
- No energices motores sin carga mecánica fija (pueden vibrar excesivamente).
- Para homing, asegura que el fin de carrera esté correctamente cableado y probado antes de activar.

## Estructura

- `boot.py`: banner de práctica.
- `main.py`: menú y modos de control (jog, mover N pasos, barrido, homing, info).
- `lib/stepper_a4988.py`: driver para A4988/DRV8825.
- `lib/stepper_uln2003.py`: driver para ULN2003 + 28BYJ-48.
- `PINES.md`: mapeo de pines y notas de cableado para ambos drivers.
- `assets/wiring_*.mmd`: diagramas Mermaid de conexiones.
- `docs/oscilograma.md`: guía de medición/registro.

> Tip: Si el motor vibra pero no gira, verifica la secuencia de pasos (ULN2003) o el cableado de las bobinas (NEMA). En A4988, asegura VREF correcto.
