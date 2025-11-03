# Oscilograma — P7 Motores a Pasos (RP2040)

Esta guía proporciona instrucciones detalladas para **medir y registrar** las señales de control de motores a pasos usando un **osciloscopio digital** o herramientas de análisis lógico.

---

## 🎯 Objetivos de la medición

1. **Verificar timing de señales STEP/DIR** (A4988) o secuencias de fases (ULN2003)
2. **Validar intervalo entre pasos** vs RPM configurado
3. **Detectar anomalías** (jitter, glitches, pulsos perdidos)
4. **Comparar RP2040 vs ESP32** en precisión de timing
5. **Documentar formas de onda** para reportes de laboratorio

---

## 🔧 Equipo necesario

### Opción 1: Osciloscopio digital (recomendado)
- **Mínimo**: 2 canales, 10 MHz, 100 MS/s
- **Ideal**: 4 canales (para medir las 4 fases del ULN2003)
- **Ejemplos**: Rigol DS1054Z, Siglent SDS1104X-E, Keysight DSOX1204G

### Opción 2: Analizador lógico
- **Ventaja**: Muchos canales (8-16), ideal para secuencias digitales
- **Desventaja**: No mide voltaje analógico (solo HIGH/LOW)
- **Ejemplos**: Saleae Logic 8, DSLogic Plus

### Opción 3: Osciloscopio USB
- **Ventaja**: Económico, portátil
- **Desventaja**: Ancho de banda limitado (~20 MHz típico)
- **Ejemplos**: Hantek 6022BE, OWON VDS1022I

---

## 📊 Mediciones por configuración

### A) Driver A4988/DRV8825 + NEMA 17

#### 🔍 Señal STEP (GP18)

**Configuración del osciloscopio:**
- **Canal 1**: GP18 (STEP)
- **Escala vertical**: 1V/div (señal 0-3.3V)
- **Escala horizontal**: 2 ms/div (para 60 RPM) o 500 µs/div (para altas RPM)
- **Trigger**: Flanco ascendente, nivel 1.5V
- **Acoplamiento**: DC

**Formas de onda esperadas:**

**Modo Jog (1 paso manual):**
```
STEP (GP18):
     ┌─5µs─┐
─────┘     └───────────────────────
     ↑
     Rising edge = 1 paso
```

**Movimiento continuo (60 RPM, 200 pasos/rev):**
```
STEP (GP18):
     ┌─┐     ┌─┐     ┌─┐     ┌─┐
─────┘ └─────┘ └─────┘ └─────┘ └─────
     ◄─5ms──►◄─5ms──►◄─5ms──►
     (intervalo entre pasos)
```

**Cálculo del intervalo:**

$$
\text{Intervalo (µs)} = \frac{60 \times 10^6}{\text{RPM} \times \text{pasos/rev}}
$$

**Ejemplos:**

| RPM | Pasos/rev | Intervalo esperado | Frecuencia STEP |
|-----|-----------|-------------------|-----------------|
| 60  | 200       | 5000 µs (5 ms)    | 200 Hz          |
| 120 | 200       | 2500 µs (2.5 ms)  | 400 Hz          |
| 240 | 200       | 1250 µs (1.25 ms) | 800 Hz          |

**Mediciones a realizar:**
1. **Ancho de pulso STEP**: Debe ser ~5 µs (configurable en `stepper_a4988.py`)
2. **Intervalo entre pulsos**: Verificar que coincida con el cálculo
3. **Jitter**: Medir variación entre intervalos consecutivos
   - RP2040 esperado: <1 µs (sin PIO), <10 ns (con PIO en futuro)
   - ESP32 típico: ~10 µs

#### 🔍 Señal DIR (GP19)

**Configuración del osciloscopio:**
- **Canal 2**: GP19 (DIR)
- **Escala vertical**: 1V/div
- **Escala horizontal**: 100 ms/div (para ver cambios de dirección)

**Formas de onda esperadas:**

