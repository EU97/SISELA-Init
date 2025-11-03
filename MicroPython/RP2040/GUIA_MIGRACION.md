# 🔄 GUÍA MAESTRA DE MIGRACIÓN ESP32 → RP2040

## 📚 Resumen Ejecutivo

Este documento proporciona las equivalencias y patrones necesarios para traducir las prácticas P3-P8 de ESP32 a RP2040.

---

## 🎯 Patrones Completados (Referencia)

### ✅ P1 - GPIO Básico
**Cambios aplicados**:
- `GPIO2` → `GP25` (LED onboard)
- `GPIO4/5` → `GP16/GP17` (LEDs externos)
- `GPIO13/14` → `GP14/GP15` (Botones)
- Código idéntico excepto números de pin

### ✅ P2 - ADC
**Cambios aplicados**:
- `ADC(Pin(34))` → `ADC(26)` (GP26 = ADC0)
- `adc.atten(ADC.ATTN_11DB)` → *eliminar* (no necesario en RP2040)
- `adc.width(ADC.WIDTH_12BIT)` → *eliminar* (no necesario en RP2040)
- `adc.read()` → `adc.read_u16()`
- `ADC_MAX = 4095` → `ADC_MAX = 65535`

---

## 🔧 P3 - Comunicación Serial (Pendiente)

### UART
**ESP32**:
```python
from machine import UART
uart = UART(1, baudrate=9600, tx=17, rx=16)
```

**RP2040**:
```python
from machine import UART, Pin
# UART0: TX=GP0, RX=GP1 (por defecto)
# UART1: TX=GP4, RX=GP5 (por defecto)
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
# O con pines alternativos (consultar datasheet)
```

### I2C
**ESP32**:
```python
from machine import I2C, Pin
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
```

**RP2040**:
```python
from machine import I2C, Pin
# I2C0: SCL=GP1, SDA=GP0 (o SCL=GP5, SDA=GP4, SCL=GP9, SDA=GP8...)
# I2C1: SCL=GP3, SDA=GP2 (o SCL=GP7, SDA=GP6, SCL=GP11, SDA=GP10...)
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)
```

### SPI
**ESP32**:
```python
from machine import SPI, Pin
spi = SPI(1, baudrate=1000000, polarity=0, phase=0, 
          sck=Pin(18), mosi=Pin(23), miso=Pin(19))
```

**RP2040**:
```python
from machine import SPI, Pin
# SPI0: SCK=GP2/6/18, MOSI=GP3/7/19, MISO=GP0/4/16
# SPI1: SCK=GP10/14/26, MOSI=GP11/15/27, MISO=GP8/12/24
spi = SPI(0, baudrate=1000000, polarity=0, phase=0,
          sck=Pin(2), mosi=Pin(3), miso=Pin(0))
```

### NTC con divisor resistivo
- **Pin ADC**: `GPIO34` → `GP26` (ADC0)
- **Código de cálculo**: Idéntico, solo cambia la lectura ADC

---

## ⚡ P4 - Interrupciones (Pendiente)

### Interrupción de pin
**Código casi idéntico**:
```python
from machine import Pin

def callback(pin):
    print(f"Interrupción en {pin}")

btn = Pin(14, Pin.IN, Pin.PULL_UP)
btn.irq(trigger=Pin.IRQ_FALLING, handler=callback)
```

**Diferencias**:
- RP2040: Interrupciones más deterministas (mejor timing)
- Mismo API: `Pin.IRQ_RISING`, `Pin.IRQ_FALLING`, `Pin.IRQ_RISING | Pin.IRQ_FALLING`

### Timers
**ESP32**:
```python
from machine import Timer
tim = Timer(0)
tim.init(period=1000, mode=Timer.PERIODIC, callback=lambda t: print("tick"))
```

**RP2040**:
```python
from machine import Timer
tim = Timer()
tim.init(period=1000, mode=Timer.PERIODIC, callback=lambda t: print("tick"))
```

**Diferencia**: RP2040 no requiere ID de timer (solo hay uno global en MicroPython)

---

## 🎛️ P5 - Servos PWM (Pendiente)

### Configuración PWM
**ESP32**:
```python
from machine import Pin, PWM
servo = PWM(Pin(25), freq=50)
servo.duty_u16(valor)  # 1638 (1ms) a 8191 (2ms) aprox
```

