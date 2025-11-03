# Práctica 7 — Control de Motores a Pasos (RP2040)

## 🔄 Versión RP2040

Esta versión está **optimizada para RP2040**, aprovechando las ventajas de timing determinístico y la capacidad PIO para futuros proyectos avanzados de control multi-motor.

**Cambios principales respecto a ESP32:**

| Componente | ESP32 | RP2040 | Notas |
|------------|-------|--------|-------|
| **Pines A4988** | GPIO18/19/5 | **GP18/19/5** | Sin cambios numéricos |
| **Pines ULN2003** | GPIO[26,25,33,32] | **GP[26,27,28,22]** | ⚠️ **GP22 reemplaza GPIO33** (no existe en RP2040) |
| **Endstop** | GPIO4 | **GP4** | Sin cambio |
| **Timing** | ~10 µs jitter PWM | **<10 ns con PIO** | Futuro: control ultra-preciso |
| **GPIO disponibles** | 28 útiles | **30 GPIO** | Mayor flexibilidad para multi-motor |

---

## Objetivos

- Comprender el funcionamiento de motores a pasos **bipolares** (NEMA 17) y **unipolares** (28BYJ-48).
- Controlar drivers **A4988/DRV8825** mediante señales STEP/DIR y **ULN2003** con secuencias de paso.
- Implementar **5 modos de control**: jog manual, movimiento por número de pasos, barrido con fin de carrera, homing e información.
- Relacionar **RPM**, **pasos por revolución** e **intervalo de tiempo** entre pasos.
- Explorar las ventajas de **RP2040** para control de steppers (timing determinístico, PIO).

---

## Material

- **RP2040** (Raspberry Pi Pico, Pico W, o compatible) con MicroPython
- **Opción A:** Motor **NEMA 17** (bipolar) + driver **A4988** o **DRV8825**
- **Opción B:** Motor **28BYJ-48** (unipolar) + driver **ULN2003**
- **Fuente externa**:
  - 12 V / 2 A para NEMA 17 (típico)
  - 5 V / 500 mA para 28BYJ-48 (puede usar VSYS si corriente <500 mA)
- **Fin de carrera** (microswitch) opcional para homing y barrido
- Cables, protoboard, multímetro

---

## Conexiones (pines)

Consulta **`PINES.md`** para detalle completo con tablas comparativas ESP32 vs RP2040.

### Resumen rápido:

#### A4988/DRV8825 + NEMA 17:
| Señal | RP2040 | ESP32 | Notas |
|-------|--------|-------|-------|
| STEP  | **GP18** | GPIO18 | Pulso de paso |
| DIR   | **GP19** | GPIO19 | Dirección |
| EN    | **GP5**  | GPIO5  | Enable (LOW activo) |
| VMOT  | Fuente externa 12 V | ⚠️ GND común obligatorio |

#### ULN2003 + 28BYJ-48:
| Señal | RP2040 | ESP32 | Notas |
|-------|--------|-------|-------|
| IN1   | **GP26** | GPIO26 | Sin cambio |
| IN2   | **GP27** | GPIO25 | ⚠️ Cambio |
| IN3   | **GP28** | GPIO33 | ⚠️ **GPIO33 no existe en RP2040** |
| IN4   | **GP22** | GPIO32 | ⚠️ Cambio |
| VCC   | 5V (VSYS o externa) | 5V | <500 mA |

#### Fin de carrera (opcional):
| Señal | RP2040 | ESP32 | Configuración |
|-------|--------|-------|---------------|
| ENDSTOP | **GP4** | GPIO4 | Pull-up interno + contacto a GND |

Diagramas de cableado en `assets/wiring_a4988.mmd` y `assets/wiring_uln2003.mmd`.

---

## Uso

### 1) Selecciona el driver

Edita `main.py` (línea ~20):

```python
# Configuración del driver (cambiar según hardware)
DRIVER_TYPE = "A4988"      # ← Para NEMA 17 con A4988/DRV8825
# DRIVER_TYPE = "ULN2003"  # ← Para 28BYJ-48 con ULN2003
```

### 2) Carga el código

Usando **Pymakr** o **rshell**:

```bash
# Con Pymakr: clic derecho en carpeta P7 → Upload project to device
# Con rshell:
> rsync . /pyboard
> repl
```

Al reiniciar, verás el banner:

```
[BOOT] P7 — Motores a Pasos (A4988/DRV8825 y ULN2003) (RP2040)
```

### 3) Menú interactivo

