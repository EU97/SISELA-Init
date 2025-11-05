# Guía Rápida — SISELA-CPP

## 🚀 Inicio rápido

### 1. Seleccionar práctica

Edita `platformio.ini`:
```ini
build_flags = -DPRACTICE=5 -DSTEPPER_A4988
```

Cambia `5` por el número de práctica deseada (1-8).

### 2. Compilar

```bash
# ESP32
pio run -e esp32dev

# RP2040
pio run -e pico
```

### 3. Flashear

```bash
# ESP32
pio run -e esp32dev -t upload

# RP2040
pio run -e pico -t upload
```

### 4. Monitor serial

```bash
pio device monitor
# o
pio run -e esp32dev -t upload -t monitor
```

---

## 📌 Pines por práctica

### P2: Potenciómetro
- **ESP32**: ADC en GPIO34
- **RP2040**: ADC en GP26

### P5: Servo PWM
- **ESP32**: Servo → GPIO18; ADC opcional → GPIO34
- **RP2040**: Servo → GP18; ADC opcional → GP26
- **Conexiones**:
  - Servo señal (amarillo/blanco) → GPIO18/GP18
  - Servo VCC (rojo) → 5V externa
  - Servo GND (marrón/negro) → GND común
  - Potenciómetro: cursor → GPIO34/GP26; extremos → 3V3 y GND

### P6: PWM + Transistor
- **ESP32**: PWM → GPIO18; ADC opcional → GPIO34
- **RP2040**: PWM → GP18; ADC opcional → GP26
- **Conexiones**:
  - GPIO18/GP18 → R 220Ω → Compuerta MOSFET (G)
  - MOSFET Drain (D) → LED (con R 220Ω en serie) → GND
  - MOSFET Source (S) → GND
  - **GND común obligatorio**

### P8: Sistema integrado
Ver matriz completa en `README.md` o `STATUS.txt`.

---

## 🎮 Control interactivo

### P5: Servo
- **Modo 1** (default): Barrido automático
- **Modo 2**: Control por potenciómetro
- Cambiar modo: Envía `1` o `2` por serial

### P6: PWM
- **Modo 1** (default): Rampa automática
- **Modo 2**: Control manual por serial
- **Modo 3**: Control por potenciómetro
- Cambiar modo: Envía `1`, `2` o `3` por serial
- En modo 2: Envía valores `0` a `100` para ajustar duty

---

## ⚙️ Opciones avanzadas

### Cambiar driver stepper (P7, P8)
```ini
# A4988 (default)
build_flags = -DPRACTICE=8 -DSTEPPER_A4988

# ULN2003
build_flags = -DPRACTICE=8 -DSTEPPER_ULN2003
```

### Entornos específicos
Descomenta en `platformio.ini`:
```ini
[env:esp32_p5]
platform = espressif32
board = esp32dev
build_flags = -DPRACTICE=5 -DSTEPPER_A4988 -DARDUINO_ARCH_ESP32
lib_deps = madhephaestus/ESP32Servo@^3.0.5
```

Luego compila:
```bash
pio run -e esp32_p5
```

---

## 🔧 Solución de problemas

### Error: `'Servo' was not declared`
**Solución**: Asegúrate de que `lib_deps` está en `[env:esp32dev]`:
```ini
[env:esp32dev]
lib_deps = 
    madhephaestus/ESP32Servo@^3.0.5
```

### Error: `'analogWriteFreq' was not declared` (RP2040)
**Solución**: Actualiza platform RP2040:
```bash
pio platform update raspberrypi
```

### IntelliSense muestra errores pero compila bien
**Normal**: IntelliSense no tiene el contexto completo de PlatformIO. Si compila con `pio run`, ignora los warnings de IDE.

### Servo no se mueve (P5)
1. Verifica alimentación 5V al servo (VCC rojo)
2. Verifica GND común entre servo y microcontrolador
3. Verifica señal conectada a GPIO18/GP18
4. Monitor serial debe mostrar "Ángulo: X" periódicamente

### LED no varía brillo (P6)
1. Verifica resistencia 220Ω entre GPIO y compuerta MOSFET
2. Verifica MOSFET es de compuerta lógica (Vgs(th) < 2V)
3. Verifica GND común
4. Monitor serial debe mostrar "Duty: X %" periódicamente

---

## 📂 Archivos importantes

- `platformio.ini` — Configuración de práctica y plataforma
- `include/pins/pins_esp32.h` — Mapa de pines ESP32
- `include/pins/pins_rp2040.h` — Mapa de pines RP2040
- `src/practices/p*.cpp` — Implementación de cada práctica
- `src/common/*.h` — Drivers reutilizables
- `README.md` — Documentación completa
- `STATUS.txt` — Estado visual del proyecto
- `IMPLEMENTATION_STATUS.md` — Detalles de implementación

---

## 📚 Referencias

- [ESP32Servo Library](https://github.com/madhephaestus/ESP32Servo)
- [Arduino-Pico](https://github.com/earlephilhower/arduino-pico)
- [PlatformIO Docs](https://docs.platformio.org/)
- Documentación original MicroPython: `MicroPython/ESP32/` y `MicroPython/RP2040/`

---

## ✅ Checklist pre-compilación

- [ ] Práctica seleccionada en `platformio.ini` (PRACTICE=N)
- [ ] Driver stepper correcto si aplica (A4988/ULN2003)
- [ ] PlatformIO Core instalado (`pio --version`)
- [ ] USB conectado y puerto COM visible

## ✅ Checklist pre-hardware (P5 Servo)

- [ ] Servo R/C estándar (SG90, MG90S, MG996R, etc.)
- [ ] Fuente 5V externa >500 mA (para servos medianos/grandes)
- [ ] Cable amarillo/blanco a GPIO18/GP18
- [ ] Cable rojo a 5V (fuente externa o VSYS si servo pequeño)
- [ ] Cable marrón/negro a GND (común con microcontrolador)
- [ ] Potenciómetro 10kΩ (opcional): cursor a GPIO34/GP26, extremos a 3V3/GND

## ✅ Checklist pre-hardware (P6 PWM)

- [ ] MOSFET canal N (AO3400, IRLZ44N) o BJT NPN (2N2222, TIP120)
- [ ] Resistencia 220Ω (compuerta/base)
- [ ] LED + resistencia 220Ω (carga de prueba)
- [ ] Diodo flyback 1N5819/1N4007 (si carga es motor/relé)
- [ ] Fuente externa para carga si >100 mA
- [ ] GND común entre micro y fuente externa

---

**¡Listo para compilar y flashear! 🎉**
