# Práctica 5 — Control PWM para Servomotores (ESP32 + MicroPython)

Control de servomotores R/C (SG90, MG90S, MG996R, etc.) mediante PWM de 50 Hz. Incluye barrido, control manual por ángulo, prueba de pulso directo (us) y control con potenciómetro.

## Objetivos

- Configurar PWM a 50 Hz en el ESP32 para control de servos.
- Relacionar ancho de pulso (us) con ángulo (°) y realizar calibración básica.
- Implementar un menú interactivo con 4 modos prácticos.
- Documentar conexiones y precauciones de alimentación de servos.

## Materiales

| Cantidad | Componente | Especificación |
|----------|------------|----------------|
| 1 | ESP32 DevKit | Cualquier modelo con PWM en GPIO18 (recomendado) |
| 1 | Servomotor | SG90/MG90S/MG996R u otro R/C estándar |
| 1 | Fuente 5V | 1–2 A según el servo (NO usar 3V3 del ESP32) |
| 1 | Potenciómetro (opcional) | 10 kΩ para control analógico |
| n | Cables Dupont | Macho-hembra / macho-macho |

> Seguridad: Alimenta el servo desde 5V externo capaz de dar corriente suficiente. Conecta GND del servo y GND del ESP32 en común. No alimentes el servo desde el pin 3V3 del ESP32.

## Conexiones

Ver detalle de pines en [**PINES.md**](PINES.md) y diagrama en [**assets/wiring.svg**](assets/wiring.svg).

Resumen rápido:

| Señal ESP32 | Pin | Servomotor | Descripción |
|-------------|-----|------------|-------------|
| GPIO18 | PWM | Señal (amarillo/blanco) | Control a 50 Hz |
| 5V | — | VCC (rojo) | Alimentación del servo |
| GND | — | GND (negro/marrón) | Tierra común con ESP32 |
| GPIO34 (opcional) | ADC | Cursor potenciómetro | Control analógico de ángulo |

## Uso (Pymakr)

1. Abre la carpeta:
   ```
   MicroPython/ESP32/P5/
   ```
2. Conecta el ESP32 y selecciona el puerto COM en Pymakr.
3. Sincroniza y ejecuta:
   - "Sync project to device" (sube boot.py, main.py, lib/servo.py).
   - "Run" o reinicia la placa.
4. Interacción:
   - Aparece un menú con 4 modos.
   - Durante cualquier modo, escribe `m` + ENTER para volver al menú.

## Modos de operación

| Modo | Descripción | Salida típica |
|------|-------------|---------------|
| 1 | Barrido 0–180–0 | Mensajes de avance opcionales |
| 2 | Ángulo manual (0–180) | `Ángulo→ 90°  (pulso ~1500us)` |
| 3 | Pulso directo (us) | `Pulso→ 1800us` |
| 4 | Control por potenciómetro | `ADC=1234 →  87°` |
| q | Salir | — |

### Parámetros ajustables (main.py)

```python
SERVO_PIN = 18
SERVO_FREQ = 50              # Hz (20 ms)
SERVO_MIN_US = 500           # us (≈ 0°)
SERVO_MAX_US = 2400          # us (≈ 180°)
ANGLE_MIN = 0
ANGLE_MAX = 180

ADC_PIN = 34                 # opcional, potenciómetro
```

> Nota: Algunos servos saturan antes de 0°/180°. Ajusta `SERVO_MIN_US`/`SERVO_MAX_US` hasta que el servo recorra seguro sin forzarse.

## Verificación

1. Arranque: `=== Práctica 5: Control PWM para Servomotores ===`.
2. Menú funcional: selección 1–4 y `q` responde.
3. Barrido: el servo oscila suave entre extremos sin vibración excesiva.
4. Manual: ángulos 0–180° posicionan de forma reproducible.
5. Potenciómetro: el ángulo sigue la perilla (lineal aprox.).

**Criterio de éxito**: Servo recorre sin atascos, no se calienta, y mantiene posición acorde al ángulo pedido.

## Teoría rápida: PWM de servos

- Periodo fijo ≈ 20 ms (50 Hz).
- Ancho de pulso típico: 1.0 ms ≈ 0°, 1.5 ms ≈ 90°, 2.0 ms ≈ 180°.
- Algunos servos aceptan 0.5–2.4 ms para ampliar recorrido; otros no (cuidado).

Consulta [**docs/oscilograma.md**](docs/oscilograma.md) para forma de onda esperada y medición con osciloscopio.

## Herramientas (PC)

- `tools/servo_cli.py`: envía ángulos o pulsos por el puerto serie para pruebas rápidas desde el PC. Requiere `pyserial`.

Instalación (opcional):

```bash
pip install -r tools/requirements.txt
```

## Recursos

- MicroPython `machine.PWM`: https://docs.micropython.org/en/latest/library/machine.PWM.html
- Guía pinout ESP32: https://randomnerdtutorials.com/esp32-pinout-reference-gpios/
- Servos R/C: documentación del fabricante de tu modelo (SG90/MG996R, etc.)
