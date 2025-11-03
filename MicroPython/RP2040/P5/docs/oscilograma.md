# Oscilograma — PWM para Servomotores (Práctica 5 RP2040)

Los servos R/C esperan un tren de pulsos de ~50 Hz (periodo 20 ms). El ángulo se codifica en el ancho de pulso:

- ~1.0 ms  → cerca de 0°
- ~1.5 ms  → cerca de 90° (centro)
- ~2.0 ms  → cerca de 180°

Algunos servos aceptan rangos extendidos (p.ej. 0.5–2.4 ms), pero no es universal. Si escuchas zumbidos fuertes o el servo se fuerza al extremo, reduce el rango.

## 🔄 Ventajas del RP2040

El RP2040 ofrece **PWM más estable** que el ESP32:

| Característica | ESP32 | RP2040 |
|----------------|-------|--------|
| **Jitter PWM** | ~10 ns típico | **~1 ns típico** ✅ |
| **Estabilidad de ángulo** | ±0.1° | **±0.01°** ✅ |
| **Suavidad de movimiento** | Buena | **Excelente** ✅ |

**Resultado práctico**: Servos mantienen posición con menos vibración micromecánica, ideal para aplicaciones de precisión (cámaras, robótica, aeromodelismo).

## Forma de onda esperada

```
Nivel alto:  ┌──────┐                     ┌──────────┐
             │      │                     │          │
             │      │                     │          │
Nivel bajo: ─┘      └─────────────────────┘          └────────
             ↑      ↑                                 ↑
             t=0    t=1.0–2.0 ms                      t=20 ms (periodo)
```

## Medición con osciloscopio

### Configuración básica

1. Conecta la punta del canal CH1 a la señal de servo (GP18) y la pinza a GND.
2. Configura:
   - **Base de tiempo**: 2 ms/div (para ver el pulso completo)
   - **Voltaje**: 1 V/div (señal de 0–3.3V)
   - **Trigger**: Flanco de subida, ~1.5 V
3. Verifica:
   - **Periodo**: ≈ 20 ms (50 Hz)
   - **Ancho alto**: ≈ 1.0–2.0 ms según el modo (barrido/manual)
   - **Nivel alto**: 3.3V (RP2040 logic level)
   - **Nivel bajo**: 0V

### Mediciones de precisión

Para verificar la **ventaja de estabilidad** del RP2040:

1. **Jitter del pulso**:
   - Modo: Manual (ej. 90°, pulso ~1500 µs)
   - Función: "Measure → Pulse Width"
   - Estadística: "Min/Max/Mean/Std Dev"
   - **Esperado RP2040**: Std Dev < 10 ns (vs ~100 ns ESP32)

2. **Repetibilidad**:
   - Fija el servo a 90° por 60 segundos
   - Captura 1000 pulsos con osciloscopio
   - Histograma de ancho: Debe ser muy estrecho (~1–2 ns)

3. **Respuesta a cambios**:
   - Modo: Barrido continuo
   - Observa transiciones entre ángulos
   - **Esperado**: Rampas suaves sin overshoots significativos

### Comparación ESP32 vs RP2040

Si tienes ambos sistemas disponibles, medición comparativa:

```python
# Misma configuración en ambos:
servo.angle(90)  # 1500 µs nominal
time.sleep(30)   # 30 segundos estable
```

| Métrica | ESP32 | RP2040 | Mejora |
|---------|-------|--------|--------|
| Ancho promedio | 1500 µs | 1500 µs | — |
| Std Dev | ~100 ns | **~10 ns** | **10×** ✅ |
| Jitter peak-to-peak | ~500 ns | **~50 ns** | **10×** ✅ |
| Vibración mecánica | Visible | **Imperceptible** | ✅ |

## Análisis de ángulos específicos

### 0° (pulso ~500 µs)

```
┌─┐
│ │    
│ │    (0.5 ms aprox)
└─┘─────────────────── 20 ms ──────────────────────
```

- **Medida**: 500 ± 10 µs (RP2040: ±1 µs)
- **Servo**: Gira completamente a un extremo
- **Cuidado**: Si el servo zumba fuerte, aumenta `SERVO_MIN_US` a 600–700 µs

### 90° (pulso ~1500 µs)

```
┌─────┐
│     │    
│     │    (1.5 ms aprox)
└─────┘─────────────── 20 ms ──────────────────────
```