**Cambio de dirección (CW → CCW):**
```
STEP (CH1):
     ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐
─────┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─────
     CW steps →    ← CCW steps

DIR (CH2):
     ──────────────┐
HIGH (CW)          │
                   └─────────────────
                    LOW (CCW)
```

**Mediciones:**
- Nivel HIGH: ~3.3V (CW, clockwise)
- Nivel LOW: ~0V (CCW, counterclockwise)
- Tiempo de setup: >200 ns antes del primer pulso STEP (A4988 spec)

#### 🔍 Señal ENABLE (GP5)

**Configuración del osciloscopio:**
- **Canal 3**: GP5 (ENABLE)
- **Escala vertical**: 1V/div

**Formas de onda esperadas:**
```
ENABLE (GP5):
     ──────────┐        ┌──────────
DISABLED (HIGH)│        │
                └────────┘
                 ENABLED (LOW activo)
                 (motor puede moverse)
```

**Mediciones:**
- Nivel LOW: Motor habilitado (~0V)
- Nivel HIGH: Motor deshabilitado (~3.3V, bobinas sin corriente)

---

### B) Driver ULN2003 + 28BYJ-48

#### 🔍 Secuencias de 4 fases (GP26, GP27, GP28, GP22)

**Configuración del osciloscopio (4 canales):**
- **Canal 1**: GP26 (IN1)
- **Canal 2**: GP27 (IN2)
- **Canal 3**: GP28 (IN3)
- **Canal 4**: GP22 (IN4)
- **Escala vertical**: 1V/div (todas)
- **Escala horizontal**: 5 ms/div
- **Trigger**: Canal 1, flanco ascendente

**Formas de onda esperadas (Half-step):**

```
IN1 (GP26):
     ┌───────┐               ┌───────┐
─────┘       └───────────────┘       └─────
     
IN2 (GP27):
         ┌───────┐               ┌───────┐
─────────┘       └───────────────┘       └─
     
IN3 (GP28):
             ┌───────┐               ┌───────┐
─────────────┘       └───────────────┘       └─
     
IN4 (GP22):
                 ┌───────┐               ┌───────┐
─────────────────┘       └───────────────┘       └─
     
     ◄───3ms──►◄───3ms──►◄───3ms──►◄───3ms──►
```

**Tabla de estados (Half-step, 8 pasos/ciclo):**

| Paso | IN1 | IN2 | IN3 | IN4 | Estado |
|------|-----|-----|-----|-----|--------|
| 1    | 1   | 0   | 0   | 0   | Solo fase 1 |
| 2    | 1   | 1   | 0   | 0   | Fases 1+2 |
| 3    | 0   | 1   | 0   | 0   | Solo fase 2 |
| 4    | 0   | 1   | 1   | 0   | Fases 2+3 |
| 5    | 0   | 0   | 1   | 0   | Solo fase 3 |
| 6    | 0   | 0   | 1   | 1   | Fases 3+4 |
| 7    | 0   | 0   | 0   | 1   | Solo fase 4 |
| 8    | 1   | 0   | 0   | 1   | Fases 4+1 |

**Mediciones a realizar:**
1. **Delay entre cambios de fase**: Debe ser ~3 ms (ajustable en `stepper_uln2003.py`)
2. **Verificar secuencia**: Debe seguir la tabla anterior (desfase progresivo)
3. **Niveles lógicos**:
   - HIGH: ~3.3V
   - LOW: ~0V
4. **Dirección inversa**: La secuencia se ejecuta en orden contrario

#### 🔍 Forma de onda completa (1 ciclo)

**8 pasos = 1 ciclo en half-step:**
```
Tiempo: 0ms    3ms    6ms    9ms    12ms   15ms   18ms   21ms   24ms
IN1:    ┌──────┬──────┐                          ┌──────┐
        │      │      └──────────────────────────┘      └──────
IN2:           ┌──────┬──────┬──────┐
        ───────┘      │      │      └────────────────────────
IN3:                  │      ┌──────┬──────┬──────┐
        ──────────────┘      │      │      │      └──────────
IN4:                         │      │      ┌──────┬──────┐
        ─────────────────────┘      └──────┘      │      └────

        ◄───────────────── 24 ms (1 ciclo) ─────────────────►
```

