# Práctica 4 (P4) — Resumen Ejecutivo

## Estado: ✅ COMPLETA (BMP180)

## Descripción general

Lectura I2C del sensor digital de presión barométrica BMP180 con algoritmo de compensación completo (11 coeficientes de calibración), cálculo de altitud barométrica con fórmula ISA, ajuste QNH y herramienta de visualización tipo instrumento aeronáutico.

## Estructura de archivos

```
MicroPython/ESP32/P4/
├── boot.py                    ✓ Mensaje de arranque
├── main.py                    ✓ Programa principal (5 modos + menú)
├── pymakr.conf                ✓ Configuración Pymakr
├── README.md                  ✓ Guía completa de uso
├── PINES.md                   ✓ Tabla de pines I2C
├── lib/
│   └── bmp180.py              ✓ Driver BMP180 (compensación completa)
├── assets/
│   ├── wiring.mmd             ✓ Diagrama Mermaid
│   └── wiring.svg             ✓ Diagrama estático
├── docs/
│   └── BMP180.md              ✓ Ficha técnica del sensor
└── tools/
    ├── altimeter_gui.py       ✓ Altímetro visual tipo aeronáutico
    ├── requirements.txt       ✓ Dependencias Python
    └── README.md              ✓ Guía de herramientas
```

## Sensor: BMP180

| Característica | Valor |
|----------------|-------|
| **Tipo** | MEMS piezoresistivo digital |
| **Interfaz** | I2C (dirección 0x77) |
| **Rango presión** | 300–1100 hPa |
| **Rango temperatura** | –40 a +85 °C |
| **Resolución** | Hasta 0.01 hPa (ultra-high) |
| **Calibración** | 11 coeficientes en EEPROM |

## Conexión con ESP32

| Pin ESP32 | Pin BMP180 | Función |
|-----------|------------|---------|
| GPIO21 | SDA | I2C Data |
| GPIO22 | SCL | I2C Clock |
| 3V3 | VCC | Alimentación |
| GND | GND | Tierra |

## Conexión con RP2040

| Pin RP2040 | Pin BMP180 | Función |
|------------|------------|---------|
| GP0 | SDA | I2C Data |
| GP1 | SCL | I2C Clock |
| 3V3(OUT) | VCC | Alimentación |
| GND | GND | Tierra |

## Modos de operación

| Modo | Función | Salida |
|------|---------|--------|
| **1** | Datos crudos + calibración | 11 coeficientes + UT, UP sin compensar |
| **2** | T + P compensados | Pasos del algoritmo + valores en °C y hPa |
| **3** | Altímetro barométrico | Altitud (m/ft) con ajuste QNH |
| **4** | Monitor CSV | `timestamp_ms,temp_C,pressure_hPa,altitude_m` |
| **5** | Comparativa de alturas | Medición guiada con promediado y tabla de diferencias |

## Fórmulas principales

### Altitud barométrica (ISA)
```
h = 44330 × (1 − (P / P₀)^(1/5.255))   [metros]
```

### Compensación de temperatura
```
X1 = (UT − AC6) × AC5 / 2¹⁵
X2 = MC × 2¹¹ / (X1 + MD)
B5 = X1 + X2
T  = (B5 + 8) / 2⁴   [0.1 °C]
```

### Compensación de presión
Algoritmo completo de Bosch con 13 pasos intermedios (B6, B3, B4, B7, etc.)
Ver `docs/BMP180.md` para detalles completos.

## Herramientas de visualización

```bash
cd MicroPython/ESP32/P4/tools
pip install -r requirements.txt
python altimeter_gui.py --port COM5
```

Altímetro visual con:
- Carátula circular con aguja (0–1000 m/rev)
- Ventana de Kollsman (QNH) 
- Lecturas digitales (altitud, presión, temperatura)
- Strip chart de altitud vs tiempo
- Grabación CSV

## Implementación C++

Archivo: `C++/SISELA-CPP/src/practices/p4.cpp`
- Comunicación Wire (I2C)
- Compensación completa en aritmética entera
- 3 modos: Raw, T+P compensado, Altímetro

## Cambios respecto a versión anterior

- **Sensor**: MPX5500DP (ADC analógico) → **BMP180** (I2C digital)
- **Comunicación**: ADC → I2C (SDA+SCL, dirección 0x77)
- **Procesamiento**: Función de transferencia lineal → Algoritmo de compensación con 11 coeficientes
- **Altitud**: No incluida → Fórmula barométrica ISA con QNH
- **Visualización**: Gráfica matplotlib → Altímetro aeronáutico tkinter
- **Modos**: 5 (crudo, T+P, altímetro, CSV, comparativa de alturas)