En el **REPL** aparecerá:

```
═══════════════════════════════════════════════
  P7 — CONTROL DE MOTORES A PASOS (RP2040)
═══════════════════════════════════════════════
Driver seleccionado: A4988

Modos:
  1) Jog         — Control manual paso a paso
  2) Mover N     — Movimiento con pasos y RPM
  3) Barrido     — Avance/retroceso con fin de carrera
  4) Homing      — Búsqueda de referencia (endstop)
  5) Info        — Configuración del driver

Opción (1-5):
```

### 4) Modos de operación

#### Modo 1: Jog (Control manual)
- Presiona `+` para avanzar 1 paso (CW)
- Presiona `-` para retroceder 1 paso (CCW)
- Presiona `m` + ENTER para volver al menú

```
[ Modo Jog ]
  + = Avanzar un paso (CW)
  - = Retroceder un paso (CCW)
  m = Menú
Comando: +
  [Avance] Paso 1
Comando: +
  [Avance] Paso 2
```

#### Modo 2: Mover N pasos
- Ingresa número de pasos (positivo=CW, negativo=CCW)
- Ingresa RPM (velocidad de rotación)
- Motor ejecuta movimiento y retorna al menú

```
[ Modo Mover N ]
Pasos (+ CW, - CCW, 0=menú): 400
RPM (0=menú): 60

→ Moviendo 400 pasos a 60.0 RPM...
✓ Movimiento completo. Presiona ENTER.
```

#### Modo 3: Barrido (Sweep)
- Avanza hasta detectar fin de carrera (o límite de pasos)
- Retrocede la misma cantidad
- Repite indefinidamente (presiona `m` + ENTER para detener)

```
[ Modo Barrido ]
RPM (0=menú): 30

→ Barrido iniciado (30.0 RPM). Presiona 'm' + ENTER para detener.

[Avance] Paso 50 / límite 1000
[Endstop detectado] en paso 283
[Retroceso] Paso 283 / 283
[Retroceso] Completo
```

#### Modo 4: Homing (Búsqueda de referencia)
- Retrocede lentamente hasta detectar fin de carrera
- Avanza 10 pasos para liberar el sensor
- Establece posición de referencia

```
[ Modo Homing ]
→ Buscando home (CCW, 20 RPM)...

[Homing] Paso 150
[Endstop detectado] → Home encontrado
[Liberando] +10 pasos
✓ Homing completo. Presiona ENTER.
```

#### Modo 5: Info (Configuración)
Muestra la configuración actual del driver:

```
[ Información del Driver ]

Driver: A4988
Pines:
  STEP:   GP18
  DIR:    GP19
  ENABLE: GP5

Motor:
  Pasos/rev: 200 (1.8° por paso)
  Microstepping: 1/1 (200 pasos/rev)
  
Endstop: GP4 (configurado)

RPM → Intervalo:
  60 RPM = 5000 µs entre pasos
  120 RPM = 2500 µs entre pasos
```

---

## Verificación y medición

### Con osciloscopio:

1. **Señal STEP (A4988)**:
   - Conecta canal 1 a **GP18**
   - Observa pulsos rectangulares
   - **Ancho de pulso**: ~5 µs
   - **Intervalo entre pulsos** = $(60 \times 10^6) / (\text{RPM} \times \text{pasos/rev})$ µs
   - Ejemplo: 60 RPM, 200 pasos/rev → 5000 µs entre pulsos

2. **Señal DIR (A4988)**:
   - Conecta canal 2 a **GP19**
   - Nivel HIGH = CW, LOW = CCW
   - Cambia con `+` / `-` en modo jog

3. **Secuencias ULN2003**:
   - Conecta 4 canales a **GP26, GP27, GP28, GP22**
   - Observa secuencia half-step (8 estados) o full-step (4 estados)
   - **Delay entre pasos**: ~3 ms (típico para 28BYJ-48)

### Sin osciloscopio:

- **Velocidad**: Mide tiempo de una revolución completa con cronómetro
  - 200 pasos a 60 RPM → 1 segundo/revolución
  - 4096 pasos (28BYJ-48) a 15 RPM → 4 segundos/revolución

- **Torque**: Intenta frenar el motor con la mano (⚠️ cuidado con altas velocidades)
  - NEMA 17: ~4.4 kg·cm (detectable resistencia)
  - 28BYJ-48: ~0.4 kg·cm (fácil de frenar)

### Documentación:

Registra capturas de osciloscopio y mediciones en **`docs/oscilograma.md`**.