**Cálculo de velocidad:**
- **8 pasos** = 1 ciclo = **24 ms** (con delay 3 ms)
- **4096 pasos** = 512 ciclos = **12.288 segundos** = **1 revolución completa**
- **RPM** = $60 / 12.288 \approx 4.88$ RPM

---

## 📈 Análisis de jitter y precisión

### ¿Qué es el jitter?

**Jitter** = Variación en el **intervalo de tiempo** entre pulsos consecutivos.

**Ejemplo**:
- Intervalo ideal: 5000 µs
- Mediciones reales: 4998, 5002, 4999, 5001, 5000 µs
- **Jitter máximo**: ±2 µs

### Medición de jitter en el osciloscopio

**Método 1: Función de estadísticas**
1. Activa medición de **periodo** en señal STEP
2. Habilita **estadísticas** (min, max, desviación estándar)
3. Captura al menos **100 periodos**
4. Calcula jitter: `Jitter = (Periodo_max - Periodo_min) / 2`

**Método 2: Modo persistencia**
1. Activa **modo persistencia** en el osciloscopio
2. Observa el "espesor" del flanco ascendente del pulso STEP
3. Más grueso = mayor jitter

### Comparación RP2040 vs ESP32

| Parámetro | RP2040 (sin PIO) | RP2040 (con PIO) | ESP32 |
|-----------|------------------|------------------|-------|
| **Jitter típico** | <1 µs | <10 ns | ~10 µs |
| **Causa del jitter** | Interrupciones, GC | Ninguna (hardware) | WiFi, interrupciones |
| **Aplicaciones** | CNC hobby, prototipos | CNC profesional, lab equipment | IoT, prototipos conectados |

**Conclusión**: RP2040 tiene timing **10-100x más estable** que ESP32 para control de motores.

---

## 🧪 Procedimiento de medición completo

### Paso 1: Preparación del hardware

1. Conecta el RP2040 al driver y motor según `assets/wiring_*.mmd`
2. Verifica alimentación y GND común
3. Conecta puntas del osciloscopio:
   - **Para A4988**: CH1 → GP18, CH2 → GP19, GND → GND RP2040
   - **Para ULN2003**: CH1-4 → GP26/27/28/22, GND → GND RP2040

### Paso 2: Carga del código

1. Sube `main.py` y librerías al RP2040
2. Abre REPL con terminal serial
3. Selecciona **Modo 2: Mover N pasos** para mediciones controladas

### Paso 3: Mediciones básicas (A4988)

**Test 1: Ancho de pulso STEP**
```python
# En REPL, ejecuta 10 pasos a 60 RPM
Opción: 2
Pasos: 10
RPM: 60
```
- **Medición**: Ancho de pulso STEP (esperado: ~5 µs)
- **Cursor 1**: Flanco ascendente STEP
- **Cursor 2**: Flanco descendente STEP
- **Resultado**: ΔT ≈ 5 µs

**Test 2: Intervalo entre pasos**
```python
# 200 pasos a 60 RPM (1 revolución completa)
Pasos: 200
RPM: 60
```
- **Medición**: Periodo entre flancos ascendentes
- **Esperado**: 5000 µs (para 60 RPM, 200 pasos/rev)
- **Cursor 1**: Primer flanco ascendente
- **Cursor 2**: Siguiente flanco ascendente
- **Resultado**: ΔT ≈ 5000 µs

**Test 3: Jitter**
```python
# Movimiento largo para estadísticas
Pasos: 1000
RPM: 120
```
- **Medición**: Activa estadísticas del periodo
- **Captura**: Al menos 100 periodos
- **Registro**:
  - Periodo promedio: ___ µs
  - Desviación estándar: ___ µs
  - Min: ___ µs
  - Max: ___ µs
  - Jitter = (Max - Min) / 2 = ___ µs

### Paso 4: Mediciones secuenciales (ULN2003)