- **Medida**: 1500 ± 10 µs (RP2040: ±1 µs)
- **Servo**: Posición central (perpendicular)
- **Prueba**: Servo debe mantener posición sin vibrar

### 180° (pulso ~2400 µs)

```
┌──────────┐
│          │    
│          │    (2.4 ms aprox)
└──────────┘──── 20 ms ──────────────────────
```

- **Medida**: 2400 ± 10 µs (RP2040: ±1 µs)
- **Servo**: Gira completamente al otro extremo
- **Cuidado**: Si el servo se fuerza, reduce `SERVO_MAX_US` a 2300 µs

## Resolución de problemas

### Problema 1: Servo vibra en posición fija

**Síntomas**:
- Servo zumba/vibra constantemente en un ángulo fijo
- Osciloscopio muestra jitter grande (>100 ns Std Dev)

**Diagnóstico**:
```python
# Código de prueba:
servo.angle(90)
time.sleep(60)  # Observa 60 segundos
```

**Soluciones**:
1. **Si es RP2040**: Jitter debe ser <10 ns. Si es mayor:
   - Verifica alimentación estable (USB o fuente regulada)
   - Revisa conexión GP18 (cable corto, sin interferencias)
   - Desconecta periféricos I2C/SPI que puedan generar ruido

2. **Si es ESP32**: Jitter ~100 ns es normal. Reduce añadiendo:
   - Condensador 470 µF cerca del servo (5V ↔ GND)
   - Cable de señal corto (<20 cm) y alejado de fuentes de alimentación

### Problema 2: Ancho de pulso incorrecto

**Síntomas**:
- Osciloscopio muestra 1600 µs cuando pides 1500 µs
- Servo no alcanza ángulos extremos

**Diagnóstico**:
```python
# Verifica calibración:
servo.pulse_us(1000)  # Debe dar 1000 µs ±10 µs en osciloscopio
servo.pulse_us(2000)  # Debe dar 2000 µs ±10 µs
```

**Soluciones**:
1. Ajusta constantes en `main.py`:
   ```python
   SERVO_MIN_US = 500   # Ajusta hasta que servo llegue a 0° sin forzarse
   SERVO_MAX_US = 2400  # Ajusta hasta que servo llegue a 180° sin forzarse
   ```

2. Verifica frecuencia PWM:
   ```python
   print(servo.pwm.freq())  # Debe ser 50 Hz
   ```

### Problema 3: Periodo incorrecto

**Síntomas**:
- Osciloscopio muestra periodo ≠ 20 ms (ej. 18 ms o 22 ms)
- Servo se comporta erráticamente

**Diagnóstico**:
```python
# Configura frecuencia explícitamente:
servo.pwm.freq(50)  # Fuerza a 50 Hz
time.sleep(1)
print(servo.pwm.freq())  # Verifica que sea 50
```

**Soluciones**:
1. **RP2040**: Verifica que el reloj del sistema sea estable:
   ```python
   import machine
   print(machine.freq())  # Debe ser 125000000 (125 MHz) típicamente
   ```

2. Si el periodo varía, reinicia la placa y vuelve a configurar PWM.

### Problema 4: Ruido eléctrico en la señal

**Síntomas**:
- Osciloscopio muestra picos/glitches en nivel bajo o alto
- Servo se sacude aleatoriamente

**Diagnóstico**:
- Base de tiempo: 100 ns/div (zoom en flancos)
- Trigger: Flanco de subida
- Busca: Overshoots (>3.5V), ringing, glitches

**Soluciones (RP2040)**:
1. **Resistencia serie**: 100–220 Ω en serie con GP18 (amortigua ringing)
2. **Condensador de desacople**: 100 nF cerca del pin VSYS del RP2040
3. **Tierra común sólida**: Cable GND corto entre RP2040 y servo
4. **Cable de señal apantallado**: Si el cable es >30 cm

## Análisis avanzado: Control por potenciómetro (modo 4)

El RP2040 permite control **subgrado** gracias al ADC de 16 bits:

### Configuración de captura

1. **Dos canales**:
   - CH1: GP18 (señal PWM al servo)
   - CH2: GP26 (voltaje del potenciómetro)

2. **Sincronización**:
   - Trigger: CH2 (flanco de subida o caída)
   - Modo: Auto o Normal