**RP2040**:
```python
from machine import Pin, PWM
servo = PWM(Pin(16))
servo.freq(50)
servo.duty_u16(valor)  # Mismo rango
```

**Diferencia**: Sintaxis idéntica, pero RP2040 tiene límite de 8 slices PWM (16 canales total, 2 por slice)

### Cálculo duty_u16 para servos
```python
def angle_to_duty(angle, min_us=500, max_us=2500):
    """Convierte ángulo 0-180° a duty_u16 para servo"""
    # Servo típico: 0.5-2.5ms (500-2500µs) a 50Hz (20ms periodo)
    pulse_us = min_us + (max_us - min_us) * (angle / 180.0)
    # duty_u16: 65535 = 20000µs (periodo completo a 50Hz)
    duty = int((pulse_us / 20000.0) * 65535)
    return duty
```

**Igual para ESP32 y RP2040**

---

## 🚗 P6 - Motor PWM (Pendiente)

### PWM para motor
**Código idéntico** entre ESP32 y RP2040:
```python
from machine import Pin, PWM

motor = PWM(Pin(18))
motor.freq(1000)  # 1 kHz típico para motores DC
motor.duty_u16(32768)  # 50% duty
```

**Hardware**:
- MOSFET N: IRF540, 2N7000, etc.
- Diodo flyback: 1N4007, 1N4148
- Mismo circuito para ambas placas

---

## 🔄 P7 - Steppers (Pendiente)

### Driver A4988/DRV8825
**ESP32**:
```python
step_pin = Pin(19, Pin.OUT)
dir_pin = Pin(21, Pin.OUT)
en_pin = Pin(5, Pin.OUT)
```

**RP2040**:
```python
step_pin = Pin(2, Pin.OUT)
dir_pin = Pin(3, Pin.OUT)
en_pin = Pin(4, Pin.OUT)
```

**Lógica de control**: Idéntica
- Pulsos en STEP para avanzar
- DIR para dirección (HIGH/LOW)
- EN para habilitar (LOW activo)

### Driver ULN2003 (unipolar)
**Código idéntico**, solo cambia pines:
```python
# ESP32: [19, 21, 22, 23]
# RP2040: [2, 3, 4, 5]
pins = [Pin(i, Pin.OUT) for i in [2, 3, 4, 5]]
```

### Clase base (lib/stepper_a4988.py)
**Sin cambios** - compatible con ambos

---

## ✈️ P8 - Sistema Integrado Aeronáutico (Pendiente)

### Mapeo de pines completo

| Subsistema | ESP32 | RP2040 |
|------------|-------|--------|
| **Sensores ADC** | | |
| Altitud | GPIO34 (ADC1_CH6) | GP26 (ADC0) |
| Velocidad | GPIO35 (ADC1_CH7) | GP27 (ADC1) |
| Actitud | GPIO32 (ADC1_CH4) | GP28 (ADC2) |
| Luz | GPIO33 (ADC1_CH5) | *Eliminar* (solo 3 ADC) |
| **Servos** | | |
| Alerón | GPIO25 | GP16 |
| Elevador | GPIO26 | GP17 |
| **Motor PWM** | | |
| Hélice | GPIO18 | GP18 |
| **Stepper** | | |
| STEP | GPIO19 | GP2 |
| DIR | GPIO21 | GP3 |
| EN | GPIO5 | GP4 |
| **Endstop** | | |
| Tren aterrizaje | GPIO4 | GP5 |

### Modificaciones necesarias en lib/sensors.py
```python
# ESP32: 4 sensores
SENSOR_PINS = {
    'altitude': 34,
    'speed': 35,
    'attitude': 32,
    'light': 33  # ← Eliminar en RP2040
}

# RP2040: 3 sensores (sin 'light')
SENSOR_PINS = {
    'altitude': 26,  # ADC0
    'speed': 27,     # ADC1
    'attitude': 28   # ADC2
}
```

### Cambios en __init__ de FlightSensors
```python
# ESP32
for name, pin in self.pins.items():
    adc = ADC(Pin(pin))
    adc.atten(ADC.ATTN_11DB)
    adc.width(ADC.WIDTH_12BIT)
    self.adcs[name] = adc

# RP2040
for name, pin in self.pins.items():
    adc = ADC(pin)  # Directo, sin Pin()
    self.adcs[name] = adc
```

