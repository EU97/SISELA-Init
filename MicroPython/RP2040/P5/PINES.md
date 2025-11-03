# Mapa de pines — Práctica 5: Servomotores PWM (RP2040)

Conexión de un servomotor R/C estándar al **RP2040** mediante señal PWM de 50 Hz.

## Tabla de conexiones

| Señal | Pin RP2040 | Dispositivo externo | Descripción |
|-------|------------|---------------------|-------------|
| **PWM_SERVO** | **GP18** (PWM1 A) | Servo (señal) | Señal de control (amarillo/blanco) a 50 Hz |
| **5V** | VSYS | Servo VCC | Alimentación del servo desde USB (rojo) |
| **GND** | GND | Servo GND | Tierra común |
| **ADC_IN** (opcional) | **GP26** (ADC0) | Potenciómetro cursor | Control analógico de ángulo |

## 🔄 Diferencias con ESP32

| Aspecto | ESP32 | RP2040 |
|---------|-------|--------|
| **Pin PWM** | GPIO18 | GP18 (PWM1 A) |
| **Canales PWM** | 16 canales independientes | **8 slices × 2 canales (16 total)** |
| **Pin ADC** | GPIO34 (ADC1_CH6) | GP26 (ADC0) |
| **Resolución ADC** | 12 bits (0–4095) | **16 bits (0–65535)** ✅ |
| **Configuración ADC** | Requiere `atten(11dB)` | **No requiere configuración** ✅ |
| **Lectura ADC** | `adc.read()` | `adc.read_u16()` |
| **Alimentación 5V** | Desde fuente externa | **VSYS disponible (5V USB)** ✅ |

## Notas importantes

- El servo requiere corriente de pico (0.3–2 A según modelo). El RP2040 puede usar **VSYS** (5V desde USB) para servos pequeños (SG90, MG90S). Para servos grandes (MG996R), usa fuente externa dedicada.
- **GP18** está en PWM slice 1, canal A. Cualquier pin PWM del RP2040 funciona, pero GP18 coincide con ESP32 GPIO18 para compatibilidad.
- Periodo típico: 20 ms (50 Hz). Pulso: 1.0 ms ≈ 0°, 1.5 ms ≈ 90°, 2.0 ms ≈ 180° (ajustable 0.5–2.4 ms bajo tu responsabilidad).
- Para potenciómetro, el RP2040 **siempre mide 0–3.3V** (no requiere divisor ni atenuación).

## Pinout RP2040 relevante

```
         RP2040 (Raspberry Pi Pico)
    ┌─────────────────────┐
GP18│ PWM1 A ●            │ Señal servo (50 Hz)
    │                     │
GP26│ ADC0 ●              │ Potenciómetro (opcional)
    │                     │
    │      ● VSYS         │ 5V USB para servo pequeño
    │      ● GND          │ Tierra común
    └─────────────────────┘
```

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
| 4 (Potenciómetro) | ADC GP26 | Ángulo proporcional 0–180° |

## Ventajas del RP2040 para servos

### 1. PWM más estable
El RP2040 tiene **jitter PWM muy bajo** (~1 ns típico), ideal para servos precisos.

```python
# ESP32: Jitter típico ~10 ns
# RP2040: Jitter típico ~1 ns ✅ (10× mejor)
```

### 2. ADC de 16 bits para control suave
Con 65535 valores vs 4095 (ESP32), el control por potenciómetro es **16× más suave**.

```python
# ESP32 (12-bit):  180° / 4095 = 0.044°/bit
# RP2040 (16-bit): 180° / 65535 = 0.0027°/bit ✅ (16× mejor resolución)
```

### 3. Alimentación simplificada
**VSYS** proporciona 5V directo del USB, suficiente para servos pequeños sin fuente externa.

```
ESP32:  Requiere fuente 5V externa siempre
RP2040: VSYS (5V @ 500mA máx USB) para SG90/MG90S ✅
```

## Recomendaciones de cableado

- Mantén el cable de señal del servo lo más corto posible.
- Si el servo introduce ruido, añade un condensador electrolítico (470–1000 µF) cerca del servo entre VSYS/5V y GND.
- Para servos >500 mA, usa fuente externa y conecta solo GND común con RP2040.
- Evita compartir la alimentación del servo con sensores sensibles sin filtrado.

## Comparativa de consumo

| Servo | Idle | Movimiento | Peak | Fuente recomendada |
|-------|------|------------|------|-------------------|
| **SG90** (mini) | 10 mA | 100–250 mA | 600 mA | VSYS (USB) ✅ |
| **MG90S** (metal) | 10 mA | 150–300 mA | 800 mA | VSYS o externa |
| **MG996R** (torque) | 20 mA | 500–900 mA | 1500 mA | Externa 5V 2A ❌ |

**Regla**: Si peak < 500 mA → VSYS. Si peak > 500 mA → fuente externa.

## Referencias

- **RP2040 PWM Guide**: https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf (Sección 4.5)
- **Servo Control Theory**: Ver [docs/oscilograma.md](docs/oscilograma.md)
- **MicroPython PWM RP2040**: https://docs.micropython.org/en/latest/rp2/quickref.html#pwm-pulse-width-modulation
