# Mapa de pines — Práctica 5: Servomotores PWM

Conexión de un servomotor R/C estándar al ESP32 mediante señal PWM de 50 Hz.

## Tabla de conexiones

| Señal | Pin ESP32 | Dispositivo externo | Descripción |
|-------|-----------|---------------------|-------------|
| **PWM_SERVO** | **GPIO18** | Servo (señal) | Señal de control (amarillo/blanco) a 50 Hz |
| **5V** | 5V | Servo VCC | Alimentación del servo (fuente externa recomendada) |
| **GND** | GND | Servo GND | Tierra común entre fuente y ESP32 |
| **ADC_IN** (opcional) | **GPIO34** | Potenciómetro cursor | Control analógico de ángulo |

## Notas importantes

- El servo requiere corriente de pico (0.3–2 A según modelo). Usa una fuente de 5V dedicada. Comparte GND con el ESP32.
- Evita pines de sólo entrada (GPIO34–39) para la señal PWM del servo. GPIO18 es una opción segura.
- Periodo típico: 20 ms (50 Hz). Pulso: 1.0 ms ≈ 0°, 1.5 ms ≈ 90°, 2.0 ms ≈ 180° (ajustable 0.5–2.4 ms bajo tu responsabilidad).
- Para potenciómetro, usa atenuación 11 dB (0–3.3V) y divisor si tu potenciómetro va a 5V.

## Diagrama de conexiones

Ver **[assets/wiring.svg](assets/wiring.svg)** para diagrama visual completo.

Para editar el diagrama fuente: **[assets/wiring.mmd](assets/wiring.mmd)** (formato Mermaid).

### Generar diagrama estático

```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i assets/wiring.mmd -o assets/wiring.svg -b transparent
```

## Relación con modos del programa

| Modo | Entrada | Salida |
|------|---------|--------|
| 1 (Barrido) | — | 0–180–0° en bucle |
| 2 (Ángulo) | REPL | Ángulo absoluto 0–180° |
| 3 (Pulso us) | REPL | Pulso directo para calibración |
| 4 (Potenciómetro) | ADC GPIO34 | Ángulo proporcional 0–180° |

## Recomendaciones de cableado

- Mantén el cable de señal del servo lo más corto posible.
- Si el servo introduce ruido, añade un condensador electrolítico (470–1000 µF) cerca del servo entre 5V y GND.
- Evita compartir la alimentación del servo con sensores sensibles sin filtrado.