**Test 4: Secuencia half-step**
```python
# 8 pasos (1 ciclo completo)
Opción: 2
Pasos: 8
RPM: 15
```
- **Medición**: Verificar secuencia en 4 canales
- **Escala horizontal**: 5 ms/div
- **Verificar**: Desfase progresivo entre IN1-IN4
- **Captura**: Screenshot del ciclo completo

**Test 5: Dirección invertida**
```python
# Modo jog, alternar entre + y -
Opción: 1
Comando: +
Comando: +
Comando: -
Comando: -
```
- **Medición**: Observar inversión de secuencia
- **CW**: IN1 → IN2 → IN3 → IN4 → IN1...
- **CCW**: IN1 → IN4 → IN3 → IN2 → IN1...

---

## 📸 Plantilla de documentación

### Registro de mediciones

**Fecha**: ____________  
**Configuración**: A4988 / ULN2003 (rodear)  
**Motor**: NEMA 17 / 28BYJ-48  
**Osciloscopio**: _____________

#### Medición 1: Ancho de pulso STEP (A4988)
- **RPM**: _____
- **Ancho medido**: _____ µs
- **Especificación**: 5 µs ± 1 µs
- **✅ / ❌**: _____

![Captura 1: Ancho de pulso STEP](path/to/screenshot1.png)

#### Medición 2: Intervalo entre pasos
- **RPM**: _____
- **Pasos/rev**: _____
- **Intervalo esperado**: _____ µs (calculado)
- **Intervalo medido**: _____ µs
- **Error**: _____ % 
- **✅ / ❌**: _____

![Captura 2: Intervalo entre pasos](path/to/screenshot2.png)

#### Medición 3: Jitter
- **RPM**: _____
- **Periodo promedio**: _____ µs
- **Desviación estándar**: _____ µs
- **Jitter máximo**: _____ µs
- **Comparación con ESP32**: _____ (mejor/peor/similar)

![Captura 3: Estadísticas de periodo](path/to/screenshot3.png)

#### Medición 4: Secuencia ULN2003 (si aplica)
- **Delay entre fases**: _____ ms
- **Secuencia verificada**: ✅ / ❌
- **Observaciones**: _____________________

![Captura 4: Secuencia de 4 fases](path/to/screenshot4.png)

---

## 🔬 Experimentos avanzados

### Experimento 1: Efecto del RPM en jitter

**Objetivo**: Determinar cómo varía el jitter con la velocidad.

**Procedimiento**:
1. Mide jitter a 30, 60, 120, 240, 480 RPM
2. Registra valores en tabla:

| RPM | Intervalo (µs) | Jitter (µs) | % Jitter |
|-----|---------------|-------------|----------|
| 30  |               |             |          |
| 60  |               |             |          |
| 120 |               |             |          |
| 240 |               |             |          |
| 480 |               |             |          |

3. Grafica **RPM vs Jitter**
4. **Conclusión**: ¿El jitter aumenta a altas velocidades?

### Experimento 2: Comparación RP2040 vs ESP32

**Objetivo**: Cuantificar la mejora de timing del RP2040.

**Procedimiento**:
1. Usa el mismo motor y driver
2. Programa idéntico en ambas plataformas
3. Mide jitter en ambas a 120 RPM
4. Registra:

| Plataforma | Jitter (µs) | Mejora RP2040 |
|------------|-------------|---------------|
| ESP32      | _____ µs    | —             |
| RP2040     | _____ µs    | _____x mejor  |

### Experimento 3: Efecto de microstepping (A4988)

**Objetivo**: Verificar que el intervalo se ajusta correctamente con microstepping.

**Configuración**:
1. Configura MS1-MS3 para 1/1, 1/2, 1/4, 1/8, 1/16
2. Mide intervalo a RPM constante (60 RPM)
3. Registra:

| Microstepping | Pasos/rev | Intervalo esperado (µs) | Intervalo medido (µs) |
|---------------|-----------|------------------------|-----------------------|
| 1/1           | 200       | 5000                   |                       |
| 1/2           | 400       | 2500                   |                       |
| 1/4           | 800       | 1250                   |                       |
| 1/8           | 1600      | 625                    |                       |
| 1/16          | 3200      | 312.5                  |                       |

