# Tabla de Pines — Práctica 4 (RP2040 — Raspberry Pi Pico)

## Sensor: BMP180 (Presión Barométrica + Temperatura)

| Pin RP2040 | Pin físico | Pin BMP180 | Función | Notas |
|------------|------------|------------|---------|-------|
| **GP0** | 1 | SDA | I2C Data | I2C0 SDA por defecto |
| **GP1** | 2 | SCL | I2C Clock | I2C0 SCL por defecto |
| **3V3(OUT)** | 36 | VCC | Alimentación | 3.3 V regulados |
| **GND** | 38 | GND | Tierra | Referencia común |

## Diagrama de conexión

```
Raspberry Pi Pico          BMP180 Módulo
┌──────────────┐          ┌───────────┐
│ 3V3(OUT) [36]├─────────►│ VCC       │
│ GND      [38]├─────────►│ GND       │
│ GP0(SDA) [ 1]├──────────│ SDA       │  (I2C Data)
│ GP1(SCL) [ 2]├──────────│ SCL       │  (I2C Clock)
└──────────────┘          └───────────┘
```

## Notas técnicas

### Protocolo I2C
- **Dirección**: `0x77` (fija, no configurable en BMP180)
- **Frecuencia**: 100 kHz (estándar) — soporta hasta 3.4 MHz
- **Pull-ups**: El módulo GY-68 incluye resistencias de pull-up de 4.7 kΩ
- **Bus**: I2C0 del RP2040 (GP0=SDA, GP1=SCL)

### Pines I2C alternativos (RP2040)
El RP2040 permite reasignar I2C a otros pines:
- I2C0: GP0/GP1, GP4/GP5, GP8/GP9, GP12/GP13, GP16/GP17, GP20/GP21
- I2C1: GP2/GP3, GP6/GP7, GP10/GP11, GP14/GP15, GP18/GP19, GP26/GP27

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
