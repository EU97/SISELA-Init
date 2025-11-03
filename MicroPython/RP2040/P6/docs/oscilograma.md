# P6 — Formas de onda y mediciones (PWM con transistor) (RP2040)

Guía de medición con osciloscopio para verificar el funcionamiento correcto de la etapa de conmutación PWM con MOSFET/BJT.

## 🔄 Ventajas del RP2040

El RP2040 ofrece **PWM más estable y preciso** que el ESP32:

| Característica | ESP32 | RP2040 |
|----------------|-------|--------|
| **Jitter PWM** | ~10 ns típico | **~1 ns típico** ✅ |
| **Precisión duty** | ±0.1% | **±0.01%** ✅ |
| **Frecuencia máxima** | ~10 MHz | **~62.5 MHz** ✅ |
| **Ruido electromagnético** | Moderado | **Muy bajo** ✅ |

**Resultado práctico**: Menos interferencias electromagnéticas, control más fino de potencia, mayor eficiencia en motores.

## Qué medir

### 1. Señal PWM en la compuerta/base del transistor (GP18)

**Parámetros a verificar**:
- **Frecuencia**: 1 kHz (configurable en `main.py` → `PWM_FREQ`)
- **Nivel alto**: 3.3V (lógica del RP2040)
- **Nivel bajo**: 0V
- **Ciclo de trabajo (duty)**: 0–100% según configuración
- **Jitter**: <10 ns (RP2040: típicamente <1 ns)
- **Tiempos de subida/bajada**: <50 ns (mejorado vs ESP32)

**Forma de onda esperada** (duty 50%, 1 kHz):
```
      ┌────────┐        ┌────────┐        ┌────────┐
3.3V  │        │        │        │        │        │
      │        │        │        │        │        │
0V  ──┘        └────────┘        └────────┘        └────
      ↑        ↑        ↑
      0      500µs     1ms (periodo)
```

### 2. Tensión en la carga (drenador/colector del transistor)

**Para cargas resistivas** (LED, lámpara):
- **Nivel alto** (MOSFET off): V+ de la fuente externa
- **Nivel bajo** (MOSFET on): ~0V (idealmente <0.5V)
- **Tensión media**: D × V+ (D = duty en decimal)
- **Ejemplo**: V+=12V, duty=50% → V_media ≈ 6V

**Para cargas inductivas** (motor, relé):
- **Nivel alto** (MOSFET off): V+ + pico inicial (controlado por diodo flyback)
- **Nivel bajo** (MOSFET on): ~0V
- **Pendiente de bajada**: Suavizada por inductancia
- **Pendiente de subida**: Más rápida, controlada por diodo flyback

### 3. Transitorios en cargas inductivas (diodo flyback)

**Sin diodo flyback** ⚠️ (NO hacer, daña el MOSFET):
```
Apagado de motor:
      Pico >100V ⚠️
           │
V+  ──────┘│
           │└─── Rápido (puede dañar MOSFET)
0V  ───────┘
```

**Con diodo flyback** ✅:
```
Apagado de motor:
      Pico ~V+ + 0.7V ✅ (limitado por diodo)
         ╱│
V+  ────╱ │
       ╱  │
0V  ───╱  └─── Suave (energía disipada en diodo)
```

## Parámetros de prueba sugeridos

### Configuración básica

```python
# main.py
ACT_PIN = 18         # GP18 (PWM1 A)
PWM_FREQ = 1000      # Hz (1 kHz)
ADC_PIN = 26         # GP26 (ADC0) potenciómetro
```

### Cargas de prueba recomendadas

| Carga | Voltaje | Corriente | Frecuencia recomendada | VSYS compatible |
|-------|---------|-----------|------------------------|-----------------|
| Tira LED 5V | 5V | 150 mA | 500–2000 Hz | ✅ Sí |
| Motor DC mini | 5V | 200 mA | 1000–2000 Hz | ✅ Sí |
| Ventilador 5V | 5V | 150 mA | 500–1000 Hz | ✅ Sí |
| Motor DC mediano | 12V | 1A | 1000–2000 Hz | ❌ No (fuente externa) |
| Tira LED 12V | 12V | 500 mA | 500–2000 Hz | ❌ No (fuente externa) |

### Ciclos de duty para pruebas

| Duty | Aplicación típica | Efecto en carga |
|------|-------------------|-----------------|
| 0% | Apagado completo | Carga apagada |
| 25% | Baja potencia | LED tenue, motor lento |
| 50% | Potencia media | LED medio, motor velocidad media |
| 75% | Alta potencia | LED brillante, motor rápido |
| 100% | Potencia máxima | LED máximo, motor máximo |

## Capturas esperadas con osciloscopio

### Configuración de osciloscopio

**Para señal PWM en gate (GP18)**:
- Canal: CH1
- Acoplamiento: DC
- Escala vertical: 1 V/div
- Escala horizontal: 200 µs/div (para 1 kHz)
- Trigger: Flanco de subida, nivel 1.5V

