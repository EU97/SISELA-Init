# [Pn] · Mapa de pines (RP2040)

Rellena con el mapeo concreto de la práctica.

Tabla rápida (ejemplo):

| Señal | Pin Pico | Función RP2040 |
|------:|---------:|-----------------|
| VCC   | 3V3(OUT) | Alimentación    |
| GND   | GND      | Tierra          |
| SIG   | GPXX     | Señal principal |

Notas:
- ADC en RP2040: ADC0=GP26, ADC1=GP27, ADC2=GP28, ADC3=interno de temperatura.
- Lectura ADC con `read_u16()` (0..65535) y Vref ~3.3V.
