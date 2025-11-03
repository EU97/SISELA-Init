# Práctica 8 — Sistema Integrado Sensor-Actuador con Énfasis Aeronáutico

## Objetivos

Esta práctica integra múltiples componentes de las prácticas anteriores (P1-P7) para construir un sistema completo de control aeronáutico que incluye:

- **Sensores**: Lectura de múltiples señales analógicas (ADC) para simular sensores de vuelo
- **Servomotores**: Control de superficies de control (alerones, timón, elevadores)
- **Actuadores PWM**: Control de potencia para motores/hélices
- **Motores a pasos**: Control de tren de aterrizaje o flaps
- **Interfaz avanzada**: Menú interactivo con monitoreo en tiempo real
- **Sistema de datos**: Registro y visualización de telemetría

## Materiales

### Hardware básico
- **ESP32** (con MicroPython instalado)
- **Cable USB** para programación y alimentación
- **Protoboard** y cables jumper

### Sensores (simular instrumentos de vuelo)
- **Potenciómetros** x3 (10kΩ): altitud, velocidad, actitud
- **LDR** (sensor de luz): sensor de luminosidad
- **Resistencias** 10kΩ para divisores de tensión

### Actuadores
- **Servomotor** x2: alerones, elevadores (control de vuelo)
- **Transistor N-MOSFET** (IRF540N o similar): control de motor/hélice
- **Motor DC** o LED de potencia: simular hélice
- **Diodo flyback** (1N4007): protección inductiva

### Motor a pasos (opcional)
- **NEMA 17** con driver A4988/DRV8825, O
- **28BYJ-48** con driver ULN2003
- **Fin de carrera** (endstop): límite de tren de aterrizaje

### Alimentación
- **Fuente externa** 5-12V para servos y motor DC
- **GND común** entre ESP32 y fuente externa

## Conexiones

### Sensores (ADC)
| Sensor | Pin ESP32 | Función |
|--------|-----------|---------|
| Pot 1 (Altitud) | GPIO34 | ADC1_CH6 |
| Pot 2 (Velocidad) | GPIO35 | ADC1_CH7 |
| Pot 3 (Actitud) | GPIO32 | ADC1_CH4 |
| LDR (Luz) | GPIO33 | ADC1_CH5 |

### Servomotores (PWM)
| Servo | Pin ESP32 | Función |
|-------|-----------|---------|
| Servo 1 (Alerón) | GPIO25 | PWM Canal 0 |
| Servo 2 (Elevador) | GPIO26 | PWM Canal 1 |

### Actuador PWM (Motor/Hélice)
| Señal | Pin ESP32 | Destino |
|-------|-----------|---------|
| PWM | GPIO18 | Gate MOSFET |
| GND | GND | Source MOSFET + GND fuente |

### Motor a pasos (Tren aterrizaje)
**Opción A4988/DRV8825:**
| Señal | Pin ESP32 |
|-------|-----------|
| STEP | GPIO19 |
| DIR | GPIO21 |
| EN | GPIO5 |

**Opción ULN2003:**
| Señal | Pin ESP32 |
|-------|-----------|
| IN1 | GPIO19 |
| IN2 | GPIO21 |
| IN3 | GPIO22 |
| IN4 | GPIO23 |

**Endstop:**
| Señal | Pin ESP32 |
|-------|-----------|
| Endstop | GPIO4 (pull-up) |

## Uso del sistema

### 1. Arranque del sistema
```python
python main.py
```

Al iniciar, el sistema mostrará:
- Banner de bienvenida con logo aeronáutico
- Inicialización de todos los subsistemas
- Estado de sensores y actuadores
- Menú principal

### 2. Menú principal
```
╔══════════════════════════════════════════════════════════════╗
║        SISTEMA DE CONTROL AERONÁUTICO - SISELA v1.0         ║
╠══════════════════════════════════════════════════════════════╣
║  [1] Panel de instrumentos (monitoreo en tiempo real)       ║
║  [2] Control manual de superficies                          ║
║  [3] Control de potencia (motor/hélice)                     ║
║  [4] Control de tren de aterrizaje                          ║
║  [5] Modo automático (piloto automático simple)             ║
║  [6] Registro de datos (telemetría)                         ║
║  [7] Diagnóstico del sistema                                ║
║  [8] Configuración                                          ║
║  [q] Salir                                                  ║
╚══════════════════════════════════════════════════════════════╝
```

### 3. Modo 1: Panel de instrumentos
Muestra en tiempo real:
```
┌─────────────────────────────────────────────────────────────┐
│ INSTRUMENTOS DE VUELO                       [m] Menú        │
├─────────────────────────────────────────────────────────────┤
│ Altitud:    1250 m  [████████░░] 82%                        │
│ Velocidad:   185 kt [███████░░░] 68%                        │
│ Actitud:    +12.5°  [██████████] 50%                        │
│ Luminosidad:  850   [████████░░] 85%                        │
├─────────────────────────────────────────────────────────────┤
│ SUPERFICIES DE CONTROL                                      │
│ Alerón:     45° [███████░░░]                                │
│ Elevador:   12° [█████░░░░░]                                │
│ Motor:      75% [████████░░]                                │
│ Tren:       EXTENDIDO                                       │
└─────────────────────────────────────────────────────────────┘
```