---

## Seguridad y buenas prácticas

⚠️ **Alimentación externa obligatoria para NEMA 17:**
- Usa fuente de 12 V / 2 A mínimo
- **GND común** entre RP2040 y fuente del motor (crítico para evitar daños)
- No conectar VMOT a VSYS del RP2040 (quemaría el regulador)

⚠️ **Configuración VREF en A4988/DRV8825:**
- Ajusta el potenciómetro del driver para limitar corriente al motor
- Fórmula: $V_{\text{REF}} = I_{\text{max}} \times 8 \times R_{\text{sense}}$
- Típico: $V_{\text{REF}} = 1.0$ V para 1.5 A (con $R_{\text{sense}} = 0.1 \Omega$)
- Usa multímetro en el pin VREF del driver

⚠️ **Fin de carrera:**
- Prueba el microswitch antes de activar homing
- Velocidad reducida en homing (20 RPM típico) para evitar rebotes
- Asegura que el motor no golpee mecánicamente la estructura

⚠️ **Sobrecalentamiento:**
- En ULN2003: llama `motor.release()` al terminar (desactiva bobinas)
- En A4988: desactiva ENABLE cuando no uses el motor
- Los drivers pueden calentarse (~50°C normal, >80°C revisar VREF)

⚠️ **Vibración excesiva:**
- Verifica que el acoplamiento mecánico esté firme
- En A4988: usa microstepping (MS1-MS3) para suavizar movimiento
- En ULN2003: half-step es más suave que full-step

---

## Estructura del proyecto

```
P7/
├── boot.py                  # Banner de práctica
├── main.py                  # Menú y modos de control (jog, mover N, barrido, homing, info)
├── lib/
│   ├── stepper_a4988.py     # Driver para A4988/DRV8825 (STEP/DIR)
│   └── stepper_uln2003.py   # Driver para ULN2003 (4-wire)
├── PINES.md                 # Mapeo de pines y comparación ESP32 vs RP2040
├── pymakr.conf              # Configuración de Pymakr
├── assets/
│   ├── wiring_a4988.mmd     # Diagrama Mermaid: RP2040 → A4988 → NEMA 17
│   └── wiring_uln2003.mmd   # Diagrama Mermaid: RP2040 → ULN2003 → 28BYJ-48
└── docs/
    └── oscilograma.md       # Guía de medición y registro de señales
```

---

## Ventajas del RP2040 para control de steppers

### 1. **PIO (Programmable I/O)**
- **Qué es**: 2 bloques PIO con 4 máquinas de estado cada uno
- **Ventaja**: Genera pulsos STEP ultra-precisos independientes de la CPU
- **Timing**: <10 ns de jitter vs ~10 µs en ESP32
- **Futuro**: Biblioteca PIO para control simultáneo de múltiples motores

### 2. **GPIO de alta velocidad**
- **Switching típico**: 2-4 MHz (vs ~1 MHz ESP32)
- **Importante para**: Microstepping 1/16 a altas RPM (>200 RPM)
- **Sin glitches**: Lógica GPIO determinística

### 3. **Bajo consumo en idle**
- **Sleep mode con PIO activo**: Steppers funcionan mientras CPU duerme
- **Útil para**: Proyectos con batería (ej. timelapses, cámaras motorizadas)

### 4. **Más GPIO disponibles**
- **RP2040**: 30 GPIO (GP0-GP29, excluyendo reservados)
- **ESP32**: ~28 útiles (algunos reservados para flash, strapping)
- **Ventaja**: Control de múltiples motores + sensores sin multiplexación

### 5. **Sin interferencia WiFi/BLE**
- **RP2040 estándar**: No tiene WiFi (sin interferencia RF en control preciso)
- **Pico W**: WiFi opcional, desactivable completamente
- **Resultado**: Timing más estable en ambientes ruidosos

---

## Comparación ESP32 vs RP2040

| Característica | ESP32 | RP2040 | Ventaja |
|----------------|-------|--------|---------|
| **Pines GPIO** | ~28 útiles | 30 | RP2040 |
| **Jitter PWM** | ~10 µs | <10 ns (PIO) | ✅ **RP2040** |
| **Velocidad GPIO** | ~1 MHz | 2-4 MHz | ✅ **RP2040** |
| **Multitarea** | FreeRTOS + WiFi (interrupciones) | Dual-core simétrico | RP2040 (más predecible) |
| **Consumo idle** | ~20 mA (WiFi activo) | ~2 mA (sin WiFi) | ✅ **RP2040** |
| **PIO** | No disponible | 8 state machines | ✅ **RP2040** (único) |
| **WiFi/BLE** | ✅ Integrado | ❌ Solo Pico W | ESP32 |
| **Costo** | ~$5 USD | ~$4 USD (Pico) | RP2040 |

