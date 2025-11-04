# Mapa de Pines — Práctica 8

## Sensores (ADC)

| Función | Pin ESP32 | Canal ADC | Rango | Simulación |
|---------|-----------|-----------|-------|------------|
| Altitud | GPIO34 | ADC1_CH6 | 0-4095 | Potenciómetro 10kΩ |
| Velocidad | GPIO35 | ADC1_CH7 | 0-4095 | Potenciómetro 10kΩ |
| Actitud | GPIO32 | ADC1_CH4 | 0-4095 | Potenciómetro 10kΩ |
| Luminosidad | GPIO33 | ADC1_CH5 | 0-4095 | LDR + R 10kΩ |

**Conexión**: Divisor de tensión 3.3V → Sensor → GND

---

## Servomotores (Superficies de control)

| Función | Pin ESP32 | Canal PWM | Frecuencia | Pulse Width |
|---------|-----------|-----------|------------|-------------|
| Alerón | GPIO25 | PWM 0 | 50 Hz | 1000-2000 µs |
| Elevador | GPIO26 | PWM 1 | 50 Hz | 1000-2000 µs |

**Conexión**: 
- Señal → Pin ESP32
- VCC → 5V fuente externa
- GND → GND común

---

## Actuador PWM (Motor/Hélice)

| Función | Pin ESP32 | Frecuencia | Destino |
|---------|-----------|------------|---------|
| Control Motor | GPIO18 | 1 kHz | Gate MOSFET |

**Etapa de potencia**:
- MOSFET N-channel (IRF540N o similar)
- Diodo flyback 1N4007 (cátodo a VCC motor)
- Motor DC o LED de potencia
- Fuente externa 5-12V

---

## Motor a pasos (Tren de aterrizaje)

### Opción A: A4988 / DRV8825 (NEMA 17)

| Señal | Pin ESP32 | Función |
|-------|-----------|---------|
| STEP | GPIO19 | Pulsos de paso |
| DIR | GPIO21 | Dirección |
| EN | GPIO5 | Enable (LOW activo) |

### Opción B: ULN2003 (28BYJ-48)

| Señal | Pin ESP32 | Función |
|-------|-----------|---------|
| IN1 | GPIO19 | Bobina 1 |
| IN2 | GPIO21 | Bobina 2 |
| IN3 | GPIO22 | Bobina 3 |
| IN4 | GPIO23 | Bobina 4 |

### Endstop (límite de tren)

| Señal | Pin ESP32 | Configuración |
|-------|-----------|---------------|
| Endstop | GPIO4 | INPUT + PULL_UP |

**Conexión endstop**: Normalmente abierto (NO), cierra a GND al activarse.

---

## Resumen de pines ocupados

| GPIO | Función |
|------|---------|
| 4 | Endstop (tren) |
| 5 | EN (stepper A4988) |
| 18 | PWM Motor |
| 19 | STEP (A4988) o IN1 (ULN2003) |
| 21 | DIR (A4988) o IN2 (ULN2003) |
| 22 | IN3 (ULN2003, si aplica) |
| 23 | IN4 (ULN2003, si aplica) |
| 25 | Servo Alerón |
| 26 | Servo Elevador |
| 32 | ADC Actitud |
| 33 | ADC Luminosidad |
| 34 | ADC Altitud |
| 35 | ADC Velocidad |

---


## Advertencia sobre ULN2003 y ADC

> **Nota:** Si usas el driver ULN2003, los pines GPIO25/26/32/33 pueden entrar en conflicto con los ADC si usas todos los sensores. Considera remapear sensores a otros pines disponibles o reducir el número de sensores.

## Notas importantes

1. **GND común**: Conectar GND de ESP32, fuente externa y todos los componentes
2. **Alimentación servos**: Desde fuente externa 5V, NO desde USB
3. **Protección inductiva**: Diodo flyback en motor DC obligatorio
4. **Pull-up endstop**: Configurado en software, conectar a GND al activarse
5. **Corriente máxima**: Verificar capacidad de fuente externa para todos los actuadores
6. **Pines ADC1**: Usar solo ADC1 (GPIO32-39) si se requiere WiFi posteriormente