### 4. Modo 2: Control manual de superficies
Control interactivo de servos:
- `a/d`: Alerón izquierda/derecha
- `w/s`: Elevador arriba/abajo
- `0-9`: Ángulo directo (0-180°)
- `c`: Centrar todas las superficies
- `m`: Volver al menú

### 5. Modo 3: Control de potencia
Control del motor/hélice:
- `+/-`: Incrementar/decrementar potencia (5%)
- `0-9`: Potencia directa (0-100%)
- `SPACE`: Emergencia (corte motor)
- `m`: Volver al menú

### 6. Modo 4: Control de tren de aterrizaje
Gestión del tren con motor a pasos:
- `e`: Extender tren (hacia endstop)
- `r`: Retraer tren
- `h`: Homing (búsqueda de límite)
- `s`: Estado actual
- `m`: Volver al menú

### 7. Modo 5: Piloto automático simple
Sistema automatizado que:
- Lee sensores continuamente
- Ajusta superficies para mantener estabilidad
- Compensa cambios de altitud/actitud
- Mantiene potencia constante
- Registro automático de eventos

### 8. Modo 6: Registro de datos
Telemetría guardada en `/log_telemetry.csv`:
```csv
timestamp,altitude,speed,attitude,light,aileron,elevator,throttle,gear
0.125,1250,185,12.5,850,45,12,75,extended
0.250,1248,187,11.8,852,43,14,75,extended
...
```

### 9. Modo 7: Diagnóstico
Verifica el estado de todos los componentes:
- Test de sensores (rango válido)
- Test de servos (barrido completo)
- Test de motor PWM (rampa)
- Test de stepper (movimiento y endstop)
- Reporte de errores y advertencias

### 10. Modo 8: Configuración
Ajustes del sistema:
- Calibración de sensores (min/max ADC)
- Límites de servos (pulse width)
- Parámetros de motor (frecuencia PWM)
- Velocidad de stepper (RPM)
- Intervalo de actualización (Hz)

## Verificación

### 1. Sensores
- Variar potenciómetros: valores 0-4095 (ADC 12-bit)
- Cubrir LDR: luminosidad debe bajar
- Verificar conversión a unidades físicas

### 2. Servomotores
- Ángulo 0°: pulso ~1000 µs
- Ángulo 90°: pulso ~1500 µs
- Ángulo 180°: pulso ~2000 µs
- Frecuencia: 50 Hz

### 3. Motor PWM
- Duty 0%: motor apagado
- Duty 50%: velocidad media
- Duty 100%: velocidad máxima
- Frecuencia: 1 kHz

### 4. Motor a pasos
- Endstop: debe detener movimiento
- Homing: retrocede hasta endstop
- Pasos precisos: contar revoluciones

## Seguridad

⚠️ **IMPORTANTE**:
1. **GND común**: Conectar GND de ESP32, fuente externa y todos los componentes
2. **Alimentación externa**: Servos y motor DC desde fuente externa (no USB)
3. **Diodo flyback**: Obligatorio en cargas inductivas (motor DC)
4. **Límites mecánicos**: No forzar servos ni steppers más allá de sus límites
5. **Corriente**: Verificar que la fuente soporte la corriente total requerida
6. **Sobrecalentamiento**: Motores y drivers pueden calentarse, verificar disipadores
7. **Endstop**: Configurar correctamente para evitar colisiones mecánicas

## Estructura del proyecto

```
P8/
├── boot.py                 # Banner y configuración inicial
├── main.py                 # Sistema principal con menú
├── lib/
│   ├── sensors.py          # Clase para gestión de sensores ADC
│   ├── flight_controls.py  # Clase para servos (alerones, elevadores)
│   ├── propulsion.py       # Clase para motor PWM
│   ├── landing_gear.py     # Clase para tren a pasos
│   ├── autopilot.py        # Lógica de piloto automático
│   ├── telemetry.py        # Registro y visualización de datos
│   └── ui_components.py    # Componentes de interfaz (progress bars, etc.)
├── docs/
│   ├── oscilograma.md      # Formas de onda y mediciones
│   └── INTEGRATION.md      # Guía de integración de subsistemas
├── assets/
│   ├── wiring.mmd          # Diagrama completo del sistema
│   └── architecture.mmd    # Arquitectura del software
├── tools/
│   └── telemetry_viewer.py # Script para visualizar datos guardados
├── PINES.md                # Resumen de pines
└── README.md               # Esta documentación

```

## Expansiones futuras

- Comunicación Bluetooth/WiFi para telemetría remota
- Integración con IMU (MPU6050) para datos reales de actitud
- GPS para navegación
- Display OLED para panel integrado
- Control remoto (joystick/gamepad)
- Más modos de vuelo (despegue, aterrizaje, looping)

---

**Práctica 8** — Sistema Integrado Sensor-Actuador con Énfasis Aeronáutico  
*SISELA - Sistemas Embebidos en Laboratorio Aeroespacial*
