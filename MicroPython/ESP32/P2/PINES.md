# P2 · Mapa de Pines (ESP32)

Sensor de posición analógico (potenciómetro) conectado a entrada ADC.

- VCC (sensor) → 3V3 ESP32
- GND (sensor) → GND ESP32
- Señal (sensor) → GPIO34 (ADC1_CH6)

Notas:
- GPIO34 es solo-entrada, ideal para ADC.
- Usamos atenuación 11 dB para medir ~0–3.3 V.
- Evita alimentar el potenciómetro con 5V.

Tabla rápida:

| Señal | Pin ESP32 | Descripción         |
|------:|-----------|---------------------|
| VCC   | 3V3       | Alimentación +3.3V  |
| GND   | GND       | Tierra              |
| SIG   | GPIO34    | Entrada analógica   |
