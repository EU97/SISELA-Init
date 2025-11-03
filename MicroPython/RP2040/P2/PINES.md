# P2 · Mapa de Pines (RP2040)

Sensor de posición analógico (potenciómetro) conectado a entrada ADC.

## Conexiones

- VCC (sensor) → 3V3 (OUT) — Pin físico 36
- GND (sensor) → GND — Pin físico 38 (o cualquier GND)
- Señal (sensor) → GP26 (ADC0) — Pin físico 31

## Notas Importantes

- **GP26/GP27/GP28 son los únicos pines con ADC** en RP2040 (ADC0/ADC1/ADC2 respectivamente)
- ADC interno: 12 bits reales, pero `read_u16()` devuelve 0-65535 (16 bits con padding de ceros)
- Voltaje de referencia: 3.3V fijo (no configurable)
- **NO usar 5V** en pines ADC del RP2040 - daño permanente garantizado
- Pin físico 31 (GP26/ADC0) es el más recomendado para ADC simple

## Tabla de Pines ADC

| Pin físico | GPIO | Función | Rango |
|-----------|------|---------|-------|
| 31 | GP26 | ADC0 | 0-3.3V |
| 32 | GP27 | ADC1 | 0-3.3V |
| 34 | GP28 | ADC2 | 0-3.3V |
| - | ADC3 | Temp interno | Sensor onboard |

## Comparativa ESP32 vs RP2040

| Aspecto | ESP32 | RP2040 |
|---------|-------|--------|
| Pines ADC | GPIO32-39 (ADC1), GPIO0-10 (ADC2) | GP26, GP27, GP28 |
| Canales | 18 canales | 3 canales + 1 temp |
| Resolución | 12 bits (0-4095) | 12 bits (read_u16: 0-65535) |
| Función lectura | `adc.read()` | `adc.read_u16()` |
| Atenuación | Configurable (0dB-11dB) | Fija (0-3.3V) |
| Configuración | `atten()`, `width()` | Solo `ADC(pin)` |
| Rango de voltaje | 0-3.6V (con 11dB) | 0-3.3V |

## Ejemplo de uso

```python
from machine import ADC

# ESP32
adc = ADC(Pin(34))
adc.atten(ADC.ATTN_11DB)
adc.width(ADC.WIDTH_12BIT)
raw = adc.read()  # 0-4095
voltage = (raw / 4095) * 3.3

# RP2040
adc = ADC(26)  # GP26 = ADC0
raw = adc.read_u16()  # 0-65535
voltage = (raw / 65535) * 3.3
```

## Distribución de Pines GP26-28 en Raspberry Pi Pico

```
                  ┌─────────┐
                  │         │
     GND (38) ────┤ GND     │
           ────┤ GP22    │
           ────┤ RUN     │
           ────┤ GP26    │──── ADC0 (pin 31) ← SENSOR AQUÍ
           ────┤ GP27    │──── ADC1 (pin 32)
           ────┤ AGND    │──── GND analógico (pin 33)
           ────┤ GP28    │──── ADC2 (pin 34)
  3V3 OUT (36) ────┤ 3V3(OUT)│──── Alimentación sensor
     GND (38) ────┤ GND     │
                  │         │
                  └─────────┘
```

## Conversión de Código ESP32 → RP2040

### ADC Setup
```python
# ESP32
from machine import ADC, Pin
adc = ADC(Pin(34))
adc.atten(ADC.ATTN_11DB)
adc.width(ADC.WIDTH_12BIT)

# RP2040
from machine import ADC
adc = ADC(26)  # Directo con número de pin
```

### Lectura
```python
# ESP32
raw = adc.read()  # 0-4095
ADC_MAX = 4095

# RP2040
raw = adc.read_u16()  # 0-65535
ADC_MAX = 65535
```

### Conversión a Voltaje
```python
# Ambos usan la misma fórmula conceptual
voltage = (raw / ADC_MAX) * 3.3
```

## Recomendaciones

1. **Filtrado**: Usa media móvil o filtro FIR para reducir ruido (el ADC del RP2040 puede ser ruidoso)
2. **Muestreo**: No superar ~100kHz en muestreo continuo (limitación del ADC)
3. **Impedancia**: Sensor/fuente debe tener impedancia baja (<10kΩ recomendado)
4. **Calibración**: El ADC del RP2040 tiene offset/ganancia variables; considera calibrar con puntos conocidos
5. **Temperatura**: ADC3 (interno) puede leer temperatura del chip con `ADC(4)`

## Recursos

- [RP2040 ADC Quickref](https://docs.micropython.org/en/latest/rp2/quickref.html#adc-analog-to-digital-conversion)
- [RP2040 Datasheet - ADC](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf#page=565)
- [Pico Pinout](https://datasheets.raspberrypi.com/pico/Pico-R3-A4-Pinout.pdf)
