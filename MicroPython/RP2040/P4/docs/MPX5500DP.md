# MPX5500DP — Sensor de Presión Absoluta Piezoresistivo (RP2040)

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

## 🔄 Ventajas con RP2040

| Aspecto | ESP32 | RP2040 | Ventaja |
|---------|-------|--------|---------|
| **Resolución ADC** | 12 bits (0–4095) | **16 bits (0–65535)** | 16× más resolución |
| **Error ADC** | ±5% típico | **±1% típico** | Mejor linealidad |
| **Resolución presión** | ~0.12 kPa/bit | **~0.0076 kPa/bit** | Detecta cambios más pequeños |
| **Alimentación 5V** | Requiere divisor externo | **VSYS disponible directamente** | Simplifica circuito |

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
- **Recomendación**: Usar VSYS (5V del USB) con divisor resistivo 10kΩ+10kΩ para proteger ADC del RP2040 (máx 3.3V).

## Conexión con RP2040 ADC

### Opción 1: Alimentación 3.3V (simple, menor precisión)

```
MPX5500DP          RP2040 (Pico)
Pin 1 (GND)   →    GND
Pin 2 (VS)    →    3V3(OUT)
Pin 3 (Vout)  →    GP26 (ADC0)
```

**ADC config**: 16-bit, 0–3.3V (sin configuración adicional)

**Ventaja RP2040**: ADC más lineal que ESP32, menor error incluso a VS=3.3V.

### Opción 2: Alimentación 5V (recomendado, máxima precisión)

```
MPX5500DP          Divisor          RP2040 (Pico)
Pin 1 (GND)   →                →    GND
Pin 2 (VS)    →    VSYS (5V USB)
Pin 3 (Vout)  →    R1 (10kΩ)    →   GP26 (ADC0)
                   R2 (10kΩ)    →   GND
```

**Divisor**: Reduce Vout de 4.5V máx a 2.25V máx (protege ADC).

**ADC config**: 16-bit, 0–3.3V

**Ventaja**: Máxima sensibilidad del sensor + máxima resolución del RP2040.

## Consideraciones de diseño específicas para RP2040

### 1. Filtrado de alimentación

Agregar **condensador cerámico 0.1 µF** entre VS y GND (lo más cerca posible del sensor) para filtrar ruido de alta frecuencia.

**Adicional para RP2040**: Condensador de 10 µF en VSYS si se usa alimentación 5V.

### 2. Ruido ADC (RP2040 ventaja)

El ADC del RP2040 tiene **±1% de error** (mejor que ESP32 ±5%). Mitigación adicional:
- Promedio de múltiples lecturas (20–50 muestras, menos que ESP32).
- Calibración de dos puntos (GND y 3V3) — **más efectiva** que en ESP32.
- Usar GP26-GP28 (canales ADC dedicados).

**Comparativa de ruido**:
```
ESP32:  σ ≈ 10 LSB (12-bit) → ~8 mV → ~1.0 kPa
RP2040: σ ≈ 2 LSB (16-bit) → ~0.1 mV → ~0.13 kPa  ✅ 8× mejor
```

### 3. Temperatura

El sensor tiene deriva térmica de **±1% FS** (-40°C a +125°C). Para aplicaciones críticas, implementar compensación térmica con sensor de temperatura externo.

**Ventaja RP2040**: La mayor resolución permite detectar deriva <0.5% más fácilmente.

### 4. Presión diferencial vs absoluta

El MPX5500DP mide **presión absoluta** (referencia: vacío). No tiene puerto de referencia (presión ambiente). Para presión diferencial, usar la serie **MPX5500D** (con puerto de referencia).

## Aplicaciones típicas optimizadas para RP2040

| Aplicación | Resolución requerida | RP2040 ventaja |
|------------|----------------------|----------------|
| **Altímetro preciso** | <1m vertical | ✅ 16-bit detecta 0.012 kPa (1m) |
| **Monitor respiración** | <0.2 kPa | ✅ Ruido bajo permite detección |
| **Control neumático** | <0.5 kPa | ✅ Respuesta rápida sin filtrado |
| **Barómetro meteorológico** | <0.1 kPa | ✅ Resolución científica |
| **Muestreo rápido >100Hz** | Sin degradación SNR | ✅ ADC más rápido |

## Cálculo de resolución teórica

### ESP32 (12 bits)
```python
# Rango 20-520 kPa, VS=3.3V, Vout=0.66-2.1V
resolution_v = 3.3 / 4095  # 0.806 mV/bit
resolution_kpa_esp32 = (520 - 20) / 4095  # ~0.122 kPa/bit
```

### RP2040 (16 bits)
```python
# Rango 20-520 kPa, VS=3.3V, Vout=0.66-2.1V  
resolution_v = 3.3 / 65535  # 0.050 mV/bit (16× mejor)
resolution_kpa_rp2040 = (520 - 20) / 65535  # ~0.0076 kPa/bit ✅

# Equivale a ~0.08m de altitud (presión atmosférica)
```

## Altimetría de alta precisión con RP2040

La resolución de 16 bits permite altimetría **submetro**:

```python
def altitude_resolution_analysis():
    """Calcula resolución vertical del RP2040 + MPX5500DP."""
    
    # Presión atmosférica estándar
    P0 = 101.325  # kPa (nivel del mar)
    
    # Cambio de presión por metro de altitud (aproximado)
    dP_dh = -0.012  # kPa/m
    
    # Resolución ADC RP2040
    adc_resolution_kpa = 0.0076  # kPa/bit
    
    # Resolución vertical
    altitude_resolution = abs(adc_resolution_kpa / dP_dh)
    
    print(f"Resolución vertical teórica: {altitude_resolution:.2f} m")
    # Resultado: ~0.63 m (submetro) ✅
    
    # ESP32 para comparación
    adc_resolution_kpa_esp32 = 0.122  # kPa/bit
    altitude_resolution_esp32 = abs(adc_resolution_kpa_esp32 / dP_dh)
    print(f"ESP32 resolución vertical: {altitude_resolution_esp32:.2f} m")
    # Resultado: ~10 m (orden de magnitud peor)
```

## Limitaciones

- **No apto para líquidos corrosivos**: El diafragma de silicio es sensible a ácidos/bases.
- **Sobrepresión**: Máx 1.75× FS (910 kPa) sin daño permanente. Evitar sobrepasar.
- **Respuesta de frecuencia**: ~1 kHz BW. No apto para mediciones ultrasónicas (pero RP2040 puede samplear a esta tasa).

## Referencias

- **Datasheet oficial (NXP)**: https://www.nxp.com/docs/en/data-sheet/MPX5500.pdf
- **Application Note AN1646**: Piezoresistive Pressure Sensor Interfacing
- **RP2040 Datasheet**: https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf (Sección 4.9 ADC)
- **MicroPython RP2040 ADC**: https://docs.micropython.org/en/latest/rp2/quickref.html#adc-analog-to-digital-conversion
