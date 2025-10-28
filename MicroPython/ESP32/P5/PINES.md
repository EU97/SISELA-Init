# Mapa de pines — Práctica 5: BMP280 (I2C)

Conexión del sensor barométrico digital BMP280 al ESP32 mediante protocolo I2C.

## Tabla de conexiones

| Señal | Pin ESP32 | Dispositivo externo | Descripción |
|-------|-----------|---------------------|-------------|
| **SDA** | **GPIO21** | BMP280 SDA | Datos I2C bidireccionales (Serial Data) |
| **SCL** | **GPIO22** | BMP280 SCL | Reloj I2C del master (Serial Clock) |
| 3V3 | 3V3 | BMP280 VCC/VIN | Alimentación del sensor (3.3V) |
| GND | GND | BMP280 GND | Tierra común |

## Notas importantes

- **GPIO21 (SDA)**: Pin de datos I2C por defecto en ESP32. Bidireccional, open-drain con pull-up.
- **GPIO22 (SCL)**: Pin de reloj I2C por defecto en ESP32. Generado por master, open-drain con pull-up.
- **Resistencias pull-up**: I2C requiere pull-ups (típ. 4.7kΩ) en SDA/SCL. La mayoría de módulos BMP280 ya las incluyen. ESP32 tiene pull-ups internos débiles (~45kΩ) que suelen ser insuficientes para Fast Mode (400 kHz).
- **Frecuencia I2C**: Configurada a 400 kHz (Fast Mode). Compatible con 100 kHz (Standard) y hasta 1 MHz (Fast Plus) si el sensor lo soporta.
- **Dirección I2C**: Por defecto **0x76**. Si el pin SDO del BMP280 está conectado a VCC, la dirección cambia a **0x77**.

## Pinout BMP280 (módulo breakout típico)

```
Vista superior (componentes hacia arriba):

 ┌──────────┐
 │   VCC    │  → 3.3V (ESP32 3V3)
 │   GND    │  → GND (ESP32 GND)
 │   SCL    │  → GPIO22 (ESP32 SCL)
 │   SDA    │  → GPIO21 (ESP32 SDA)
 │   CSB    │  → No conectado (I2C mode, pull-up interno)
 │   SDO    │  → No conectado (dirección 0x76) o VCC (dirección 0x77)
 └──────────┘

Notas:
- CSB (Chip Select): Pull-up para I2C, pull-down para SPI.
- SDO (Serial Data Out): Define dirección I2C (GND→0x76, VCC→0x77).
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

| Modo | Protocolo usado | Salida |
|------|-----------------|--------|
| 1 (ADC crudo) | I2C read registros 0xF7–0xFC | Valores ADC 20-bit |
| 2 (Temperatura) | I2C + compensación | °C |
| 3 (Presión) | I2C + compensación | hPa / kPa |
| 4 (Altitud) | I2C + fórmula barométrica | Metros |
| 5 (CSV monitor) | I2C + CSV | Timestamp, T, P, Alt |
| 6 (Info sensor) | I2C read calibración 0x88–0xA1 | Coeficientes dig_T, dig_P |

## Protocolo I2C: comunicación básica

### Secuencia de lectura típica

1. **START**: Master (ESP32) envía condición de inicio.
2. **Dirección + Write**: Envía dirección del sensor (0x76) + bit W (0).
3. **ACK**: Sensor responde con acknowledge.
4. **Registro**: Master envía dirección del registro a leer (ej: 0xF7).
5. **ACK**: Sensor responde.
6. **RESTART**: Master envía condición de reinicio.
7. **Dirección + Read**: Envía dirección del sensor + bit R (1).
8. **ACK**: Sensor responde.
9. **Datos**: Sensor envía N bytes de datos.
10. **NACK**: Master envía not-acknowledge en último byte.
11. **STOP**: Master envía condición de parada.

### Temporizaciones (400 kHz Fast Mode)

| Parámetro | Mín | Máx | Unidad |
|-----------|-----|-----|--------|
| Frecuencia SCL | 0 | 400 | kHz |
| Periodo SCL | 2.5 | — | µs |
| Tiempo de setup SDA | 100 | — | ns |
| Tiempo de hold SDA | 0 | 900 | ns |
| Tiempo de rise (SDA/SCL) | — | 300 | ns |
| Tiempo de fall (SDA/SCL) | — | 300 | ns |

## Troubleshooting I2C

| Problema | Causa probable | Solución |
|----------|----------------|----------|
| `Dispositivos detectados: []` | Conexiones incorrectas o sensor apagado | Verificar SDA/SCL cruzados, VCC/GND |
| `BMP280 no detectado (Chip ID: 0x00)` | Sin pull-ups o cables muy largos | Agregar resistencias 4.7kΩ a 3V3 |
| `OSError: [Errno 19] ENODEV` | Dirección I2C incorrecta | Probar 0x76 y 0x77 |
| Lecturas erráticas | Ruido EMI en cables | Usar cables cortos (<30 cm), blindados |
| Timeout en lectura | Frecuencia I2C muy alta | Reducir a 100 kHz |

## Múltiples dispositivos I2C

El bus I2C permite conectar varios sensores simultáneamente si tienen direcciones únicas:

**Ejemplo**: BMP280 (0x76) + OLED SSD1306 (0x3C) + MPU6050 (0x68)

```python
# Conectar todos al mismo bus SDA/SCL
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
devices = i2c.scan()  # → [0x3C, 0x68, 0x76]

bmp = BMP280(i2c, addr=0x76)
# oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)
# mpu = MPU6050(i2c, addr=0x68)
```

**NOTA**: Algunos sensores tienen direcciones fijas (conflicto). Usa múltiples buses I2C (ESP32 tiene I2C0 e I2C1) o multiplexores I2C (TCA9548A).

## Referencias

- **BMP280 Datasheet**: https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp280-ds001.pdf
- **I2C Specification (NXP)**: https://www.nxp.com/docs/en/user-guide/UM10204.pdf
- **ESP32 I2C Driver**: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/i2c.html
- **MicroPython machine.I2C**: https://docs.micropython.org/en/latest/library/machine.I2C.html
