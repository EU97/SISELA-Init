# P3 · Mapa de pines (ESP32 + NTC)

Configuración del divisor resistivo para medir temperatura con NTC:

- VCC: 3V3
- R_SERIES: 10kΩ (entre 3V3 y nodo)
- NTC: 10kΩ @25°C, Beta≈3950 (entre nodo y GND)
- Nodo (señal): GPIO34 (ADC1) — pin de solo entrada
- GND: GND

Tabla rápida:

| Señal   | Pin ESP32 | Descripción                          |
|--------:|-----------|--------------------------------------|
| VCC     | 3V3       | Alimentación del divisor             |
| Nodo    | GPIO34    | Lectura ADC del divisor (V nodo)     |
| Rserie  | —         | 10kΩ hacia 3V3                       |
| NTC     | —         | 10kΩ@25°C hacia GND                  |
| GND     | GND       | Tierra común                          |

Notas:
- GPIO34 es entrada‑solo (no intentes usarlo como salida).
- Configura la atenuación del ADC en 11dB para abarcar ~3.3V.
- El ADC del ESP32 no es lineal; los cálculos son aproximados sin calibración.

## Diagrama de conexiones

![Wiring](./assets/wiring.svg)

- Mermaid editable: `assets/wiring.mmd`.
- Si todos los voltajes están dentro de 0–3.3V y usas 11dB, no necesitas divisor adicional.

## Relación con los modos

- Modo 1: imprime ADC crudo y voltaje de nodo.
- Modo 2: estima la resistencia de la NTC a partir del voltaje de nodo.
- Modo 3: calcula temperatura en °C usando la ecuación Beta.
- Modo 4: emite CSV con t,adc,V,R,T para graficar o registrar.
