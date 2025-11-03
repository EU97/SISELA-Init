# PINES — P7 Motores a pasos (RP2040)

## 🔄 Configuraciones soportadas

Esta práctica soporta **dos controladores de motores paso a paso** diferentes. Elige la configuración que se adapte a tu motor:

### 1) A4988/DRV8825 + NEMA 17 (Bipolar)

**Conexiones RP2040 → Driver:**

| Señal    | RP2040 (GP) | Driver Pin | Notas |
|----------|-------------|------------|-------|
| **STEP** | **GP18**    | STEP       | Pulso de paso (rising edge) |
| **DIR**  | **GP19**    | DIR        | Dirección (HIGH=CW, LOW=CCW) |
| **EN**   | **GP5**     | ENABLE     | Activación (LOW=habilitado) |
| GND      | GND         | GND        | ⚠️ **Común obligatorio** |

**Alimentación del motor:**
- **VMOT**: 12 V (típico para NEMA 17), hasta 2A
- **Fuente externa** requerida (⚠️ NO conectar a VSYS del RP2040)
- **GND común** entre RP2040 y fuente del motor (crítico)

**Microstepping (opcional):**
- MS1, MS2, MS3 → Configuran resolución (1/1, 1/2, 1/4, 1/8, 1/16)
- Por defecto: 200 pasos/revolución (1.8° por paso)
- Con 1/16: 3200 pasos/revolución (0.1125° por paso)

---

### 2) ULN2003 + 28BYJ-48 (Unipolar, 5V)

**Conexiones RP2040 → Driver:**

| Señal | RP2040 (GP) | ULN2003 Pin | ESP32 (GPIO) | Notas |
|-------|-------------|-------------|--------------|-------|
| **IN1** | **GP26**  | IN1         | GPIO26       | Sin cambio |
| **IN2** | **GP27**  | IN2         | GPIO25       | ⚠️ Cambio ESP32→RP2040 |
| **IN3** | **GP28**  | IN3         | GPIO33       | ⚠️ Cambio (GPIO33 no existe) |
| **IN4** | **GP22**  | IN4         | GPIO32       | ⚠️ Cambio ESP32→RP2040 |
| GND     | GND       | GND (–)     | GND          | Común |
| VCC     | VSYS      | VCC (+)     | 5V           | 5V, <500 mA |

**⚠️ CAMBIOS IMPORTANTES ESP32 → RP2040:**

| ESP32 | RP2040 | Razón del cambio |
|-------|--------|------------------|
| GPIO25 | **GP27** | Pin contiguo disponible |
| GPIO33 | **GP28** | ⚠️ GPIO33 no existe en RP2040 (máx GP28) |
| GPIO32 | **GP22** | Pin alternativo, misma funcionalidad |

**Alimentación:**
- **VCC Motor**: 5 V, ~200 mA (picos <500 mA)
- Opciones:
  - **VSYS** (si corriente <500 mA y conexión USB estable)
  - **Fuente externa 5V** (recomendado para proyectos con batería)

**Modos de secuencia:**
- **Full-step**: 2048 pasos/revolución (4 fases activas)
- **Half-step**: 4096 pasos/revolución (8 fases activas, más suave)

---

## 🔧 Fin de carrera (opcional, ambos drivers)

| Señal | RP2040 (GP) | ESP32 (GPIO) | Configuración |
|-------|-------------|--------------|---------------|
| **ENDSTOP** | **GP4** | GPIO4 | Pull-up interno + contacto a GND |

**Conexión física:**
- Microswitch / sensor óptico: contacto **Normalmente Abierto (NO)**
- Cuando se activa → conecta **GP4** a **GND** (flanco descendente)
- Pull-up interno configurado en software (`Pin.PULL_UP`)

---

## 📊 Comparación de configuraciones

| Característica | A4988 + NEMA 17 | ULN2003 + 28BYJ-48 |
|----------------|-----------------|---------------------|
| **Torque** | Alto (típico 4.4 kg·cm) | Bajo (típico 0.4 kg·cm) |
| **Velocidad** | Alta (hasta 600 RPM sin carga) | Baja (máx ~15 RPM) |
| **Pasos/rev** | 200 (configurable con MS) | 2048 (full) / 4096 (half) |
| **Voltaje motor** | 12 V (típico) | 5 V |
| **Corriente motor** | 1-2 A | 150-200 mA |
| **Fuente externa** | ⚠️ **Obligatoria** | Opcional (VSYS ok) |
| **GND común** | ⚠️ **Crítico** | Necesario |
| **Precisión** | Alta (con microstepping) | Media (pasos grandes) |
| **Aplicaciones** | CNC, robótica, impresoras 3D | Cámaras, displays, prototipos |

---

## 🚀 Ventajas del RP2040 para control de steppers

1. **PIO (Programmable I/O)**:
   - Puede generar pulsos STEP ultra-precisos independientes de la CPU
   - Timing determinístico (<10 ns de jitter) vs ~10 µs en ESP32
   - Futuras mejoras: biblioteca PIO para control multi-motor

2. **GPIO de alta velocidad**:
   - Conmutación típica: 2-4 MHz (vs ~1 MHz ESP32)
   - Importante para microstepping 1/16 a altas RPM

3. **Bajo consumo en idle**:
   - Modo sleep profundo con PIO activo (steppers funcionando)
   - Útil para proyectos con batería

4. **Sin ADC requirements**:
   - P7 no usa ADC (solo GPIO digitales)
   - RP2040 ofrece 30 GPIO vs 28 útiles del ESP32

---

## 🔍 Notas técnicas

### A4988/DRV8825:
- **Paso mínimo**: 5 µs (pulso STEP)
- **Intervalo mínimo**: 800 µs entre pasos (evita perder pasos)
- **ENABLE**: Activo en LOW (desactivar motor → HIGH)
- **Decaimiento**: Configurar DECAY para suavizar movimiento

### ULN2003 + 28BYJ-48:
- **Delay típico**: 3 ms entre pasos (motor lento)
- **Ratio reducción**: 64:1 interno (4096 pasos = 1 vuelta externa)
- **Secuencia half-step**: Más suave, menos torque instantáneo
- **Desactivar**: Llamar `release()` para evitar sobrecalentamiento

### Endstop:
- **Debounce**: Software (código verifica estabilidad)
- **Velocidad homing**: Reducida automáticamente (evita rebotes)

---

## 📝 Verificación rápida

### Checklist A4988:
- [ ] VMOT conectada a fuente externa (12 V)
- [ ] **GND común** entre RP2040 y fuente externa
- [ ] STEP, DIR, EN conectados a GP18, GP19, GP5
- [ ] Motor conectado a A1, A2, B1, B2 (bipolar)
- [ ] MS1-MS3 configurados (si se usa microstepping)

### Checklist ULN2003:
- [ ] GP26, GP27, GP28, GP22 conectados a IN1-IN4
- [ ] VCC motor a 5V (VSYS o fuente externa)
- [ ] GND común
- [ ] Conectores motor en orden correcto (cable de 5 pines)

Consulta los diagramas `assets/wiring_*.mmd` para más detalles visuales.
