# Práctica 3 — Medición de Temperatura Aeronáutica con NTC (RP2040 + MicroPython)

Esta práctica mide temperatura usando una NTC en un divisor resistivo y el ADC del Raspberry Pi Pico (RP2040). Incluye modos para ver ADC, resistencia y temperatura, y un monitor CSV para graficar.

---

## 🎯 Objetivos

- Cablear un divisor resistivo con NTC y leerlo con el ADC del RP2040
- Calcular la temperatura usando la ecuación Beta (R0, Beta, T0)
- Registrar datos en formato CSV para analizar dinámica térmica y ruido
- Comparar diferencias entre RP2040 y ESP32 en lectura ADC

---

## 📦 Materiales

- **Raspberry Pi Pico** (RP2040)
- **NTC 10kΩ @25°C**, Beta≈3950
- **Resistencia 10kΩ** (serie) tolerancia 1% recomendada
- **Protoboard** y cables jumper
- **Cable USB** (para alimentación y comunicación)
- **Multímetro** (opcional, para verificación)

---

## 🔌 Conexiones

![Wiring](./assets/wiring.svg)

**Ver detalles completos en**: [`PINES.md`](./PINES.md)

### Esquema Simplificado

```
3V3 (Pin 36) ──┬─── 10kΩ R_SERIES ───┬─── GP26 (Pin 31, ADC0)
               │                      │
               └─── NTC 10kΩ ─────────┴─── GND (Pin 38)
```

### Mapa de Pines (Resumen)

| Componente | Conexión           | Pin Físico |
|------------|--------------------|------------|
| R_SERIES   | 3V3 → Nodo         | 36 → nodo  |
| NTC        | Nodo → GND         | nodo → 38  |
| Señal ADC  | Nodo → GP26 (ADC0) | nodo → 31  |

---

## 🆚 Diferencias: ESP32 vs RP2040

| Característica         | ESP32                          | RP2040 (Pico)               |
|------------------------|--------------------------------|-----------------------------|
| **Pin ADC**            | GPIO34 (ADC1_CH6)              | GP26 (ADC0)                 |
| **Canales ADC**        | 18 canales (GPIO32-39)         | 3 canales (GP26-GP28)       |
| **Función lectura**    | `adc.read()`                   | `adc.read_u16()`            |
| **Rango valores**      | 0-4095 (12-bit)                | 0-65535 (16-bit)            |
| **Inicialización**     | `ADC(Pin(34))`                 | `ADC(26)`                   |
| **Configuración**      | `atten()`, `width()` requerido | No requiere configuración   |
| **Voltaje máximo**     | ~3.6V (con ATTN_11DB)          | 3.3V estricto (sin protección) |
| **Linealidad**         | Baja (requiere calibración)    | Alta (calibración opcional) |
| **Conversión voltaje** | `(adc/4095) * 3.3`             | `(adc/65535) * 3.3`         |

### Cambios Clave en el Código

```python
# ESP32
from machine import Pin, ADC
adc = ADC(Pin(34))
adc.atten(ADC.ATTN_11DB)
adc.width(ADC.WIDTH_12BIT)
raw = adc.read()  # 0-4095
voltage = (raw / 4095) * 3.3

# RP2040
from machine import ADC
adc = ADC(26)  # GP26 = ADC0, sin Pin() wrapper
raw = adc.read_u16()  # 0-65535
voltage = (raw / 65535) * 3.3
```

---

## 🚀 Uso (Thonny o Pymakr)

### Opción 1: Thonny (Recomendado)
1. Abre **Thonny IDE**
2. Conecta el Pico, selecciona intérprete: `MicroPython (Raspberry Pi Pico)`
3. Abre `main.py` desde `MicroPython/RP2040/P3`
4. Guarda en el Pico: **File > Save as... > Raspberry Pi Pico**
5. Presiona **F5** para ejecutar

### Opción 2: VS Code + Pymakr
1. Abre `MicroPython/RP2040/P3` en VS Code
2. Conecta el Pico, selecciona puerto en Pymakr y **Connect**
3. **Sync project** para subir archivos
4. **Run** o reinicia la placa

### Interacción en REPL
1. El menú aparece automáticamente después de `boot.py`
2. Elige modo (`1`-`5`) y presiona **ENTER**
3. Espera 6 segundos para modo por defecto (3: Temperatura)
4. Escribe `m` + **ENTER** en cualquier momento para volver al menú

---

## 🎮 Modos de Operación

| Modo | Nombre              | Descripción                                        | Salida Ejemplo                     |
|-----:|---------------------|----------------------------------------------------|-------------------------------------|
| **1** | ADC crudo          | Muestra valor ADC y voltaje de nodo                | `adc=32768, V=1.650`                |
| **2** | Resistencia        | Calcula resistencia de la NTC                      | `adc=32768, V=1.650, Rntc=10000Ω`  |
| **3** | Temperatura        | Calcula temperatura en °C (ecuación Beta)          | `V=1.650V, Rntc=10000Ω, T=25.00°C` |
| **4** | Monitor CSV        | Salida continua para graficar                      | `t_ms,adc,v_node_v,r_ntc_ohm,t_c`  |
| **5** | Calibración        | Asistente interactivo para calibrar ADC            | Guarda `calibration.json`           |

