# P3 — Visualización de datos (NTC) — RP2040

Esta práctica emite datos en distintos modos. Úsalos para verificar forma y estabilidad de la medida.

---

## CSV en modo 4

### Cabecera y ejemplo:
```csv
t_ms,adc,v_node_v,r_ntc_ohm,t_c
12,32768,1.6500,10000.0,25.12
215,32850,1.6550,10200.0,24.50
420,32250,1.6200,9500.0,26.80
```

### Campos:
- **`t_ms`**: Tiempo relativo desde el arranque del modo (milisegundos)
- **`adc`**: Lectura promedio ADC (0-65535, 16-bit)
- **`v_node_v`**: Tensión en el nodo del divisor (voltios)
- **`r_ntc_ohm`**: Resistencia estimada de la NTC (ohmios)
- **`t_c`**: Temperatura estimada (°C) usando ecuación Beta

---

## Diferencias vs ESP32

| Aspecto            | ESP32             | RP2040            |
|--------------------|-------------------|-------------------|
| **Rango ADC**      | 0-4095 (12-bit)   | 0-65535 (16-bit)  |
| **Resolución real**| ~8-10 bits efectivos | ~12 bits efectivos|
| **Linealidad**     | Baja (no lineal)  | Alta (más lineal) |
| **Ruido típico**   | ±50-100 cuentas   | ±20-50 cuentas    |

---

## Observaciones típicas

### 🔥 Calentamiento (tocar NTC con dedos)
- **Resistencia NTC** ↓ (disminuye)
- **Voltaje nodo** ↑ (aumenta)
- **Temperatura** ↑ (sube 2-5°C)
- **Tiempo de respuesta**: 1-3 segundos

### ❄️ Enfriamiento (soltar NTC)
- **Resistencia NTC** ↑ (aumenta)
- **Voltaje nodo** ↓ (disminuye)  
- **Temperatura** ↓ (baja gradualmente)
- **Tiempo de respuesta**: 5-15 segundos

### 📊 Ruido
- **Sin filtro**: ±0.1-0.3°C variación
- **Con SAMPLES=16**: ±0.05-0.1°C variación
- **Con SAMPLES=64**: ±0.02-0.05°C variación

---

## Consejos de medida

### ✅ Mejores prácticas

1. **Calibración de referencia**:
   - Mide temperatura ambiente con termómetro de referencia
   - Compara con lectura NTC en reposo (sin tocar)
   - Ajusta `NTC_BETA` si hay offset consistente

2. **Ajuste de voltaje**:
   - Mide `3V3` real con multímetro (suele ser 3.27-3.33V)
   - Actualiza `V_SUPPLY` en `main.py` línea 77

3. **Verificación de resistencias**:
   - Mide `R_SERIES` con multímetro (puede ser 9.8-10.2kΩ)
   - Actualiza `R_SERIES` si difiere

4. **Reducción de ruido**:
   - Usa cables cortos (<15cm) para conexión ADC
   - Evita cerca de motores, WiFi, o fuentes PWM
   - Aumenta `SAMPLES` a 32 o 64 si necesitas más estabilidad

5. **Aislamiento térmico**:
   - Aleja NTC de corrientes de aire
   - Espera 30-60s para estabilización tras cambios
   - Usa cinta aislante para fijar NTC al objeto a medir

---

## Formas de onda esperadas

### Calentamiento súbito (tocar con dedos)
```
T(°C)
30 │                    ┌─────
   │                 ┌──┘
25 │──────────────┌──┘
   │              
20 └──────────────────────────► t(s)
   0     5    10    15    20
```
- **Fase 1** (0-10s): Temperatura estable ~25°C
- **Fase 2** (10-12s): Subida rápida (+3°C en 2s)
- **Fase 3** (12-20s): Estabilización en ~28°C

### Enfriamiento gradual
```
T(°C)
28 │──────┐
   │      └──┐
25 │         └────┐
   │              └─────────────
22 └──────────────────────────► t(s)
   0     5    10    15    20
```
- **Fase 1** (0-5s): Temperatura elevada ~28°C
- **Fase 2** (5-15s): Bajada exponencial
- **Fase 3** (15-20s): Convergencia a ambiente ~22°C

---

## Graficar con Matplotlib (Python)