### Cambios en read_all()
```python
# ESP32
raw = adc.read()  # 0-4095
scaled = (raw / 4095) * scale['max']

# RP2040
raw = adc.read_u16()  # 0-65535
scaled = (raw / 65535) * scale['max']
```

### Limitación de memoria
**RP2040 tiene menos RAM (264KB vs 520KB)**:
- Reducir buffers de telemetría
- Simplificar autopiloto
- Considerar eliminar un modo si es necesario

---

## 📊 Tabla de Conversión Rápida

### Pines Comunes

| Función | ESP32 | RP2040 |
|---------|-------|--------|
| LED onboard | GPIO2 | GP25 |
| ADC 1 | GPIO34 | GP26 |
| ADC 2 | GPIO35 | GP27 |
| ADC 3 | GPIO32 | GP28 |
| PWM genérico | GPIO18 | GP18 |
| I2C SDA | GPIO21 | GP0/2/4... |
| I2C SCL | GPIO22 | GP1/3/5... |
| UART TX | GPIO17 | GP0/4/8... |
| UART RX | GPIO16 | GP1/5/9... |

### Código ADC

| Operación | ESP32 | RP2040 |
|-----------|-------|--------|
| Import | `from machine import ADC, Pin` | `from machine import ADC` |
| Init | `ADC(Pin(34))` | `ADC(26)` |
| Config | `.atten()`, `.width()` | *No necesario* |
| Read | `.read()` → 0-4095 | `.read_u16()` → 0-65535 |
| Voltaje | `(raw/4095)*3.3` | `(raw/65535)*3.3` |

### Código PWM

| Operación | ESP32 | RP2040 |
|-----------|-------|--------|
| Init | `PWM(Pin(25), freq=50)` | `pwm = PWM(Pin(16)); pwm.freq(50)` |
| Duty | `.duty_u16(val)` | `.duty_u16(val)` |
| Freq | `.freq(f)` | `.freq(f)` |

---

## 🛠️ Procedimiento de Migración (P3-P8)

### Paso 1: Copiar estructura
```powershell
# Desde ESP32 a RP2040
Copy-Item -Recurse MicroPython\ESP32\Px\* MicroPython\RP2040\Px\
```

### Paso 2: Actualizar boot.py
Cambiar `ESP32` por `RP2040` en el mensaje

### Paso 3: Actualizar PINES.md
- Reemplazar tabla de pines
- Añadir sección "Comparativa ESP32 vs RP2040"
- Actualizar diagramas Mermaid

### Paso 4: Actualizar README.md
- Añadir sección "Diferencias clave vs ESP32"
- Actualizar procedimiento de flasheo
- Actualizar troubleshooting específico de RP2040

### Paso 5: Actualizar main.py
- **Pines**: Cambiar todos los números (ver tabla arriba)
- **ADC**: Cambiar `ADC(Pin(x))` → `ADC(x)` y `.read()` → `.read_u16()`
- **ADC config**: Eliminar `.atten()` y `.width()`
- **Constantes**: `ADC_MAX = 4095` → `65535`

### Paso 6: Actualizar lib/*.py (si aplica)
- Mismas modificaciones que main.py
- Verificar imports

### Paso 7: Actualizar tools/*.py
- Código Python PC: Sin cambios (solo afecta formato de datos)

### Paso 8: Probar
- Flashear MicroPython en Pico
- Subir archivos con Thonny
- Validar funcionamiento

---

## 🎯 Prioridades Sugeridas

1. **P3** (Comunicación) - Base para muchos sensores
2. **P4** (Interrupciones) - Útil para P8
3. **P5-P7** (Actuadores) - Críticos para P8
4. **P8** (Integrado) - Proyecto final

---

## 📝 Notas Finales

- **Memoria**: RP2040 tiene menos RAM; optimiza buffers en P8
- **WiFi**: RP2040 estándar no tiene WiFi (usar Pico W si necesitas)
- **ADC**: RP2040 tiene solo 3 canales; elimina sensor de luz en P8
- **USB**: RP2040 tiene USB nativo; mejor para REPL que ESP32

---

**Documento creado**: Noviembre 2025  
**Autor**: EU97/SISELA-Init  
**Basado en**: Prácticas P1-P8 ESP32 completadas