### Modo 3: Temperatura (Por defecto)
```
[Modo 3] Temperatura (°C) — Beta=3950, R0=10000Ω
V=1.650V, Rntc=10000Ω, T=25.12°C
V=1.655V, Rntc=10200Ω, T=24.50°C
V=1.620V, Rntc=9500Ω, T=26.80°C
```

### Modo 4: Monitor CSV
```
t_ms,adc,v_node_v,r_ntc_ohm,t_c
0,32768,1.6500,10000.0,25.12
200,32850,1.6550,10200.0,24.50
400,32250,1.6200,9500.0,26.80
```

**Ideal para**:
- Copiar/pegar en Excel o LibreOffice Calc
- Graficar con Python (Matplotlib, Pandas)
- Analizar dinámica de calentamiento/enfriamiento

---

## ⚙️ Parámetros Ajustables (en `main.py`)

```python
# Líneas 72-79
ADC_PIN = 26         # GP26 (ADC0), cambia a 27 o 28 si usas otros pines
SAMPLES = 16         # Promedio por lectura (reduce ruido)

V_SUPPLY = 3.3       # Voltaje real medido con multímetro
R_SERIES = 10000.0   # Resistencia serie en ohmios
NTC_R0 = 10000.0     # Resistencia NTC @ 25°C
NTC_BETA = 3950.0    # Beta típica (ver datasheet NTC)
T0_K = 273.15 + 25.0 # Temperatura de referencia (25°C)
```

**Recomendación**: Mide `V_SUPPLY` con multímetro y actualiza el valor para mayor precisión.

---

## ✅ Verificación

### Test Básico
1. **Temperatura ambiente**: A 20-30°C, `T` debe estar cerca de esa referencia
2. **Calentamiento**: Toca la NTC con los dedos → `T` sube 2-5°C
3. **Enfriamiento**: Suelta la NTC → `T` baja gradualmente
4. **Rango ADC**: Con divisor 50/50, debe leer ~32000 (mitad de 65535)

### Valores Esperados (25°C, R_SERIES = NTC = 10kΩ)

| Variable        | Valor Esperado | Rango Normal    |
|-----------------|----------------|-----------------|
| ADC (raw)       | ~32768         | 30000-35000     |
| Voltaje (nodo)  | ~1.65V         | 1.5-1.7V        |
| Resistencia NTC | ~10kΩ          | 9-11kΩ          |
| Temperatura     | ~25°C          | 20-30°C         |

### Troubleshooting

| Problema                  | Causa Probable                    | Solución                                    |
|---------------------------|-----------------------------------|---------------------------------------------|
| ADC siempre 0             | Conexión GP26 suelta/incorrecta   | Verifica cableado en Pin 31                 |
| ADC siempre 65535         | Cortocircuito a 3V3               | Verifica que NTC esté conectado a GND       |
| Temperatura muy baja      | R_SERIES incorrecto               | Mide resistencia real con multímetro        |
| Temperatura muy alta      | NTC en corto o mal valor Beta     | Verifica NTC con multímetro, ajusta Beta    |
| Ruido excesivo            | Poca estabilidad eléctrica        | Aumenta `SAMPLES` a 32 o 64                 |
| Error "ADC no inicializado" | Ejecutando en PC                 | Normal, ejecutar en Pico                    |

---

## 📊 Visualización de Datos

### Captura CSV desde REPL
1. Ejecuta **Modo 4** (Monitor CSV)
2. Deja correr 30-60 segundos
3. Copia toda la salida del REPL
4. Pega en archivo `datos.csv`

### Graficar con Python (ejemplo)
```python
import pandas as pd
import matplotlib.pyplot as plt

# Cargar datos
df = pd.read_csv('datos.csv')

# Graficar temperatura vs tiempo
plt.figure(figsize=(10, 6))
plt.plot(df['t_ms']/1000, df['t_c'], label='Temperatura (°C)')
plt.xlabel('Tiempo (s)')
plt.ylabel('Temperatura (°C)')
plt.title('Respuesta Térmica de NTC')
plt.grid(True)
plt.legend()
plt.show()
```

### Graficar en Excel
1. Abre Excel, **Datos > Desde texto/CSV**
2. Selecciona `datos.csv`, importa
3. Selecciona columnas `t_ms` y `t_c`
4. **Insertar > Gráfico de líneas**

**Ver más detalles**: [`docs/oscilograma.md`](./docs/oscilograma.md)

---

## 🔧 Calibración ADC (Opcional)

