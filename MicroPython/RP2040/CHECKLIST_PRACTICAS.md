# 📋 CHECKLIST de Prácticas — MicroPython RP2040

Este documento lista todas las prácticas disponibles para RP2040 y su estado de completitud.

## 🎯 Resumen General

El RP2040 (Raspberry Pi Pico) es un microcontrolador de bajo costo con:
- **CPU**: Dual-core ARM Cortex-M0+ @ 133 MHz
- **RAM**: 264 KB SRAM
- **Flash**: 2 MB (en Pico estándar)
- **GPIO**: 26 pines multifunción (GP0-GP25 + GP26-GP28 para ADC)
- **ADC**: 3 canales externos + 1 interno (temp), 12 bits reales (read_u16 da 16 bits con padding)
- **PWM**: 8 slices, 16 canales PWM total
- **Comunicación**: 2× UART, 2× I2C, 2× SPI, USB 1.1
- **Voltaje**: 3.3V (NO tolerante a 5V)

---

## 📚 Prácticas Disponibles

### ✅ P1 — GPIO Básico y Entorno de Desarrollo
- **Estado**: ✅ Completa
- **Objetivos**:
  - Configurar entorno MicroPython en RP2040
  - Controlar LEDs y leer botones
  - Menú de 4 modos interactivo
- **Archivos**:
  - `boot.py` ✅
  - `main.py` ✅
  - `PINES.md` ✅
  - `README.md` ✅
- **Hardware**:
  - LED onboard (GP25)
  - 2× LEDs externos (GP16, GP17)
  - 2× Botones pull-up (GP14, GP15)

---

### 🔄 P2 — ADC (Adquisición de Datos Analógicos)
- **Estado**: 🔄 En desarrollo
- **Objetivos**:
  - Leer ADC en RP2040 (3 canales: GP26, GP27, GP28)
  - Filtrado con media móvil
  - Salida CSV para análisis
- **Diferencias vs ESP32**:
  - ESP32: 18 canales ADC, 12 bits (`read()` → 0-4095)
  - RP2040: 3 canales ADC, 12 bits reales (`read_u16()` → 0-65535, pero solo 12 bits significativos)
  - Conversión: `voltage = (adc.read_u16() / 65535) * 3.3`
- **Hardware**:
  - Potenciómetro 10kΩ conectado a GP26 (ADC0)
  - Vcc = 3.3V, GND común

---

### ⏳ P3 — Comunicación Serial (UART/I2C/SPI)
- **Estado**: ⏳ Pendiente
- **Objetivos**:
  - UART: Comunicación serial con sensor/PC
  - I2C: Leer sensor de temperatura NTC
  - SPI: Comunicación con periféricos externos
- **Diferencias vs ESP32**:
  - RP2040: 2× UART, 2× I2C, 2× SPI (vs múltiples en ESP32)
  - Pines predefinidos pero configurables mediante PIO

---

### ⏳ P4 — Interrupciones (IRQ)
- **Estado**: ⏳ Pendiente
- **Objetivos**:
  - Interrupciones por GPIO (rising/falling edge)
  - Timers con callback
  - Debouncing de botones
- **Diferencias vs ESP32**:
  - Sintaxis similar: `pin.irq(handler, Pin.IRQ_FALLING)`
  - RP2040 tiene interrupciones más deterministas por su arquitectura

---

### ⏳ P5 — Control de Servos (PWM)
- **Estado**: ⏳ Pendiente
- **Objetivos**:
  - Generar PWM para servos (50Hz, 1-2ms)
  - Control de múltiples servos
- **Diferencias vs ESP32**:
  - RP2040: 8 slices PWM, hasta 16 canales simultáneos
  - Frecuencia independiente por slice (2 canales por slice comparten frecuencia)
  - Uso: `PWM(Pin(GPxx)); pwm.freq(50); pwm.duty_u16(valor)`

---

### ⏳ P6 — Control de Motores DC (Transistor PWM)
- **Estado**: ⏳ Pendiente
- **Objetivos**:
  - PWM para control de velocidad de motor
  - Uso de transistores MOSFET/BJT como switch
- **Hardware similar a ESP32**:
  - MOSFET N (ej: 2N7000, IRF540)
  - Diodo flyback obligatorio
  - PWM típico 1-10kHz

---

### ⏳ P7 — Motores Paso a Paso
- **Estado**: ⏳ Pendiente
- **Objetivos**:
  - Control con drivers A4988 / DRV8825 / ULN2003
  - Generación de pulsos STEP/DIR
  - Endstops y homing