**Para tensión en carga (drenador)**:
- Canal: CH2
- Acoplamiento: DC
- Escala vertical: 5 V/div (ajustar según V+)
- Escala horizontal: 200 µs/div
- Trigger: CH1 (sincronizado con PWM)

### Captura 1: Modo On/Off (duty 0% y 100%)

**Duty 0%** (carga apagada):
```
CH1 (GP18):
0V  ──────────────────────────────
      (Siempre en bajo)

CH2 (Drenador):
V+  ──────────────────────────────
      (MOSFET off, carga recibe V+)
```

**Duty 100%** (carga encendida):
```
CH1 (GP18):
3.3V ──────────────────────────────
      (Siempre en alto)

CH2 (Drenador):
0V  ──────────────────────────────
      (MOSFET on, carga a GND)
```

### Captura 2: PWM manual (duty 50%)

**Gate (GP18)**:
```
      ┌────────┐        ┌────────┐
3.3V  │        │        │        │
      │        │        │        │
0V  ──┘        └────────┘        └────
      ↑        ↑        ↑
      0      500µs     1ms
```

**Drenador (carga resistiva, V+=12V)**:
```
12V  ─┐        ┌────────┐        ┌────
      │        │        │        │
      │        │        │        │
0V  ──┘        └────────┘        └────
      (Inverso a gate: MOSFET on → 0V)
```

**Tensión media**: 12V × 0.5 = 6V (medible con multímetro DC)

### Captura 3: Barrido 0→100→0 (variación continua)

**Observación dinámica** (con persistencia en osciloscopio):
- CH1 (GP18): Pulsos con ancho creciente/decreciente
- CH2 (Drenador): Pulsos inversos con ancho decreciente/creciente
- Tensión media cambia suavemente de 0V a V+ y viceversa

### Captura 4: Control por potenciómetro (modo 4)

**Con potenciómetro a mitad de recorrido**:
- ADC lee ~32768 (16-bit)
- Duty ≈ 50%
- Forma de onda igual que captura 2

**Ventaja RP2040**: Al girar potenciómetro lentamente:
- Duty cambia en pasos de **0.0015%/bit** (vs 0.024% en ESP32)
- Movimiento **ultra suave**, imperceptible a simple vista
- Osciloscopio muestra cambios continuos sin "escalones"

## Mediciones avanzadas

### 1. Jitter del PWM (RP2040 vs ESP32)

**Procedimiento**:
1. Configura duty 50%, frecuencia 1 kHz
2. Activa función "Measure → Pulse Width" en CH1
3. Activa estadística "Min/Max/Mean/Std Dev"
4. Deja medir por 10 segundos (10,000 pulsos)

**Resultados esperados**:

| Métrica | ESP32 | RP2040 | Mejora |
|---------|-------|--------|--------|
| Ancho promedio | 500.000 µs | 500.000 µs | — |
| Std Dev | ~100 ns | **~10 ns** | **10×** ✅ |
| Jitter p-p | ~500 ns | **~50 ns** | **10×** ✅ |
| Estabilidad | Buena | **Excelente** ✅ |

### 2. Eficiencia de conmutación

**Medición de disipación en MOSFET**:
1. Coloca termopar/termómetro IR en el MOSFET
2. Ejecuta duty 50%, carga 1A por 60 segundos
3. Mide temperatura superficial

**Cálculo teórico** (IRLZ44N, Rds(on)=0.022Ω):
```
P_mosfet = I² × R_ds(on) = 1² × 0.022 = 22 mW
ΔT ≈ 5°C (sin disipador, TO-220)
```

**Si temperatura >60°C**: Verifica Vgs(on) insuficiente o corriente excesiva.

### 3. Respuesta transitoria (cargas inductivas)

**Procedimiento** (motor DC con diodo flyback):
1. Modo On/Off: Duty 100% → 0%
2. Trigger: Single shot en CH2
3. Base de tiempo: 10 µs/div
4. Observa pico de voltaje al apagar

**Con diodo 1N5819** ✅:
```
Apagado (t=0):
      V+ + 0.7V ───┐
                   │╲
V+  ───────────────┘ ╲___ (caída exponencial ~100 µs)
                       ╲
0V  ────────────────────╲___
```

**Pico aceptable**: V+ + 0.7V (1N5819: Vf=0.45V, 1N4007: Vf=0.7V)

**Sin diodo** ⚠️ (NO probar):
```
Apagado (t=0):
      >100V ───┐ ⚠️ (puede destruir MOSFET)
               │
V+  ───────────┘
```

### 4. Ripple de potencia (RP2040 ventaja)

**Medición de ripple en carga**:
1. CH1: Gate (GP18) PWM 50%
2. CH2: AC coupling (para ver solo ripple)
3. Base de tiempo: 200 µs/div
4. Escala vertical: 10 mV/div

**Ripple esperado** (motor DC 12V 1A, duty 50%):
- **ESP32** (jitter ~10 ns): Ripple ~50 mV p-p
- **RP2040** (jitter ~1 ns): Ripple ~5 mV p-p ✅ (10× menor)

