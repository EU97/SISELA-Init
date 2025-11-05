# Actualización P3: Soporte para LM35

**Fecha:** 2025-11-04  
**Práctica:** P3 - Sensor de Temperatura

## 🎯 Objetivo

Ampliar la práctica 3 para soportar **dos tipos de sensores de temperatura** con menú de selección:
1. **NTC Termistor** (10kΩ, Beta=3950) - sensor no lineal
2. **LM35** (10mV/°C) - sensor lineal

## ✨ Cambios Implementados

### 1. Menú de Selección de Sensor

Al iniciar P3, el usuario elige el tipo de sensor:

```
=== Seleccionar Tipo de Sensor ===
1) NTC Termistor (10kΩ, Beta=3950)
2) LM35 (Sensor lineal 10mV/°C)

Escribe 1 o 2 y ENTER. Default: 1 en 5s
```

- **Timeout**: 5 segundos
- **Default**: NTC (opción 1)
- **Variable global**: `sensorType` (1=NTC, 2=LM35)

### 2. Sensor NTC (Opción 1) - Comportamiento Original

**Hardware:**
- Divisor resistivo: `3V3 → R_series 10kΩ → [ADC] → NTC 10kΩ → GND`

**Conversión matemática:**
1. ADC → Voltaje (normalizado por plataforma)
2. `R_NTC = R_series × V_nodo / (V_supply - V_nodo)`
3. `1/T = 1/T0 + (1/β) × ln(R/R0)` (ecuación Beta)

**Parámetros:**
- R0 = 10kΩ @ 25°C
- Beta = 3950
- V_SUPPLY = 3.3V
- R_SERIES = 10kΩ

**3 Modos NTC:**
1. ADC crudo + Voltaje nodo
2. ADC + Voltaje + Resistencia NTC (Ω)
3. ADC + Voltaje + Resistencia + Temperatura (°C)

### 3. Sensor LM35 (Opción 2) - NUEVO

**Hardware:**
- Conexión directa: `LM35 Vout → [ADC]`
- Alimentación LM35: Vs = 3.3V o 5V (5V recomendado)

**Conversión matemática:**
- Lineal directa: `T(°C) = Voltaje(V) × 100`
- Fundamento: LM35 entrega 10mV/°C = 0.01V/°C
- Ejemplo: 0.25V = 25°C, 0.50V = 50°C

**Parámetros LM35:**
- Sensibilidad: 10mV/°C
- Rango típico: 0-100°C (LM35DZ)
- Rango extendido: -55°C a +150°C (otras versiones)

**2 Modos LM35:**
1. ADC crudo + Voltaje
2. ADC + Voltaje + Temperatura (°C)

**Nota importante:** El modo "resistencia" no aplica para LM35 (es un sensor de voltaje directo).

### 4. Función Nueva: `lm35_voltage_to_temp_c()`

```cpp
float lm35_voltage_to_temp_c(float voltage) {
    return voltage * 100.0;  // 10mV/°C = 0.01V/°C → V * 100 = °C
}
```

Conversión directa sin necesidad de cálculos complejos.

### 5. Lógica Adaptativa en `loop()`

El código ahora bifurca según `sensorType`:

**Para NTC (`sensorType == 1`):**
```cpp
if (mode >= 2) {
    float r_ntc = voltage_to_ntc_res(voltage);
    // Mostrar resistencia...
    if (mode >= 3) {
        float temp_c = ntc_res_to_temp_c(r_ntc);
        // Mostrar temperatura...
    }
}
```

**Para LM35 (`sensorType == 2`):**
```cpp
if (mode >= 2) {
    float temp_c = lm35_voltage_to_temp_c(voltage);
    // Mostrar temperatura directamente (sin resistencia)
}
```

## 📊 Comparativa de Sensores

| Aspecto | NTC Termistor | LM35 |
|---------|---------------|------|
| **Tipo** | Pasivo (resistencia variable) | Activo (salida de voltaje) |
| **Circuito** | Divisor resistivo requerido | Conexión directa a ADC |
| **Conversión** | No lineal (ecuación Beta) | Lineal (10mV/°C) |
| **Rango típico** | -40°C a +125°C | 0-100°C (DZ) |
| **Precisión** | ±1-2°C (depende calibración) | ±0.5°C típico |
| **Costo** | ~$0.10 USD | ~$1.50 USD |
| **Alimentación** | Pasivo (solo divisor) | Requiere Vs (4-30V) |
| **Complejidad SW** | Alta (logaritmos, Beta) | Baja (multiplicación) |
| **Mejor para** | DIY, bajo costo, baterías | Precisión, facilidad |

## 🔌 Conexiones Hardware

