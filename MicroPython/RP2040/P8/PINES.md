# Mapa de Pines — Práctica 8 (RP2040)

## Sensores (ADC)

RP2040 dispone de 3 entradas ADC externas (GP26–GP28) y 1 canal interno de temperatura (ADC4). Para 4 "sensores" se usa la temperatura interna como cuarto canal por defecto.

| Función    | Pin RP2040 | Canal ADC | Rango  | Simulación            |
|------------|------------|-----------|--------|-----------------------|
| Altitud    | GP26       | ADC0      | 0-65535 (u16) | Potenciómetro 10kΩ  |
| Velocidad  | GP27       | ADC1      | 0-65535 (u16) | Potenciómetro 10kΩ  |
| Actitud    | GP28       | ADC2      | 0-65535 (u16) | Potenciómetro 10kΩ  |
| Luminosidad| TEMP (int) | ADC4      | 0-65535 (u16) | Temp interna como proxy |

Notas:
- Conecta divisores de tensión entre 3.3V → Sensor → GND.
- Si necesitas 4 entradas externas, reubica el tren ULN2003 o usa un multiplexor ADC.

---

## Servomotores (Superficies de control)

| Función  | Pin RP2040 | PWM | Frecuencia | Pulse Width |
|----------|------------|-----|------------|-------------|
| Alerón   | GP14       | PWM | 50 Hz      | 1000-2000 µs|
| Elevador | GP15       | PWM | 50 Hz      | 1000-2000 µs|

Recomendaciones:
- Alimenta servos desde fuente 5V externa.
- Conecta GND común entre RP2040 y la fuente externa.

---

## Actuador PWM (Motor/Hélice)

| Función       | Pin RP2040 | Frecuencia | Destino     |
|---------------|------------|------------|-------------|
| Control Motor | GP13       | 1 kHz      | Gate MOSFET |

Etapa de potencia:
- MOSFET N-channel (IRLZ44N/IRF540N o similar)
- Diodo flyback (1N4007) en paralelo con la carga
- Fuente externa acorde a la carga

---

## Motor a pasos (Tren de aterrizaje)

### Opción A: A4988 / DRV8825 (NEMA 17 recomendado)

| Señal | Pin RP2040 | Función |
|-------|------------|---------|
| STEP  | GP18       | Pulsos de paso |
| DIR   | GP19       | Dirección |
| EN    | GP5        | Enable (LOW activo) |

### Opción B: ULN2003 (28BYJ-48)

| Señal | Pin RP2040 | Función |
|-------|------------|---------|
| IN1   | GP26       | Bobina 1 |
| IN2   | GP27       | Bobina 2 |
| IN3   | GP28       | Bobina 3 |
| IN4   | GP22       | Bobina 4 |

⚠ Importante: Esta opción usa GP26–GP28 que también son ADC. Si seleccionas ULN2003, debes remapear los sensores ADC a otros pines o reducir a 3 sensores (usando TEMP como cuarto).

### Endstop (límite de tren)

| Señal   | Pin RP2040 | Configuración |
|---------|------------|---------------|
| Endstop | GP4        | INPUT + PULL_UP |

Conexión: contacto normalmente abierto (NO) que cierra a GND al activarse.

---

## Resumen de pines ocupados (configuración por defecto)

| GPIO | Función                      |
|------|------------------------------|
| GP4  | Endstop (tren)               |
| GP5  | EN (stepper A4988)           |
| GP13 | PWM Motor                    |
| GP14 | Servo Alerón                 |
| GP15 | Servo Elevador               |
| GP18 | STEP (A4988)                 |
| GP19 | DIR (A4988)                  |
| GP22 | IN4 (ULN2003, si aplica)     |
| GP26 | ADC Altitud (o IN1 ULN2003)  |
| GP27 | ADC Velocidad (o IN2 ULN2003)|
| GP28 | ADC Actitud (o IN3 ULN2003)  |

---

## Notas

1. GND común entre todas las fuentes y el RP2040 es obligatorio.
2. No alimentes servos desde el USB del RP2040; usa fuente externa.
3. Añade diodo flyback para cargas inductivas.
4. El endstop usa pull-up interno; cablea a GND al activarse.
5. Si activas ULN2003, revisa conflictos con ADC y remapea en `main.py`.
