# Tabla de Pines — Práctica 4 (ESP32)

## Sensor: BMP180 (Presión Barométrica + Temperatura)

| Pin ESP32 | Pin BMP180 | Función | Notas |
|-----------|------------|---------|-------|
| **GPIO21** | SDA | I2C Data | Línea de datos bidireccional |
| **GPIO22** | SCL | I2C Clock | Línea de reloj (maestro) |
| **3V3** | VCC | Alimentación | 1.8–3.6 V (módulo con regulador acepta 5V) |
| **GND** | GND | Tierra | Referencia común |

## Diagrama de conexión

```
ESP32                BMP180 Módulo
┌───────┐           ┌───────────┐
│  3V3  ├──────────►│ VCC       │
│  GND  ├──────────►│ GND       │
│ GPIO21├───────────│ SDA       │  (I2C Data)
│ GPIO22├───────────│ SCL       │  (I2C Clock)
└───────┘           └───────────┘
```

## Notas técnicas

### Protocolo I2C
- **Dirección**: `0x77` (fija, no configurable en BMP180)
- **Frecuencia**: 100 kHz (estándar) — soporta hasta 3.4 MHz
- **Pull-ups**: El módulo GY-68 incluye resistencias de pull-up de 4.7 kΩ
- **Bus**: I2C0 del ESP32 (por defecto: SDA=21, SCL=22)

### Sobre el sensor
- **Tipo**: MEMS piezoresistivo (puente Wheatstone)
- **Rango presión**: 300–1100 hPa
- **Rango temperatura**: –40 a +85 °C
- **Resolución**: hasta 0.01 hPa (modo ultra-alta resolución)
- **Calibración**: 11 coeficientes en EEPROM (AC1–AC6, B1, B2, MB, MC, MD)

### Alimentación
- El BMP180 opera a 1.8–3.6 V nativo
- El módulo GY-68 incluye regulador LDO → acepta 3.3 V o 5 V en pin VCC
- Consumo: ~5 µA en modo estándar, ~0.1 µA en standby

## Puntos de medida — Análisis de señales (modos 6–7)

El BMP180 es digital: **no se inyecta señal con el generador de funciones**. Los puntos
de sonda del osciloscopio son el propio bus I2C:

| Punto de sonda | Señal | Config. osciloscopio sugerida |
|---|---|---|
| CH1 → **GPIO22 (SCL)** | reloj I2C ~100 kHz | 10 µs/div, trigger flanco de bajada |
| CH2 → **GPIO21 (SDA)** | datos I2C | acoplo DC, 1 V/div |
| pinza → **GND** | referencia | — |

Medidas: frecuencia de SCL, duración de una transacción de lectura, periodo entre
transacciones (= 1/Fs del modo activo). Ver [docs/analisis_senales.md](docs/analisis_senales.md).