### Script básico:
```python
import pandas as pd
import matplotlib.pyplot as plt

# Cargar CSV
df = pd.read_csv('datos_ntc.csv')

# Convertir tiempo a segundos
df['t_s'] = df['t_ms'] / 1000

# Crear figura con subplots
fig, axes = plt.subplots(2, 2, figsize=(12, 8))

# 1. Temperatura vs Tiempo
axes[0, 0].plot(df['t_s'], df['t_c'], 'r-', linewidth=2)
axes[0, 0].set_xlabel('Tiempo (s)')
axes[0, 0].set_ylabel('Temperatura (°C)')
axes[0, 0].set_title('Respuesta Térmica')
axes[0, 0].grid(True, alpha=0.3)

# 2. ADC vs Tiempo
axes[0, 1].plot(df['t_s'], df['adc'], 'b-', linewidth=1)
axes[0, 1].set_xlabel('Tiempo (s)')
axes[0, 1].set_ylabel('ADC (cuentas)')
axes[0, 1].set_title('Lectura ADC Cruda')
axes[0, 1].grid(True, alpha=0.3)

# 3. Resistencia vs Temperatura
axes[1, 0].plot(df['t_c'], df['r_ntc_ohm'], 'g.', markersize=2)
axes[1, 0].set_xlabel('Temperatura (°C)')
axes[1, 0].set_ylabel('Resistencia (Ω)')
axes[1, 0].set_title('Curva R-T de la NTC')
axes[1, 0].grid(True, alpha=0.3)

# 4. Voltaje vs Tiempo
axes[1, 1].plot(df['t_s'], df['v_node_v'], 'm-', linewidth=1)
axes[1, 1].set_xlabel('Tiempo (s)')
axes[1, 1].set_ylabel('Voltaje (V)')
axes[1, 1].set_title('Voltaje del Nodo')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('analisis_ntc.png', dpi=300)
plt.show()
```

### Ejecutar:
```bash
pip install pandas matplotlib
python graficar_ntc.py
```

---

## Graficar con Excel

### Pasos:
1. **Importar CSV**:
   - Datos > Desde texto/CSV
   - Selecciona `datos_ntc.csv`
   - Delimitador: coma

2. **Crear gráfico de temperatura**:
   - Selecciona columnas `t_ms` y `t_c`
   - Insertar > Gráfico de líneas
   - Agregar título y etiquetas de ejes

3. **Formato recomendado**:
   - Eje X: "Tiempo (ms)"
   - Eje Y: "Temperatura (°C)"
   - Línea: 2pt, color rojo
   - Cuadrícula: Activada

---

## Análisis de calidad

### Métricas esperadas (modo CSV, 60s de captura):

| Métrica                  | Valor esperado | Comentarios                       |
|--------------------------|----------------|-----------------------------------|
| **Muestras recolectadas**| ~300 (5Hz)     | Depende de `period_s` en modo 4   |
| **Desviación estándar T**| <0.2°C         | En condiciones estables           |
| **Rango T estable**      | ±0.5°C         | Sin perturbaciones                |
| **Tiempo respuesta**     | 1-3s           | 63% del cambio final              |
| **Resolución efectiva**  | 0.05-0.1°C     | Con SAMPLES=16                    |

---

## Troubleshooting

### Problema: Lecturas muy ruidosas
- **Causa**: Cables largos, interferencia EMI
- **Solución**: Acortar cables, alejar de fuentes RF/PWM, aumentar `SAMPLES`

### Problema: Offset constante (+5°C)
- **Causa**: Valor Beta incorrecto o R_SERIES no medido
- **Solución**: Medir resistencias reales, ajustar `NTC_BETA` (prueba 3900-4100)

### Problema: Temperatura no cambia al calentar
- **Causa**: NTC no conectado o en corto
- **Solución**: Medir NTC con multímetro (debe ser ~10kΩ @ 25°C)

### Problema: ADC saturado (65535 o 0)
- **Causa**: Conexión incorrecta o voltaje fuera de rango
- **Solución**: Verificar divisor resistivo, medir voltajes con multímetro

---

## Recursos adicionales

- **Datasheet NTC**: Buscar curva R-T y Beta específica
- **RP2040 ADC**: [Datasheet sección 4.9](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf#page=565)
- **Ecuación Beta**: [Wikipedia - Thermistor](https://en.wikipedia.org/wiki/Thermistor)
- **Matplotlib Gallery**: https://matplotlib.org/stable/gallery/index.html

---

**Última actualización**: 2025-11-03  
**Plataforma**: RP2040 (Raspberry Pi Pico)