### ¿Por qué calibrar?
- El ADC de RP2040 es más lineal que ESP32, pero puede tener offset
- Útil si observas error sistemático (ej: siempre +0.2°C)
- Mejora precisión cerca de 0V y 3.3V

### Procedimiento (Modo 5)
1. Ejecuta `main.py`, selecciona **Modo 5**
2. **Paso 1**: 
   - Desconecta NTC y R_SERIES temporalmente
   - Conecta **GP26 directamente a GND**
   - Escribe `ok` + ENTER en REPL
   - Se mide valor LOW (~0)
3. **Paso 2**:
   - Desconecta GP26 de GND
   - Conecta **GP26 directamente a 3V3**
   - Escribe `ok` + ENTER
   - Se mide valor HIGH (~65535)
4. Se guarda `calibration.json` en el Pico

### Activar Calibración
```python
# En main.py, línea ~87:
AUTO_USE_CALIBRATION = True  # Cambiar de False a True
```

**Nota**: La calibración NO se aplica automáticamente para evitar confusiones. Actívala solo si la necesitas.

---

## ⚠️ Notas y Limitaciones

### ADC del RP2040
- **Mayor linealidad** que ESP32 (no requiere calibración compleja)
- **Sin atenuación**: Solo 0-3.3V, NO CONECTES 5V
- **3 canales**: GP26, GP27, GP28 (vs 18 en ESP32)
- **Resolución efectiva**: ~12-bit real, padding a 16-bit

### Precisión de Temperatura
- **Sin calibración**: ±2-3°C (depende de Beta y tolerancia de R_SERIES)
- **Con calibración**: ±0.5-1°C (mejora offset/ganancia)
- **Error de Beta**: Si Beta real ≠ 3950, ajusta `NTC_BETA` en `main.py`
- **Autocalentamiento**: NTC en corriente alta puede elevar 0.1-0.5°C

### Recomendaciones
1. **Mide voltajes reales** con multímetro antes de confiar en cálculos
2. **Usa R_SERIES de 1%** para mejor precisión
3. **Verifica Beta de tu NTC** en el datasheet (puede ser 3900-4100)
4. **Aísla la NTC** de corrientes de aire para mediciones estables

---

## 📚 Recursos

### Documentación Oficial
- **MicroPython RP2040 ADC**: https://docs.micropython.org/en/latest/rp2/quickref.html#adc-analog-to-digital-conversion
- **Pico Getting Started**: https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html
- **RP2040 Datasheet** (ADC section): https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf#page=565

### Teoría NTC
- **Ecuación Beta**: Modelo simplificado para NTC (precisión ±2°C)
- **Steinhart-Hart**: Modelo avanzado (precisión ±0.1°C, requiere 3 coeficientes)
- **Referencia general**: [Wikipedia - Thermistor](https://en.wikipedia.org/wiki/Thermistor)

### Herramientas
- **Thonny IDE**: https://thonny.org
- **Matplotlib** (graficar): `pip install matplotlib pandas`
- **Fritzing** (diagramas): https://fritzing.org

---

## 🎓 Expansiones Sugeridas

1. **Múltiples sensores**: Usa GP27 (ADC1) y GP28 (ADC2) para 3 NTCs simultáneas
2. **Alarma térmica**: Añade LED/buzzer cuando T > umbral
3. **Display OLED**: Muestra temperatura en pantalla I2C (SSD1306)
4. **Datalogging**: Guarda CSV en archivo con `uos` y `open()`
5. **WiFi** (Pico W): Envía datos a ThingSpeak o servidor web
6. **Steinhart-Hart**: Implementa ecuación de 3 parámetros para ±0.1°C

---

## 📄 Archivos del Proyecto

```
P3/
├── README.md           ← Este archivo (instrucciones completas)
├── PINES.md            ← Mapa detallado de pines y cálculos
├── boot.py             ← Inicialización (banner de arranque)
├── main.py             ← Programa principal (5 modos)
├── pymakr.conf         ← Configuración Pymakr (VS Code)
├── assets/
│   └── wiring.mmd      ← Diagrama Mermaid editable
└── docs/
    └── oscilograma.md  ← Guía de visualización CSV
```

---

## 🤝 Créditos

- **Proyecto**: SISELA-Init (EU97)
- **Plataforma**: RP2040 (Raspberry Pi Pico)
- **MicroPython**: v1.24+
- **Traducción**: ESP32 → RP2040 (Noviembre 2025)

---

## 📞 Soporte

- **Issues**: https://github.com/EU97/SISELA-Init/issues
- **Comparativa ESP32**: Ver carpeta `../ESP32/P3/`
- **Documentación RP2040**: Ver archivos `.md` en esta carpeta

---

**Última actualización**: 2025-11-03  
**Versión**: 1.0  
**Estado**: ✅ Funcional (traducción completa de ESP32)

---

¡Disfruta midiendo temperaturas con tu Raspberry Pi Pico! 🌡️🚀