---

## 🚨 Problemas comunes y diagnóstico

### Problema 1: No se observa señal en el osciloscopio

**Posibles causas**:
- Punta de prueba en mal estado (verificar con señal de calibración del osciloscopio)
- Pin incorrecto (verificar con multímetro: GP18 debe medir 0-3.3V)
- GND de punta no conectado (⚠️ crítico)

**Solución**:
1. Conecta punta a **CAL 1 kHz** del osciloscopio (debe ver cuadrada 1 kHz)
2. Si funciona, problema está en conexión al RP2040
3. Verifica continuidad con multímetro

### Problema 2: Señal distorsionada o ruidosa

**Posibles causas**:
- Cables muy largos (capacitancia parásita)
- Fuente de alimentación ruidosa
- GND flotante (no común)

**Solución**:
1. Usa cables de punta <15 cm
2. Conecta GND de punta lo más cerca posible del pin medido
3. Añade condensador 100 µF entre VSYS y GND del RP2040

### Problema 3: Jitter excesivo (>10 µs en RP2040)

**Posibles causas**:
- Código Python con delays bloqueantes
- Garbage collector de MicroPython activo
- Interrupciones de otros periféricos

**Solución**:
1. Desactiva WiFi (si usas Pico W): `import network; network.WLAN().active(False)`
2. Reduce frecuencia de garbage collection: `import gc; gc.threshold(50000)`
3. Considera implementar driver con PIO (proyecto avanzado)

---

## 📚 Recursos adicionales

### Hojas de datos (Datasheets)
- [A4988 Stepper Driver](https://www.pololu.com/file/0J450/a4988_DMOS_microstepping_driver_with_translator.pdf)
- [DRV8825 Stepper Driver](https://www.ti.com/lit/ds/symlink/drv8825.pdf)
- [ULN2003 Darlington Array](https://www.ti.com/lit/ds/symlink/uln2003a.pdf)
- [28BYJ-48 Stepper Motor](https://components101.com/motors/28byj-48-stepper-motor)
- [RP2040 Datasheet (GPIO timing)](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf)

### Software de análisis
- **PulseView** (Sigrok): Análisis de señales lógicas (gratis, open-source)
- **Matlab/Octave**: Scripts para análisis de jitter y FFT
- **Python + matplotlib**: Visualización de datos exportados del osciloscopio

### Tutoriales RP2040 PIO
- [RP2040 PIO Stepper Control](https://github.com/GitJer/Some_RPI-Pico_stuff/tree/main/Stepper)
- [PIO Assembly Tutorial](https://learn.adafruit.com/intro-to-rp2040-pio-with-circuitpython)

---

## ✅ Criterios de aprobación

Para considerar la práctica completa, debes:

1. ✅ **Capturar al menos 4 screenshots** del osciloscopio:
   - Ancho de pulso STEP (A4988) o secuencia completa (ULN2003)
   - Intervalo entre pasos
   - Cambio de dirección (señal DIR en A4988)
   - Jitter con estadísticas

2. ✅ **Completar tabla de mediciones** con valores reales

3. ✅ **Calcular error porcentual** entre valor esperado y medido:
   $$
   \text{Error \%} = \frac{|\text{Medido} - \text{Esperado}|}{\text{Esperado}} \times 100
   $$
   Error aceptable: <5% para intervalos, <20% para jitter

4. ✅ **Análisis comparativo RP2040 vs ESP32** (opcional pero recomendado)

5. ✅ **Documentar al menos 1 problema encontrado** y su solución

---

> **Nota final**: Las mediciones con osciloscopio son fundamentales para validar que el sistema funciona según especificaciones. En aplicaciones industriales (CNC, robótica), el jitter de timing puede ser la diferencia entre un sistema funcional y uno que pierde pasos constantemente. RP2040 con PIO es una de las mejores opciones actuales para control de steppers de alta precisión. 🎯