- **Diferencias vs ESP32**:
  - Código muy similar
  - Pines STEP/DIR/ENABLE siguen misma lógica

---

### ⏳ P8 — Sistema Integrado Aeronáutico
- **Estado**: ⏳ Pendiente
- **Objetivos**:
  - Integrar ADC (sensores), Servos, Motor PWM, Stepper
  - Menú de 8 modos completo
  - Sistema de telemetría
- **Arquitectura**:
  - Misma estructura de clases que ESP32
  - Adaptaciones de pines para RP2040
  - Considerar limitaciones de memoria (264KB RAM vs 520KB en ESP32)

---

## 🔧 Diferencias Clave: ESP32 vs RP2040

| Característica | ESP32 | RP2040 |
|----------------|-------|--------|
| **CPU** | Xtensa LX6/LX7 @ 240MHz | ARM Cortex-M0+ @ 133MHz |
| **Cores** | 1-2 (según modelo) | 2 |
| **RAM** | 520 KB | 264 KB |
| **GPIO** | 34-48 pines | 26 pines (GP0-GP25) |
| **ADC canales** | 18 canales, 12 bits | 3 canales + 1 temp, 12 bits |
| **ADC función** | `adc.read()` → 0-4095 | `adc.read_u16()` → 0-65535 |
| **PWM canales** | 16 canales | 16 canales (8 slices × 2) |
| **WiFi/BT** | ✅ Integrado | ❌ Requiere Pico W para WiFi |
| **USB** | Mediante chip externo | ✅ Nativo USB 1.1 |
| **Voltaje I/O** | 3.3V | 3.3V (NO 5V tolerante) |
| **Precio** | ~$5-10 | ~$4-6 |

---

## 📖 Guía de Migración Rápida

### Cambio de Pines
```python
# ESP32 → RP2040
GPIO2  → GP25  # LED onboard
GPIO4  → GP16  # GPIO genérico
GPIO34 → GP26  # ADC (ESP32: ADC1_CH6, RP2040: ADC0)
GPIO35 → GP27  # ADC (ESP32: ADC1_CH7, RP2040: ADC1)
GPIO32 → GP28  # ADC (ESP32: ADC1_CH4, RP2040: ADC2)
```

### Código ADC
```python
# ESP32
from machine import ADC, Pin
adc = ADC(Pin(34))
adc.atten(ADC.ATTN_11DB)
adc.width(ADC.WIDTH_12BIT)
raw = adc.read()  # 0-4095
voltage = (raw / 4095) * 3.3

# RP2040
from machine import ADC
adc = ADC(26)  # GP26 = ADC0
raw = adc.read_u16()  # 0-65535 (pero solo 12 bits reales)
voltage = (raw / 65535) * 3.3
```

### Código PWM
```python
# ESP32 y RP2040 son muy similares
from machine import Pin, PWM
pwm = PWM(Pin(16))
pwm.freq(1000)        # 1 kHz
pwm.duty_u16(32768)   # 50% duty cycle
```

---

## ✅ Checklist de Verificación por Práctica

### P1 — GPIO Básico
- [x] boot.py creado
- [x] main.py con 4 modos funcionales
- [x] PINES.md con tabla de pines
- [x] README.md completo
- [ ] assets/wiring.mmd (diagrama Mermaid)
- [ ] docs/oscilograma.md

### P2 — ADC
- [ ] main.py adaptado a read_u16()
- [ ] Calibración para 3 canales (GP26-28)
- [ ] Herramientas de visualización CSV
- [ ] README.md con notas de RP2040

### P3-P8 — Resto de prácticas
- [ ] Código adaptado
- [ ] Documentación actualizada
- [ ] Diagramas de conexión
- [ ] Pruebas funcionales

---

## 🚀 Próximos Pasos

1. **Completar P2**: Adaptar ADC de 12 bits con read_u16()
2. **P3-P4**: Comunicación serial e interrupciones
3. **P5-P7**: Actuadores (servos, motores, steppers)
4. **P8**: Sistema integrado completo
5. **Documentación**: Crear guías comparativas y troubleshooting

---

## 📚 Recursos

- **MicroPython RP2040**: https://docs.micropython.org/en/latest/rp2/quickref.html
- **Raspberry Pi Pico Datasheet**: https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf
- **RP2040 Datasheet**: https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf
- **MicroPython Forum**: https://forum.micropython.org/
- **Thonny IDE**: https://thonny.org

---

**Última actualización**: Noviembre 2025  
**Mantenedor**: EU97/SISELA-Init