**Conclusión**: RP2040 es superior para control de steppers cuando se requiere **precisión**, **multiples motores** o **proyectos con batería**. ESP32 es mejor si necesitas **conectividad inalámbrica**.

---

## Proyectos avanzados

### 1. **Control multi-motor con PIO**
- Controla hasta **8 motores simultáneamente** (1 PIO state machine por motor)
- Sin jitter, sin bloqueo de CPU
- Ideal para: CNC, brazos robóticos, impresoras 3D

### 2. **Homing con encoder óptico**
- Usa sensor óptico en lugar de microswitch
- PIO lee pulsos del encoder mientras mueve el motor
- Precisión: <0.1° (con microstepping 1/16)

### 3. **Timelapses motorizados**
- RP2040 en sleep mode entre movimientos
- PIO mueve el motor sin despertar CPU
- Autonomía: días con batería LiPo 2000 mAh

### 4. **Comunicación CAN para steppers**
- Usa PIO para implementar protocolo CAN
- Red de múltiples RP2040 controlando steppers
- Ideal para: Robótica modular

---

## Solución de problemas

### Motor no se mueve (A4988):
- ✅ Verifica **GND común** entre RP2040 y fuente externa
- ✅ Mide **VMOT** (debe ser ~12 V en terminales del driver)
- ✅ Revisa cableado de bobinas (A1-A2, B1-B2 del motor)
- ✅ Ajusta **VREF** (potenciómetro del driver) si corriente es muy baja

### Motor vibra pero no gira (A4988):
- ✅ Aumenta **VREF** (corriente insuficiente)
- ✅ Reduce **RPM** (motor pierde pasos a alta velocidad)
- ✅ Verifica **secuencia de cableado** de bobinas (intercambia A1-A2 si es necesario)

### Motor no gira en ULN2003:
- ✅ Verifica cable de 5 pines del motor (orden correcto en conectores)
- ✅ Mide **5V en VCC** del driver
- ✅ Verifica pines **GP26, GP27, GP28, GP22** (no GPIO33 como en ESP32)
- ✅ Prueba con `motor.step(100)` en REPL directamente

### Endstop no detecta:
- ✅ Configura **pull-up interno** en código (`Pin(4, Pin.IN, Pin.PULL_UP)`)
- ✅ Mide voltaje en **GP4**: debe ser **3.3V sin presionar**, **0V al presionar**
- ✅ Verifica que el microswitch sea **Normalmente Abierto (NO)**
- ✅ Reduce velocidad de homing (20 RPM máximo para evitar rebotes)

### Driver A4988 se calienta excesivamente:
- ✅ **VREF demasiado alto** → ajusta a valor correcto para tu motor
- ✅ Añade **disipador térmico** al chip del driver
- ✅ Mejora **ventilación** del área de trabajo
- ✅ Desactiva ENABLE cuando no uses el motor

---

## Tips y trucos

### Cálculo de RPM a partir del intervalo:
$$
\text{RPM} = \frac{60 \times 10^6}{\text{interval\_us} \times \text{steps\_per\_rev}}
$$

**Ejemplo**: Intervalo 5000 µs, 200 pasos/rev → $\frac{60 \times 10^6}{5000 \times 200} = 60$ RPM

### Relación de reducción del 28BYJ-48:
- Interno: **64:1** (engranajes planetarios)
- Por eso 4096 pasos = 1 vuelta del eje de salida (no del motor interno)

### Microstepping en A4988:
- MS1=LOW, MS2=LOW, MS3=LOW → **1/1** (200 pasos/rev)
- MS1=HIGH, MS2=LOW, MS3=LOW → **1/2** (400 pasos/rev)
- MS1=HIGH, MS2=HIGH, MS3=HIGH → **1/16** (3200 pasos/rev)

### Ahorro de energía:
```python
# Desactiva motor cuando no lo uses
motor.disable()  # A4988
# o
motor.release()  # ULN2003
```

---

> **Nota final**: Esta práctica es la base para proyectos CNC, impresoras 3D, robótica y automatización. Dominar el control de steppers te abre las puertas a infinitas aplicaciones de control de movimiento preciso. 🚀
