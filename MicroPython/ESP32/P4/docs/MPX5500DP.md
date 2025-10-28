# MPX5500DP — Sensor de Presión Absoluta Piezoresistivo

## Resumen

| Parámetro | Valor |
|-----------|-------|
| **Fabricante** | Freescale Semiconductor / NXP |
| **Tipo** | Sensor de presión absoluta piezoresistivo |
| **Rango** | 20 kPa – 520 kPa (2.9 – 75 psi) |
| **Package** | SOT-223 (3 pines) |
| **Alimentación (VS)** | 4.75V – 5.25V (nominal 5V) |
| **Salida (Vout)** | Analógica proporcional a presión |
| **Sensibilidad** | ~4.5 mV/kPa @ VS=5V |
| **Offset** | ~0.2 × VS (1V @ VS=5V) |
| **Temperatura operativa** | -40°C a +125°C |
| **Coeficiente térmico** | ±1% FS (Full Scale) |

## Principio de operación

El MPX5500DP utiliza tecnología **piezoresistiva** basada en un diafragma de silicio con resistencias difundidas. Cuando la presión aplicada deforma el diafragma, las resistencias cambian su valor, produciendo un voltaje de salida proporcional mediante un puente de Wheatstone integrado.

### Función de transferencia

$$
V_{out} = V_S \times (0.2 \times P + 0.2)
$$

Donde:
- $V_{out}$: Voltaje de salida (V)
- $V_S$: Voltaje de alimentación (V, nominal 5V)
- $P$: Presión aplicada (kPa), normalizada como $P_{norm} = \frac{P - 20}{500}$ (rango 0–1 para 20–520 kPa)

**Simplificada para presión absoluta:**

$$
P(kPa) = \frac{V_{out} - 0.2 \times V_S}{0.2 \times V_S} \times 500 + 20
$$

O, reorganizando:

$$
P(kPa) = \frac{V_{out} - V_{min}}{Sensibilidad} + P_{min}
$$

Donde:
- $V_{min} = 0.2 \times V_S$ (offset a presión mínima)
- $Sensibilidad = \frac{V_{max} - V_{min}}{P_{max} - P_{min}} \approx 0.0053$ V/kPa @ VS=5V

## Pinout (SOT-223)

```
Vista frontal (cara con marcado):

 ┌─────────┐
 │    1    │  GND (tierra)
 │    2    │  VS (alimentación, 4.75–5.25V)
 │    3    │  Vout (salida analógica)
 └─────────┘
     TAB: GND (conectado internamente a pin 1)
```

## Características eléctricas (VS = 5V, 25°C)

| Parámetro | Mín | Típico | Máx | Unidad |
|-----------|-----|--------|-----|--------|
| Voltaje de alimentación (VS) | 4.75 | 5.0 | 5.25 | V |
| Consumo de corriente | — | 7 | 10 | mA |
| Salida a 20 kPa (Vmin) | 0.90 | 1.00 | 1.10 | V |
| Salida a 520 kPa (Vmax) | 4.40 | 4.50 | 4.60 | V |
| Sensibilidad | 4.0 | 4.5 | 5.0 | mV/kPa |
| Linealidad | — | ±0.25 | ±1.0 | % FS |
| Histéresis | — | ±0.1 | ±0.2 | % FS |
| Impedancia de salida | — | 1.4 | 2.0 | kΩ |

## Operación con VS = 3.3V (no estándar)

El sensor **puede funcionar** con VS=3.3V pero fuera de especificaciones:

- **Sensibilidad reducida**: ~66% del nominal (≈3.0 mV/kPa).
- **Rango de salida**: ~0.66V (20 kPa) a ~2.1V (520 kPa).
- **Precisión**: Mayor error (±2–3% FS estimado).
- **Recomendación**: Usar VS=5V con divisor resistivo 10kΩ+10kΩ para proteger ADC del ESP32 (máx 3.3V).

## Conexión con ESP32 ADC

### Opción 1: Alimentación 3.3V (simple, menor precisión)

