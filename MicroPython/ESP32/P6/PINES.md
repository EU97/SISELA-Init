# PINES — P6 Conmutación de potencia (PWM + transistor)

Conexiones principales en ESP32 (DevKit) y etapa de potencia:

- GPIO18 → Resistencia 220 Ω → compuerta/base del transistor (señal PWM)
- GND (ESP32) → GND de la fuente externa (GND común obligatorio)
- GPIO34 (opcional) → Potenciómetro (cursor). Extremos a 3V3 y GND.

Etapa de potencia típica (bajo lado, MOSFET canal N):

- Drenador (D) → extremo negativo de la carga
- Extremo positivo de la carga → +V (5–12 V)
- Fuente (S) → GND común
- Diodo flyback (1N5819/1N4007) en paralelo con la carga (cátodo a +V, ánodo al drenador) para cargas inductivas

Notas y seguridad:

- Nunca alimentes la carga desde el 3V3 del ESP32. Usa fuente externa adecuada.
- Imprescindible GND común entre ESP32 y la fuente externa.
- Para MOSFET, usa uno de compuerta lógica (ej. AO3400, IRLZ44N). Para BJT, añade resistencia base y calcula corriente.
- Ajusta la frecuencia PWM según la carga (500 Hz – 2 kHz suele funcionar bien).
