# Práctica 8 — Sistema Integrado (RP2040)

> Integración de sensores analógicos, superficies de control (servos), propulsión PWM y tren de aterrizaje con motor a pasos en RP2040 (MicroPython).

## 🧩 Componentes del sistema

- Sensores analógicos (3 externos + 1 interno TEMP) con `lib/sensors.py`
- Superficies de control (servos a 50 Hz) con `lib/flight_controls.py`
- Propulsión (PWM + MOSFET) con `lib/propulsion.py`
- Tren de aterrizaje (stepper A4988 o ULN2003) con `lib/landing_gear.py`

## 📌 Pines (RP2040)

Consulta `PINES.md` para el detalle completo. Configuración por defecto:

- Sensores ADC: GP26 (altitude), GP27 (speed), GP28 (attitude), TEMP interna (light)
- Servos: GP14 (aileron), GP15 (elevator)
- Motor PWM: GP13
- Stepper A4988: GP18 (STEP), GP19 (DIR), GP5 (EN), Endstop GP4

Nota: La opción ULN2003 usa GP26–GP28 y entra en conflicto con ADC; si eliges ULN2003, remapea sensores.

## ▶️ Ejecución

1) Copia esta carpeta al RP2040 (o usa Pymakr/rshell/Thonny):
- `boot.py` (banner)
- `main.py`
- `lib/` (módulos y drivers de stepper)

2) Conecta el hardware según `PINES.md` y fuentes externas (servos/motores).

3) Reinicia el RP2040. Verás el banner y el menú interactivo:
- [1] Panel de instrumentos (telemetría en tiempo real)
- [2] Control manual de superficies (servos)
- [3] Control de potencia (PWM)
- [4] Tren de aterrizaje (stepper + endstop)
- [5] Piloto automático simple
- [6] Diagnóstico del sistema
- [7] Configuración

## 🔧 Ajustes rápidos

- Cambia el driver del tren: `STEPPER_DRIVER = "A4988"` o `"ULN2003"` en `main.py`.
- Edita pines en `main.py` y `PINES.md` si tu cableado es distinto.
- Ajusta escalas físicas de sensores en `lib/sensors.py` (diccionario `scales`).

## ⚠️ Recomendaciones y seguridad

- Usa fuente de 5 V externa para servos y de 12 V (típico) para NEMA 17.
- GND común entre RP2040 y todas las fuentes externas.
- Diodo flyback para cargas inductivas.
- El endstop usa `Pin.PULL_UP` y se activa a nivel bajo (cierre a GND).

## ✅ Verificación

Ejecuta el diagnóstico ([6] en el menú):
- Lecturas de sensores dentro de rango (no pegadas al 0%/100%).
- Barrido correcto de servos.
- Rampa PWM 0% → 50% → 0%.
- Estado del tren y del endstop reportados correctamente.

## 📚 Notas de portabilidad

- ADC RP2040 opera a 16 bits (`read_u16`); se adaptó el escalado.
- Stepper A4988: driver actualizado para evitar conflicto de nombres (`step_pin`).
- `uselect` y `machine` se resuelven en el entorno MicroPython del RP2040; los avisos del editor en PC son normales.