```
MPX5500DP          ESP32
Pin 1 (GND)   →    GND
Pin 2 (VS)    →    3V3
Pin 3 (Vout)  →    GPIO34 (ADC1_CH6)
```

**ADC config**: 12-bit, ATTN_11DB (0–3.3V)

### Opción 2: Alimentación 5V (recomendado, máxima precisión)

```
MPX5500DP          Divisor          ESP32
Pin 1 (GND)   →                →    GND
Pin 2 (VS)    →    5V (regulado)
Pin 3 (Vout)  →    R1 (10kΩ)    →   GPIO34
                   R2 (10kΩ)    →   GND
```

**Divisor**: Reduce Vout de 4.5V máx a 2.25V máx (protege ADC).

**ADC config**: 12-bit, ATTN_11DB (0–3.3V)

## Consideraciones de diseño

### 1. Filtrado de alimentación

Agregar **condensador cerámico 0.1 µF** entre VS y GND (lo más cerca posible del sensor) para filtrar ruido de alta frecuencia.

### 2. Ruido ADC

El ADC del ESP32 tiene **±5% de error** y no linealidad. Mitigación:
- Promedio de múltiples lecturas (50–100 muestras).
- Calibración de dos puntos (GND y 3V3).
- Usar ADC1 (más estable que ADC2).

### 3. Temperatura

El sensor tiene deriva térmica de **±1% FS** (-40°C a +125°C). Para aplicaciones críticas, implementar compensación térmica con sensor de temperatura externo.

### 4. Presión diferencial vs absoluta

El MPX5500DP mide **presión absoluta** (referencia: vacío). No tiene puerto de referencia (presión ambiente). Para presión diferencial, usar la serie **MPX5500D** (con puerto de referencia).

## Aplicaciones típicas

- Altimetría (aviación, drones).
- Control de motores (MAP sensor).
- Sistemas neumáticos industriales.
- Meteorología (barómetros).
- Sistemas HVAC (climatización).

## Limitaciones

- **No apto para líquidos corrosivos**: El diafragma de silicio es sensible a ácidos/bases.
- **Sobrepresión**: Máx 1.75× FS (910 kPa) sin daño permanente. Evitar sobrepasar.
- **Respuesta de frecuencia**: ~1 kHz BW. No apto para mediciones ultrasónicas.

## Referencias

- **Datasheet oficial (NXP)**: https://www.nxp.com/docs/en/data-sheet/MPX5500.pdf
- **Application Note AN1646**: Piezoresistive Pressure Sensor Interfacing
- **ESP32 ADC Calibration**: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/adc.html

## Ejemplo de código (conversión básica)

```python
# Parámetros (VS = 3.3V)
V_SUPPLY = 3.3
P_MIN = 20.0
P_MAX = 520.0
VOUT_MIN = 0.2 * V_SUPPLY  # 0.66V
VOUT_MAX = 1.0 * V_SUPPLY  # 3.3V
SENSITIVITY = (VOUT_MAX - VOUT_MIN) / (P_MAX - P_MIN)

def voltage_to_pressure(v):
    """Convierte voltaje del sensor a presión (kPa)."""
    if v < VOUT_MIN:
        return P_MIN
    if v > VOUT_MAX:
        return P_MAX
    return ((v - VOUT_MIN) / SENSITIVITY) + P_MIN

# Ejemplo:
adc_value = 2048  # Lectura ADC de 12 bits
voltage = (adc_value / 4095.0) * 3.3
pressure = voltage_to_pressure(voltage)
print(f"Presión: {pressure:.2f} kPa")
```

## Alternativas

| Modelo | Rango | Package | Notas |
|--------|-------|---------|-------|
| **MPX5100DP** | 0–100 kPa | SOT-223 | Presión absoluta, rango bajo |
| **MPX5700DP** | 20–700 kPa | SOT-223 | Mayor rango que MPX5500DP |
| **BMP280** | 30–110 kPa | Digital I2C/SPI | Barómetro digital con temperatura |
| **MS5611** | 10–120 kPa | Digital I2C/SPI | Alta precisión (±1.5 mbar) |