**Aplicación práctica**: Menor ripple = menos ruido electromagnético, mejor para aplicaciones de precisión.

## Resolución de problemas

### Problema 1: Carga no responde

**Síntomas**:
- Osciloscopio muestra PWM correcto en GP18
- Carga permanece apagada o encendida siempre

**Diagnóstico**:
1. Verifica GND común (RP2040 ↔ fuente externa)
2. Mide Vgs con CH1 en Gate, CH2 en Source:
   - Debe ser 0V (off) o 3.3V (on)
   - Si Vgs <2V en on, el MOSFET no satura
3. Verifica MOSFET:
   - Vgs(th) < 2V (compuerta lógica)
   - Polaridad correcta (Gate, Drain, Source)

**Solución**:
- Usa MOSFET de compuerta lógica: IRLZ44N, AO3400
- Verifica cableado: GP18 → 220Ω → Gate, Source → GND

### Problema 2: MOSFET se calienta excesivamente

**Síntomas**:
- MOSFET caliente (>80°C) después de 30 segundos
- Duty <100%, corriente nominal

**Diagnóstico**:
1. Mide Vgs durante conducción (CH1=Gate, CH2=Source):
   - Debe ser ~3.3V
2. Mide Vds durante conducción (CH1=Drain, CH2=Source):
   - Debe ser <0.5V (idealmente <0.2V)
   - Si Vds >1V, el MOSFET está en región lineal (no satura)

**Causas**:
- Vgs insuficiente (MOSFET no lógico: Vgs(on)=10V)
- Rds(on) alto (MOSFET inadecuado para la corriente)

**Solución**:
- Reemplaza por MOSFET lógico (Vgs(on)≤4.5V)
- Añade disipador si P_mosfet >500 mW
- Reduce corriente de carga

### Problema 3: Ruido audible en motor

**Síntomas**:
- Motor emite zumbido molesto (500–2000 Hz)
- Duty <100%

**Diagnóstico**:
- Frecuencia PWM coincide con rango audible humano (20 Hz–20 kHz)
- Mayor sensibilidad: 500–4000 Hz

**Solución** (RP2040 ventaja):
```python
# Opción 1: Frecuencia ultrasónica (silenciosa)
PWM_FREQ = 25000  # 25 kHz (RP2040 soporta hasta 62.5 MHz)

# Opción 2: Frecuencia muy baja (subsónica)
PWM_FREQ = 50  # 50 Hz (motor responde por inercia)
```

**Nota**: ESP32 tiene más jitter a frecuencias altas; RP2040 mantiene estabilidad hasta 20 kHz.

### Problema 4: Picos de voltaje en carga inductiva

**Síntomas**:
- Osciloscopio muestra picos >50V al apagar motor
- MOSFET se daña después de varias horas

**Diagnóstico**:
1. Modo On/Off, trigger single shot
2. Observa pico al apagar (duty 100% → 0%)
3. Si pico >V+ + 5V, el diodo flyback falla o falta

**Solución**:
1. Verifica polaridad del diodo:
   - Cátodo (banda) → +V (positivo de carga)
   - Ánodo → Drenador (nodo de conmutación)
2. Usa diodo rápido (Schottky preferible):
   - 1N5819 (Schottky, Vf=0.45V) ✅ Recomendado
   - 1N4007 (normal, Vf=0.7V) ✅ Aceptable
3. Verifica corriente del diodo:
   - Ifwd > corriente de carga

## Notas de seguridad

### ⚠️ Obligatorio

1. **GND común**: Verifica con multímetro continuidad entre GND del RP2040 y GND de la fuente externa.
2. **Fuente externa**: NO alimentes cargas >100 mA desde 3V3 del RP2040.
3. **Diodo flyback**: Obligatorio para motores, relés, bobinas (cargas inductivas).
4. **Osciloscopio**: Conecta GND de las puntas al GND común (no al nodo de conmutación).

### 🔧 Consejos de medición

- **Puntas de osciloscopio**: Usa cables cortos (<15 cm) para minimizar ringing.
- **Sondas compensadas**: Ajusta compensación (onda cuadrada 1 kHz).
- **AC coupling**: Útil para ver ripple, pero no para medir niveles DC.
- **Trigger**: Usa CH1 (gate) como trigger para sincronizar con CH2 (carga).
- **Persistencia**: Activa para observar variaciones en barrido continuo.

## Recursos adicionales

- **RP2040 Datasheet** (Sección 4.5 PWM): https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf
- **MicroPython PWM RP2040**: https://docs.micropython.org/en/latest/rp2/quickref.html#pwm-pulse-width-modulation
- **MOSFET Switching**: https://www.infineon.com/mosfet
- **Guía de migración ESP32→RP2040**: [../../GUIA_MIGRACION.md](../../GUIA_MIGRACION.md)

---

**Conclusión**: El RP2040 ofrece **PWM ultra estable** (<1 ns jitter) que resulta en menos ruido electromagnético, control más preciso y mayor eficiencia en aplicaciones de conmutación de potencia. 🎯