### Opción 1: NTC Termistor
```
ESP32/RP2040
   3.3V ────┬──── R_series (10kΩ)
            │
            ├──── GPIO34/GP26 (ADC)
            │
            └──── NTC (10kΩ @ 25°C)
                  │
                 GND
```

### Opción 2: LM35
```
ESP32/RP2040
   3.3V* ──── LM35 Vs (pin 1)
                │
   GPIO34 ──── LM35 Vout (pin 2)
                │
   GND ─────── LM35 GND (pin 3)

* Recomendado: 5V para máxima precisión
  Si usa 5V, considerar divisor resistivo para proteger ADC (3.3V max)
```

**Nota sobre 5V:**
- LM35 funciona con 3.3V pero pierde precisión
- Para usar 5V con ESP32/RP2040:
  - Alimentar LM35 con 5V
  - Agregar divisor resistivo 2:1 en Vout antes del ADC
  - O usar diodo Zener 3.3V

## 🧪 Testing

### Test NTC (Opción 1)
```
1. Compilar con -DPRACTICE=3
2. Flashear y abrir monitor serial
3. Seleccionar "1" (NTC)
4. Seleccionar modo 3 (temperatura)
5. Verificar lectura ~25°C a temperatura ambiente
6. Calentar NTC con dedos → debe aumentar a ~30-35°C
7. Enfriar con hielo → debe bajar a ~5-10°C
```

### Test LM35 (Opción 2)
```
1. Compilar con -DPRACTICE=3
2. Flashear y abrir monitor serial
3. Seleccionar "2" (LM35)
4. Seleccionar modo 2 (temperatura)
5. Verificar lectura ~25°C a temperatura ambiente
6. Tocar sensor con dedos → debe aumentar a ~30-35°C
7. Soplar aire frío → debe bajar a ~20-22°C
```

### Validación de Conversión LM35
```
Voltaje (V) | Temp esperada (°C) | Fórmula
------------|-------------------|-------------
0.00        | 0°C               | 0.00 × 100
0.15        | 15°C              | 0.15 × 100
0.25        | 25°C              | 0.25 × 100
0.37        | 37°C (corporal)   | 0.37 × 100
1.00        | 100°C (agua)      | 1.00 × 100
```

## 📝 Archivos Modificados

1. **`src/practices/p3.cpp`**:
   - Agregado `sensorType` y `LM35_MV_PER_C`
   - Función `lm35_voltage_to_temp_c()`
   - Menú de selección en `setup()`
   - Lógica bifurcada en `loop()`

2. **`README.md`**:
   - Actualizada tabla de prácticas
   - Sección P3 expandida con ambos sensores

3. **`IMPLEMENTATION_STATUS.md`**:
   - Actualizada documentación técnica P3

## 🎓 Justificación Pedagógica

Esta actualización tiene valor educativo:

1. **Contraste de sensores**: Los estudiantes experimentan la diferencia entre sensores pasivos (NTC) y activos (LM35)
2. **Complejidad matemática**: NTC requiere logaritmos y ecuación Beta; LM35 es una simple multiplicación
3. **Trade-offs de diseño**: Costo vs precisión vs facilidad de implementación
4. **Flexibilidad**: Un mismo código soporta múltiples configuraciones de hardware

## 🚀 Posibles Extensiones Futuras

- [ ] Agregar DS18B20 (sensor digital 1-Wire)
- [ ] Agregar DHT11/DHT22 (temperatura + humedad)
- [ ] Modo de comparación: mostrar ambos sensores simultáneamente
- [ ] Calibración interactiva con puntos de referencia (hielo, agua hirviendo)
- [ ] Logging CSV con timestamp para análisis térmico
- [ ] Alarmas configurables por temperatura (ej: >40°C)

## 🔗 Referencias

- [LM35 Datasheet (Texas Instruments)](https://www.ti.com/lit/ds/symlink/lm35.pdf)
- [NTC Thermistor Beta Equation](https://en.wikipedia.org/wiki/Thermistor#B_or_%CE%B2_parameter_equation)
- [Comparing Temperature Sensors](https://www.analogictips.com/temperature-sensor-comparison/)

---

**Commit sugerido:**  
```
feat(P3): Add LM35 temperature sensor support with menu selection

- Add sensor type selection menu (NTC/LM35) with 5s timeout
- Implement lm35_voltage_to_temp_c() for linear conversion
- Adapt modes: 3 for NTC, 2 for LM35 (no resistance mode)
- Update documentation (README.md, IMPLEMENTATION_STATUS.md)
- Add CHANGELOG_P3_LM35.md with testing guide
```

**Autor:** GitHub Copilot  
**Fecha:** 2025-11-04
