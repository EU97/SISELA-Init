# Práctica 4 — Altímetro Barométrico BMP180 (ESP32)

## Descripción

Lectura I2C del sensor digital de presión barométrica BMP180 con algoritmo de compensación completo (11 coeficientes de calibración), cálculo de altitud barométrica con fórmula ISA y ajuste QNH.

## Sensor: BMP180

| Característica | Valor |
|----------------|-------|
| **Tipo** | MEMS piezoresistivo digital |
| **Interfaz** | I2C (dirección 0x77) |
| **Rango presión** | 300–1100 hPa |
| **Rango temperatura** | –40 a +85 °C |
| **Resolución** | Hasta 0.01 hPa |
| **Sobremuestreo** | 4 modos (ultra-low → ultra-high) |
| **Calibración** | 11 coeficientes de fábrica en EEPROM |

## Conexión

| ESP32 | BMP180 | Función |
|-------|--------|---------|
| GPIO21 | SDA | I2C Data |
| GPIO22 | SCL | I2C Clock |
| 3V3 | VCC | Alimentación |
| GND | GND | Tierra |

Ver [PINES.md](PINES.md) para detalles técnicos.

## Modos de operación

| Modo | Función | Descripción |
|------|---------|-------------|
| **1** | Datos crudos + calibración | Muestra 11 coeficientes y valores UT/UP sin compensar |
| **2** | T + P compensados | Algoritmo de compensación paso a paso visible |
| **3** | Altímetro barométrico | Altitud en m/ft con ajuste QNH ('q' para QNH, 'aXXX' para calibrar) |
| **4** | Monitor CSV | `timestamp_ms,temp_C,pressure_hPa,altitude_m` para visualización |
| **5** | Comparativa de alturas | Medición guiada a distintos niveles con promediado y estadísticas |

## Estructura de archivos

```
P4/
├── boot.py            # Mensaje de arranque
├── main.py            # Programa principal (5 modos)
├── pymakr.conf        # Configuración Pymakr
├── PINES.md           # Tabla de pines
├── README.md          # Esta guía
├── lib/
│   └── bmp180.py      # Driver BMP180 (compensación completa)
├── assets/            # Diagramas
├── docs/              # Fichas técnicas
└── tools/
    ├── altimeter_gui.py   # Altímetro visual tipo aeronáutico
    ├── requirements.txt   # Dependencias Python
    └── README.md          # Guía de herramientas
```

## Uso rápido

1. **Cargar archivos** con Pymakr o Thonny (incluir `lib/bmp180.py`)
2. **Conectar BMP180** según tabla de pines
3. **Abrir terminal serie** (115200 baud)
4. **Seleccionar modo** del menú interactivo
5. **Presionar 'm'** para regresar al menú

## Fórmulas clave

**Altitud barométrica (ISA):**
```
h = 44330 × (1 − (P / P₀)^(1/5.255))   [metros]
```

Donde:
- `P` = presión medida (Pa)
- `P₀` = presión al nivel del mar / QNH (Pa)

**Conversión ft → m:**
```
1 ft = 0.3048 m
```

## Herramientas de visualización

```bash
cd tools
pip install -r requirements.txt
python altimeter_gui.py --port COM5
```

Ver [tools/README.md](tools/README.md) para instrucciones completas.