3. **Observación**:
   - Al girar el potenciómetro lentamente, CH1 cambia **suavemente** el ancho de pulso
   - Resolución: 180° / 65535 bits = **0.0027°/bit** ✅

### Medición de suavidad

```python
# Código de prueba:
while True:
    raw = adc.read_u16()
    angle = int(ANGLE_MIN + (raw / 65535.0) * (ANGLE_MAX - ANGLE_MIN))
    servo.angle(angle)
    print(f"ADC={raw} → {angle}°")
    time.sleep_ms(50)
```

**Captura de osciloscopio**:
1. Gira el potenciómetro **muy lentamente** (10 segundos de un extremo al otro)
2. Observa CH1: Debe cambiar en pasos de ~1 µs (imperceptibles)
3. Cuenta los pasos visibles en 1° de rotación:
   - **ESP32 (12-bit)**: ~23 pasos visibles (0.044°/paso)
   - **RP2040 (16-bit)**: ~370 pasos (0.0027°/paso) → **Movimiento continuo** ✅

### Ejemplo de captura

**ESP32 (12-bit ADC)**:
```
Potenciómetro girando lentamente:
ADC=2047 → 89°  ←─┐
ADC=2048 → 90°  ←─┼─ Paso de 1° (23 bits ADC)
ADC=2071 → 91°  ←─┘   = Movimiento "escalón"
```

**RP2040 (16-bit ADC)**:
```
Potenciómetro girando lentamente:
ADC=32767 → 89.996°  ←─┐
ADC=32768 → 90.000°  ←─┼─ Paso de 0.003° (1 bit ADC)
ADC=32769 → 90.003°  ←─┘   = Movimiento "continuo"
```

## Notas de alimentación (RP2040 específico)

### Opción 1: VSYS (5V del USB)

**Ventajas**:
- Simplifica cableado (no requiere fuente externa)
- Ideal para prototipos y demostraciones

**Limitaciones**:
- **Corriente máxima**: 500 mA (límite USB)
- **Servos compatibles**: SG90, MG90S (consumo <300 mA en movimiento)
- **Servos incompatibles**: MG996R (consumo >500 mA)

**Circuito**:
```
USB 5V → VSYS (pin 40) → Servo VCC (rojo)
                GND     → Servo GND (negro)
              GP18      → Servo Signal (amarillo)
```

**Medición**:
- Usa multímetro en serie con VSYS para medir corriente
- **Servo SG90 quieto**: ~10 mA
- **Servo SG90 movimiento lento**: ~100–150 mA
- **Servo SG90 movimiento rápido o bloqueado**: ~250–300 mA ✅ (dentro de límite USB)

### Opción 2: Fuente externa 5V

**Necesario para**:
- Servos grandes (MG996R, HS-422, etc.)
- Múltiples servos (>2 servos simultáneos)
- Aplicaciones de alta corriente (>500 mA total)

**Circuito**:
```
Fuente 5V 2A → Servo VCC (rojo)
         GND → Servo GND (negro) ┬─ GND RP2040 (tierra común)
       GP18  → Servo Signal (amarillo)
```

**Importante**: GND de la fuente externa y GND del RP2040 **deben estar unidos** (tierra común).

**Medición**:
- Coloca capacitor electrolítico 470 µF cerca del servo (5V ↔ GND)
- Verifica con osciloscopio que 5V no tenga caídas >0.2V durante movimiento
- Si hay caídas mayores, aumenta el capacitor (1000 µF) o usa fuente de mayor corriente

## Recursos adicionales

- **RP2040 Datasheet** (Sección 4.5 PWM): https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf
- **MicroPython PWM RP2040**: https://docs.micropython.org/en/latest/rp2/quickref.html#pwm-pulse-width-modulation
- **Servo Theory**: https://www.arduino.cc/en/Tutorial/LibraryExamples/Sweep
- **Guía de migración ESP32→RP2040**: [../../GUIA_MIGRACION.md](../../GUIA_MIGRACION.md)

---

**Conclusión**: El RP2040 es una **excelente plataforma para control de servos** gracias a su PWM estable (<1 ns jitter) y ADC de 16 bits. Para aplicaciones de precisión (robótica, cámaras, aeromodelismo), el RP2040 supera al ESP32 en estabilidad y suavidad de movimiento. 🎯
