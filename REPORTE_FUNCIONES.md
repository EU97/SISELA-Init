# Reporte de Funciones — Prácticas MicroPython RP2040

Este documento describe las funciones principales implementadas en cada práctica del repositorio SISELA-Init para la plataforma RP2040 con MicroPython.

---

## Práctica 1: Fundamentos de MCUs y Entorno de Desarrollo Aeronáutico

**Archivo:** `MicroPython/RP2040/P1/main.py`

### Funciones principales

#### `make_led(pin_no)`
Crea un objeto Pin configurado como salida para control de LED.
- **Parámetros:** `pin_no` (int) - Número de pin GPIO
- **Retorna:** Objeto `Pin` configurado como salida
- **Uso:** Inicialización de LEDs onboard y externos

#### `make_button(pin_no)`
Crea un objeto Pin configurado como entrada con pull-up interno para botones.
- **Parámetros:** `pin_no` (int) - Número de pin GPIO
- **Retorna:** Objeto `Pin` configurado como entrada con pull-up
- **Uso:** Lectura de botones (activo LOW)

#### `read_line_timeout(timeout_ms=0, poll_obj=None)`
Lee una línea del REPL con timeout no bloqueante.
- **Parámetros:** 
  - `timeout_ms` (int) - Tiempo de espera en milisegundos
  - `poll_obj` (Poll, opcional) - Objeto poll reutilizable
- **Retorna:** `str` o `None`
- **Uso:** Interacción con menú interactivo

#### `menu_select(timeout_s=8)`
Muestra menú de modos y espera selección con timeout.
- **Parámetros:** `timeout_s` (int) - Timeout en segundos
- **Retorna:** `int` - Modo seleccionado (1-4)
- **Uso:** Selección de modo de operación

#### `check_menu_break(poll_obj=None)`
Verifica si el usuario escribió 'm' para regresar al menú.
- **Parámetros:** `poll_obj` (Poll, opcional)
- **Retorna:** `bool` - True si se detecta 'm'
- **Uso:** Salida de modos hacia menú principal

#### `set_all_leds(v)`
Enciende o apaga todos los LEDs simultáneamente.
- **Parámetros:** `v` (bool) - Estado deseado
- **Uso:** Control de múltiples LEDs en modo integrado

#### `blink_led1(period_s=1.0)`
Modo 1: Parpadeo simple del LED onboard (GP25).
- **Parámetros:** `period_s` (float) - Periodo de parpadeo
- **Uso:** Verificación básica de GPIO y temporización

#### `chaser(period_s=0.3)`
Modo 2: Secuencia tipo "chaser" en 3 LEDs (GP25, GP16, GP17).
- **Parámetros:** `period_s` (float) - Tiempo entre transiciones
- **Uso:** Demostración de control secuencial de GPIO

#### `monitor_inputs(sample_ms=200)`
Modo 3: Monitorea estado de botones y refleja en LEDs.
- **Parámetros:** `sample_ms` (int) - Periodo de muestreo
- **Uso:** Lectura de entradas digitales con debounce

#### `integrated_mode()`
Modo 4: Control integrado donde BTN1 alterna patrón y BTN2 cicla velocidad.
- **Uso:** Demostración de sistema reactivo con múltiples entradas/salidas

### Configuración de pines (RP2040)
- **LED1:** GP25 (LED onboard)
- **LED2:** GP16 (LED externo)
- **LED3:** GP17 (LED externo)
- **BTN1:** GP14 (pull-up interno)
- **BTN2:** GP15 (pull-up interno)

---

## Práctica 2: Adquisición de Datos Analógicos (ADC) - Sensor de Posición

**Archivo:** `MicroPython/RP2040/P2/main.py`

### Funciones principales

#### `raw_to_voltage(raw: int) -> float`
Convierte lectura ADC de 16 bits a voltaje (0-3.3V).
- **Parámetros:** `raw` (int) - Valor ADC (0-65535)
- **Retorna:** `float` - Voltaje en V
- **Fórmula:** `(raw / 65535) * 3.3`
- **Diferencia RP2040 vs ESP32:** RP2040 usa `read_u16()` con rango 0-65535; ESP32 usa `read()` con 0-4095

#### `voltage_to_angle(voltage: float) -> float`
Mapea voltaje a ángulo de posición (0-300°).
- **Parámetros:** `voltage` (float) - Voltaje del sensor (0-3.3V)
- **Retorna:** `float` - Ángulo estimado en grados
- **Uso:** Conversión para sensores de posición tipo potenciómetro

#### `class MovingAverage`
Filtro de media móvil simple para reducir ruido ADC.

##### `__init__(self, size: int)`
Constructor del filtro.
- **Parámetros:** `size` (int) - Tamaño de ventana del filtro

##### `add(self, x: int) -> int`
Añade muestra y retorna promedio actualizado.
- **Parámetros:** `x` (int) - Nuevo valor ADC
- **Retorna:** `int` - Promedio actual
- **Uso:** Suavizado de lecturas ADC en tiempo real

#### `main()`
Loop principal que lee ADC, filtra, convierte y genera salida CSV.
- **Salida:** `t_ms,raw,avg,voltage_v,angle_deg`
- **Frecuencia:** Configurable mediante `FS_HZ` (100 Hz por defecto)
- **Uso:** Captura de datos para visualización y análisis

### Configuración de hardware
- **ADC_PIN:** GP26 (ADC0, pin físico 31 en Pico)
- **Rango ADC:** 0-65535 (16 bits con padding, 12 bits reales)
- **Voltaje:** 0-3.3V (sin atenuación configurable)

---

## Práctica 3: Medición de Temperatura con NTC

**Archivo:** `MicroPython/RP2040/P3/main.py`

### Funciones principales

#### `_init_adc(pin_no=ADC_PIN)`
Inicializa ADC en RP2040.
- **Parámetros:** `pin_no` (int) - Número de pin GPIO (26, 27 o 28)
- **Retorna:** Objeto `ADC`
- **Diferencia clave:** RP2040 usa `ADC(pin_number)` directamente, sin wrapper `Pin()`

#### `load_calibration()`
Carga archivo de calibración ADC desde JSON.
- **Archivo:** `calibration.json`
- **Uso:** Corrección de offset/ganancia del ADC (opcional)

#### `save_calibration()`
Guarda parámetros de calibración a archivo JSON.
- **Uso:** Persistencia de valores medidos en modo calibración

#### `adc_read_avg(adc_obj, nsamples=SAMPLES)`
Lee ADC múltiples veces y promedia.
- **Parámetros:** 
  - `adc_obj` (ADC) - Objeto ADC
  - `nsamples` (int) - Número de muestras (16 por defecto)
- **Retorna:** `int` - Promedio de lecturas
- **Uso:** Reducción de ruido mediante sobremuestreo

#### `adc_to_voltage(adc_val, adc_max=ADC_MAX, v_full=V_SUPPLY)`
Convierte valor ADC a voltaje con calibración opcional.
- **Parámetros:**
  - `adc_val` (int) - Valor ADC (0-65535)
  - `adc_max` (int) - Valor máximo del ADC
  - `v_full` (float) - Voltaje de referencia (3.3V)
- **Retorna:** `float` - Voltaje en V
- **Uso:** Conversión con corrección de offset/ganancia si calibración activa

#### `voltage_to_ntc_res(v_node, vcc=V_SUPPLY, r_series=R_SERIES)`
Calcula resistencia de NTC desde voltaje de nodo del divisor resistivo.
- **Parámetros:**
  - `v_node` (float) - Voltaje en nodo del divisor
  - `vcc` (float) - Voltaje de alimentación (3.3V)
  - `r_series` (float) - Resistencia en serie (10kΩ)
- **Retorna:** `float` - Resistencia NTC en Ω
- **Fórmula:** `Rntc = Rseries * Vnode / (Vcc - Vnode)`

#### `ntc_res_to_temp_c(r_ntc, r0=NTC_R0, beta=NTC_BETA, t0=T0_K)`
Convierte resistencia NTC a temperatura usando ecuación Beta.
- **Parámetros:**
  - `r_ntc` (float) - Resistencia medida (Ω)
  - `r0` (float) - Resistencia nominal a 25°C (10kΩ)
  - `beta` (float) - Coeficiente Beta (3950 típico)
  - `t0` (float) - Temperatura nominal en Kelvin (298.15K)
- **Retorna:** `float` - Temperatura en °C
- **Fórmula:** `1/T = 1/T0 + (1/Beta)*ln(R/R0)`

### Modos de operación

#### `mode_adc_raw(period_s=0.2)`
Modo 1: Muestra valor ADC crudo y voltaje de nodo.
- **Salida:** `adc=XXXXX, V=X.XXX`

#### `mode_resistance(period_s=0.2)`
Modo 2: Muestra resistencia estimada de la NTC.
- **Salida:** `adc=XXXXX, V=X.XXX, Rntc=XXXX.XΩ`

#### `mode_temperature(period_s=0.5)`
Modo 3: Muestra temperatura calculada en °C.
- **Salida:** `V=X.XXX V, Rntc=XXXXΩ, T=XX.XX°C`

#### `mode_monitor_csv(period_s=0.2)`
Modo 4: Monitor CSV para graficar datos.
- **Salida:** `t_ms,adc,v_node_v,r_ntc_ohm,t_c`

#### `mode_calibration_wizard()`
Modo 5: Guía interactiva para calibrar el ADC (offset/ganancia).
- **Procedimiento:**
  1. Conectar nodo (GP26) a GND → medir LOW
  2. Conectar nodo (GP26) a 3V3 → medir HIGH
  3. Guardar en `calibration.json`

### Configuración de hardware
- **Divisor resistivo:** 3V3 → R_SERIES (10kΩ) → nodo (GP26) → NTC (10kΩ@25°C) → GND
- **NTC Beta:** 3950 (típico)
- **Advertencia:** RP2040 ADC solo acepta 0-3.3V (sin protección de sobrevoltaje)

---

## Práctica 4: Medición de Presión con ADC (MPX5500DP)

**Archivo:** `MicroPython/RP2040/P4/main.py`

### Funciones principales

#### `load_calibration()`
Carga parámetros de calibración desde JSON.
- **Archivo:** `calibration.json`
- **Retorna:** `dict` o `None`

#### `save_calibration(data)`
Guarda parámetros de calibración a JSON.
- **Parámetros:** `data` (dict) - Datos de calibración

#### `adc_to_voltage(raw, calib=None)`
Convierte lectura ADC cruda a voltaje con calibración opcional.
- **Parámetros:**
  - `raw` (int) - Valor ADC (0-65535)
  - `calib` (dict, opcional) - Parámetros de calibración
- **Retorna:** `float` - Voltaje en V
- **Mapeo calibrado:** Si calib contiene `adc_low` y `adc_high`, mapea linealmente a 0-3.3V

#### `read_adc_avg(n=ADC_SAMPLES)`
Lee n muestras del ADC y devuelve el promedio.
- **Parámetros:** `n` (int) - Número de muestras (50 por defecto)
- **Retorna:** `int` - Promedio de lecturas
- **Uso:** Reducción de ruido mediante sobremuestreo (50 muestras → mejora ~7× en SNR)

#### `voltage_to_pressure_kpa(voltage)`
Convierte voltaje del sensor MPX5500DP a presión (kPa).
- **Parámetros:** `voltage` (float) - Voltaje del sensor (V)
- **Retorna:** `float` - Presión en kPa
- **Transfer function:** `P(kPa) = (Vout - Vmin) / sensitivity + Pmin`
- **Rango:** 20-520 kPa
- **Nota:** Para VS=3.3V, sensibilidad disminuye a ~66% del nominal (óptimo: VS=5V)

#### `menu_select(timeout_s=6)`
Muestra menú de modos y espera selección con timeout.
- **Parámetros:** `timeout_s` (int) - Timeout en segundos
- **Retorna:** `str` o `None`

#### `check_menu_break()`
Verifica si el usuario escribió 'm' para regresar al menú.
- **Retorna:** `bool`

### Modos de operación

#### `mode_raw_adc()`
Modo 1: Lectura ADC cruda continua.
- **Salida:** `ADC: XXXXX (0-65535)`

#### `mode_voltage()`
Modo 2: Voltaje del sensor (V).
- **Salida:** `Voltaje: X.XXX V  (ADC: XXXXX)`

#### `mode_pressure()`
Modo 3: Presión en kPa.
- **Salida:** `Presión: XXX.XX kPa  (V: X.XXX, ADC: XXXXX)`

#### `mode_csv_monitor()`
Modo 4: Monitor CSV continuo para visualización.
- **Salida:** `timestamp_ms,adc_raw,voltage_V,pressure_kPa`
- **Frecuencia:** 10 Hz (configurable)

#### `mode_calibration_wizard()`
Modo 5: Asistente de calibración ADC.
- **Procedimiento:**
  1. Conectar GP26 a GND → medir LOW
  2. Conectar GP26 a 3V3 → medir HIGH
  3. Guardar en `calibration.json`

### Configuración de hardware
- **Sensor:** MPX5500DP (piezoresistivo, 20-520 kPa)
- **Alimentación:** VS=3.3V (óptimo: 4.75-5.25V con divisor)
- **Conexión:** Vout (sensor) → GP26 (ADC0)
- **Transfer function:** `Vout = VS × (0.2 × P + 0.2)` donde P en kPa

---

## Práctica 5: Control PWM de Servomotores

**Archivo:** `MicroPython/RP2040/P5/main.py`

### Funciones principales

#### `menu_select(timeout_s=8)`
Muestra menú de modos y espera selección con timeout.
- **Parámetros:** `timeout_s` (int) - Timeout en segundos
- **Retorna:** `str` o `None`
- **Opciones:** 1) Barrido, 2) Ángulo manual, 3) Pulso directo, 4) Potenciómetro, q) Salir

#### `check_menu_break()`
Verifica si el usuario escribió 'm' para regresar al menú.
- **Retorna:** `bool`

#### `_clip(x, a, b)`
Limita valor x al rango [a, b].
- **Parámetros:** `x`, `a`, `b` (numéricos)
- **Retorna:** Valor limitado
- **Uso:** Validación de ángulos (0-180°)

### Modos de operación

#### `mode_sweep()`
Modo 1: Barrido 0–180–0 en bucle continuo.
- **Parámetros:** `SWEEP_STEP` (2° por defecto), `SWEEP_DELAY_MS` (20 ms)
- **Uso:** Demostración de rango completo del servo

#### `mode_angle_manual()`
Modo 2: Ángulo manual (0–180).
- **Entrada:** Usuario ingresa ángulo y ENTER
- **Salida:** `Ángulo→ XX°  (pulso ~XXXXus)`
- **Uso:** Posicionamiento preciso del servo

#### `mode_pulse_us()`
Modo 3: Pulso directo (us) para calibración.
- **Entrada:** Microsegundos (ej. 1500)
- **Rango típico:** 500-2400 us
- **Uso:** Calibración fina de límites físicos del servo

#### `mode_pot_control()`
Modo 4: Control por potenciómetro (ADC).
- **Pin ADC:** GP26 (ADC0)
- **Rango ADC:** 0-65535 (16 bits)
- **Resolución angular:** 0.0027°/bit (16× mejor que ESP32)
- **Salida:** `ADC=XXXXX → XXX°`
- **Uso:** Control analógico suave del servo

### Configuración de hardware
- **Servo PWM:** GP18 (PWM1 A), frecuencia 50 Hz (20 ms periodo)
- **Potenciómetro (opcional):** GP26 (ADC0)
- **Alimentación servo:** VSYS (5V USB) para servos pequeños (<500 mA); fuente externa para servos grandes
- **Ventajas RP2040:**
  - PWM jitter ~1 ns (10× mejor que ESP32)
  - ADC 16 bits (control 16× más suave que ESP32)
  - VSYS simplifica alimentación de servos pequeños

### Biblioteca de soporte
- **lib/servo.py:** Clase `Servo` con métodos:
  - `angle(deg)` - Posiciona servo en ángulo (0-180°)
  - `pulse_us(us)` - Control directo por ancho de pulso (us)

---

## Práctica 6: Conmutación de Potencia con PWM (transistor)

**Archivo:** `MicroPython/RP2040/P6/main.py`

### Funciones principales

#### `_stdin_key_available()`
Verifica si hay datos en stdin sin bloquear.
- **Retorna:** `bool`
- **Uso:** Detección de teclas para interrumpir modos

#### `_readline_nonblocking()`
Lee línea si hay datos disponibles, en caso contrario cadena vacía.
- **Retorna:** `str`

#### `_set_duty_percent(pwm: PWM, percent: float)`
Ajusta duty cycle (0–100%) usando `duty_u16` o `duty`.
- **Parámetros:**
  - `pwm` (PWM) - Objeto PWM
  - `percent` (float) - Duty cycle (0-100%)
- **Uso:** Configuración compatible con diferentes firmwares MicroPython

#### `_build_pwm()`
Construye objeto PWM en pin ACT_PIN con frecuencia PWM_FREQ.
- **Retorna:** Objeto `PWM` inicializado a 0% duty
- **Configuración:** GP18, 1000 Hz por defecto

#### `_build_adc()`
Construye objeto ADC para potenciómetro.
- **Retorna:** Objeto `ADC` en GP26
- **Uso:** Control analógico de duty cycle

### Modos de operación

#### `mode_on_off(pwm: PWM)`
Modo 1: Encendido/Apagado (alterna 100%/0% cada segundo).
- **Uso:** Verificación de conmutación básica

#### `mode_manual_pwm(pwm: PWM)`
Modo 2: PWM manual (0–100%).
- **Entrada:** Usuario ingresa duty % y ENTER
- **Salida:** `Aplicado duty = XX.X%`
- **Uso:** Control preciso de potencia media

#### `mode_sweep(pwm: PWM)`
Modo 3: Barrido 0→100→0.
- **Paso:** 1% cada 15 ms
- **Salida:** Imprime duty cada 10%
- **Uso:** Demostración de rampa de potencia

#### `mode_potentiometer(pwm: PWM, adc: ADC | None)`
Modo 4: Control por potenciómetro (ADC).
- **Pin ADC:** GP26 (ADC0)
- **Rango ADC:** 0-65535 (16 bits)
- **Resolución duty:** 0.0015%/bit (16× mejor que ESP32)
- **Salida:** `ADC=XXXXX → Duty=XX%`
- **Uso:** Control ultra-suave de potencia con potenciómetro

### Configuración de hardware
- **PWM:** GP18 (PWM1 A), 1000 Hz por defecto
- **Potenciómetro (opcional):** GP26 (ADC0)
- **Etapa de potencia:** MOSFET canal N (IRLZ44N, IRF540N, etc.)
  - GP18 → Resistencia 220Ω → Gate MOSFET
  - Source MOSFET → GND común (RP2040 + fuente)
  - Drain MOSFET → GND carga
  - +V fuente → +V carga
- **Diodo flyback:** Obligatorio para cargas inductivas (1N5819, 1N4007)
- **Ventajas RP2040:**
  - PWM jitter ~1 ns (10× mejor que ESP32)
  - ADC 16 bits (control subporcentual preciso)
  - VSYS disponible para cargas <500 mA

### Guía de frecuencias PWM por tipo de carga
- **LED/Lámpara:** 100-1000 Hz (evitar parpadeo visible)
- **Motor DC:** 500-2000 Hz (compromiso eficiencia/ruido)
- **Electroválvula:** 50-200 Hz (evitar sobrecalentamiento)
- **Resistencia calefactora:** 10-100 Hz (inercia térmica alta)

---

## Práctica 7: Control de Motores a Pasos

**Archivo:** `MicroPython/RP2040/P7/main.py`

### Funciones principales

#### `_stdin_key_available()`
Verifica si hay datos en stdin sin bloquear.
- **Retorna:** `bool`

#### `_readline_nonblocking()`
Lee línea si hay datos disponibles.
- **Retorna:** `str`

#### `rpm_to_interval_us(rpm: float, steps_per_rev: int) -> int`
Convierte RPM a intervalo entre pasos en microsegundos.
- **Parámetros:**
  - `rpm` (float) - Revoluciones por minuto
  - `steps_per_rev` (int) - Pasos por revolución (200 para NEMA 17 a 1/1)
- **Retorna:** `int` - Intervalo en microsegundos
- **Fórmula:** `1/(rpm * steps_per_rev / 60) * 1,000,000`

#### `_build_driver(driver_type: str)`
Construye el driver de motor a pasos según tipo seleccionado.
- **Parámetros:** `driver_type` (str) - "A4988" o "ULN2003"
- **Retorna:** Objeto driver o `None`
- **A4988:** Para motores bipolares (NEMA 17)
- **ULN2003:** Para motores unipolares (28BYJ-48)

#### `_setup_endstop()`
Configura el pin de fin de carrera con pull-up interno.
- **Pin:** GP4
- **Configuración:** INPUT + PULL_UP
- **Retorna:** Objeto `Pin`
- **Uso:** Detección de límites mecánicos (contacto a GND = activado)

### Modos de operación

#### `mode_jog(driver)`
Modo 1: Jog (avanza + o retrocede - paso a paso).
- **Entrada:** '+' avanza, '-' retrocede, 'm' menú
- **Uso:** Control manual fino de posición

#### `mode_move_n_steps(driver)`
Modo 2: Mover N pasos con velocidad y dirección configurables.
- **Entrada:** 
  - Número de pasos (positivo o negativo)
  - RPM (opcional, default 60)
- **Uso:** Movimiento programado preciso

#### `mode_sweep(driver, endstop=None)`
Modo 3: Barrido (avanza hasta límite, retrocede, repite).
- **Límite:** Fin de carrera (si conectado) o 400 pasos
- **Uso:** Demostración de ciclo automático con retorno

#### `mode_homing(driver, endstop)`
Modo 4: Homing (busca fin de carrera retrocediendo).
- **Velocidad:** Reducida automáticamente para precisión
- **Uso:** Calibración de posición inicial (punto cero)

#### `mode_info(driver)`
Modo 5: Información del driver (configuración actual).
- **Salida:** Tipo, pines, configuración de microstepping

### Configuración de hardware

#### Opción A: A4988 / DRV8825 (NEMA 17)
- **Pines:**
  - STEP: GP18
  - DIR: GP19
  - EN: GP5 (LOW activo)
- **Alimentación motor:** 12V típico, 1-2A
- **Fuente externa:** Obligatoria
- **GND común:** Crítico entre RP2040 y fuente
- **Microstepping:** Configurable (1/1, 1/2, 1/4, 1/8, 1/16)

#### Opción B: ULN2003 (28BYJ-48)
- **Pines:**
  - IN1: GP26
  - IN2: GP27
  - IN3: GP28
  - IN4: GP22
- **Alimentación motor:** 5V, ~200 mA (VSYS ok)
- **Resolución:** 2048 pasos/rev (full-step), 4096 (half-step)
- **⚠️ Conflicto:** Usa GP26-GP28 que son pines ADC; remapear sensores si se usa

#### Fin de carrera (opcional, ambos drivers)
- **Pin:** GP4 (INPUT + PULL_UP)
- **Conexión:** Microswitch NO (Normalmente Abierto) → GP4 a GND al activar

### Ventajas RP2040 para control de steppers
1. **PIO (Programmable I/O):** Pulsos STEP ultra-precisos independientes de CPU (jitter <10 ns)
2. **GPIO alta velocidad:** Conmutación 2-4 MHz (vs ~1 MHz ESP32)
3. **Bajo consumo idle:** Modo sleep profundo con PIO activo

---

## Práctica 8: Integración de Sistemas Sensor-Actuador

**Archivo:** `MicroPython/RP2040/P8/main.py`

### Módulos del sistema

#### `lib.sensors.FlightSensors`
Gestión de sensores ADC de vuelo.
- **Sensores:** Altitud (GP26), Velocidad (GP27), Actitud (GP28), Luminosidad (TEMP interno)
- **Métodos:**
  - `read_all()` - Lee todos los sensores
  - `get_percentage(name)` - Retorna valor normalizado 0-100%
  - `get_raw(name)` - Retorna valor ADC crudo

#### `lib.flight_controls.FlightControls`
Control de superficies de vuelo (servos).
- **Superficies:** Alerón (GP14), Elevador (GP15)
- **Métodos:**
  - `set_surface(name, angle)` - Posiciona superficie (0-180°)
  - `increment(name, delta)` - Incrementa/decrementa ángulo
  - `center_all()` - Centra todas las superficies (90°)
  - `get_angle(name)` - Retorna ángulo actual
  - `get_status()` - Retorna estado de todas las superficies

#### `lib.propulsion.PropulsionSystem`
Sistema de propulsión (motor PWM).
- **Pin:** GP13
- **Métodos:**
  - `set_throttle(percent)` - Ajusta throttle (0-100%)
  - `get_throttle()` - Retorna throttle actual
  - `emergency_stop()` - Detiene motor inmediatamente

#### `lib.landing_gear.LandingGear`
Control del tren de aterrizaje (motor a pasos).
- **Driver:** A4988 (GP18, GP19, GP5)
- **Endstop:** GP4
- **Métodos:**
  - `deploy()` - Despliega tren
  - `retract()` - Retrae tren
  - `home()` - Calibra posición inicial
  - `get_state()` - Retorna estado: "DEPLOYED", "RETRACTED", "MOVING", "UNKNOWN"

### Funciones de interfaz

#### `clear_screen()`
Limpia pantalla del terminal (código ANSI).

#### `print_banner()`
Muestra banner del sistema.

#### `print_menu()`
Muestra menú principal con opciones.

#### `wait_key(timeout_ms=0)`
Espera tecla con timeout.
- **Parámetros:** `timeout_ms` (int) - Timeout en ms (0 = sin timeout)
- **Retorna:** `str` o `None`

#### `check_menu_command()`
Verifica si se presionó 'm' para menú.
- **Retorna:** `bool`

### Modos de operación

#### `mode_instruments(sensors, controls, propulsion, landing_gear)`
Modo 1: Panel de instrumentos (monitoreo en tiempo real).
- **Actualización:** 5 Hz (200 ms)
- **Visualización:**
  - Sensores con barras de progreso
  - Ángulos de superficies de control
  - Throttle del motor
  - Estado del tren de aterrizaje

#### `mode_manual_surfaces(controls)`
Modo 2: Control manual de superficies.
- **Controles:**
  - [a/d] Alerón izquierda/derecha
  - [w/s] Elevador arriba/abajo
  - [0-9] Ángulo directo (×20, ej: 5 → 100°)
  - [c] Centrar todas (90°)
  - [m] Menú

#### `mode_power_control(propulsion)`
Modo 3: Control de potencia (motor/hélice).
- **Controles:**
  - [↑/↓] Incrementar/decrementar throttle
  - [0-9] Throttle directo (×10, ej: 5 → 50%)
  - [e] Emergency stop (0%)
  - [m] Menú

#### `mode_landing_gear(landing_gear)`
Modo 4: Control de tren de aterrizaje.
- **Controles:**
  - [d] Deploy (desplegar)
  - [r] Retract (retraer)
  - [h] Home (calibrar posición)
  - [s] Estado actual
  - [m] Menú

#### `mode_autopilot(sensors, controls, propulsion)`
Modo 5: Piloto automático simple.
- **Lógica:**
  - **Alerón:** Centrado (90°)
  - **Elevador:** Proporcional a altitud (bajo → sube, alto → baja)
  - **Throttle:** Proporcional a velocidad deseada
- **Parámetros:** `TARGET_ALTITUDE`, `TARGET_SPEED`
- **Uso:** Demostración de control automático básico

#### `mode_diagnostics(sensors, controls, propulsion, landing_gear)`
Modo 6: Diagnóstico del sistema.
- **Verificaciones:**
  - Rangos de sensores ADC
  - Ángulos de servos
  - Throttle del motor
  - Estado del tren
  - Pines configurados

#### `mode_configuration()`
Modo 7: Configuración del sistema.
- **Ajustes:**
  - Velocidad de actualización del panel
  - Límites de sensores
  - Ganancias del piloto automático
  - Driver de motor a pasos (A4988/ULN2003)

### Configuración de pines (RP2040)

#### Sensores ADC
- **Altitud:** GP26 (ADC0)
- **Velocidad:** GP27 (ADC1)
- **Actitud:** GP28 (ADC2)
- **Luminosidad:** TEMP (ADC4, interno)

#### Servos
- **Alerón:** GP14 (PWM)
- **Elevador:** GP15 (PWM)

#### Motor PWM
- **Control:** GP13 (PWM, 1 kHz)

#### Motor a pasos (tren de aterrizaje)
- **STEP:** GP18
- **DIR:** GP19
- **EN:** GP5
- **Endstop:** GP4 (INPUT + PULL_UP)

### Ventajas de la integración RP2040
1. **ADC 16 bits:** Lecturas suaves de sensores (16× mejor que ESP32)
2. **PWM estable:** Jitter ~1 ns para servos y motor (10× mejor que ESP32)
3. **PIO:** Pulsos STEP determinísticos para motor a pasos
4. **VSYS:** Alimentación simplificada para servos pequeños (<500 mA)
5. **30 GPIO:** Suficientes para múltiples sensores y actuadores sin multiplexado

---

## Diferencias clave RP2040 vs ESP32

### ADC (Analog-to-Digital Converter)
| Aspecto | ESP32 | RP2040 |
|---------|-------|--------|
| **Canales** | 18 canales (ADC1: GPIO32-39, ADC2: GPIO0-10) | 3 externos (GP26-GP28) + 1 interno (TEMP) |
| **Resolución** | 12 bits (0-4095) | 12 bits con padding a 16 bits (0-65535) |
| **Función lectura** | `adc.read()` → 0-4095 | `adc.read_u16()` → 0-65535 |
| **Configuración** | Requiere `atten()` (0dB-11dB) y `width()` | No requiere configuración (fijo 0-3.3V) |
| **Inicialización** | `ADC(Pin(34))` | `ADC(26)` (número directo) |
| **Rango voltaje** | 0-3.6V (con ATTN_11DB) | 0-3.3V estricto (sin protección) |

### PWM (Pulse Width Modulation)
| Aspecto | ESP32 | RP2040 |
|---------|-------|--------|
| **Canales** | 16 canales independientes | 8 slices × 2 canales = 16 total |
| **Jitter** | ~10 ns típico | ~1 ns típico ✅ (10× mejor) |
| **Frecuencia** | Configurable, hasta ~40 MHz | Configurable, hasta 62.5 MHz |
| **Resolución duty** | Configurable (hasta 16 bits) | Fijo 16 bits (0-65535) |

### GPIO (General Purpose Input/Output)
| Aspecto | ESP32 | RP2040 |
|---------|-------|--------|
| **Pines totales** | 34 (28-30 usables, algunos input-only) | 30 (26 usables, todos I/O) |
| **Velocidad conmutación** | ~1 MHz | 2-4 MHz ✅ |
| **Pull-up/down** | Interno configurable | Interno configurable |

### Memoria y procesamiento
| Aspecto | ESP32 | RP2040 |
|---------|-------|--------|
| **CPU** | Dual-core Xtensa LX6 @ 240 MHz | Dual-core ARM Cortex-M0+ @ 133 MHz |
| **RAM** | 520 KB | 264 KB |
| **Flash** | Externa (4 MB típico) | Externa (2 MB típico en Pico) |
| **PIO** | No | Sí (2 bloques, 4 state machines c/u) ✅ |

### Conectividad
| Aspecto | ESP32 | RP2040 |
|---------|-------|--------|
| **Wi-Fi** | Sí (802.11 b/g/n) ✅ | No |
| **Bluetooth** | Sí (BLE 4.2) ✅ | No |
| **USB** | No nativo | Sí (USB 1.1 device/host) ✅ |

### Alimentación
| Aspecto | ESP32 | RP2040 |
|---------|-------|--------|
| **Voltaje operación** | 3.0-3.6V | 1.8-5.5V (GPIO: 3.3V) |
| **Consumo típico** | ~80 mA activo, ~10 µA deep sleep | ~30 mA activo, ~180 µA sleep |
| **5V disponible** | No (requiere fuente externa) | Sí (VSYS desde USB) ✅ |

---

## Resumen de ventajas por práctica

### P1 (GPIO): RP2040 = ESP32
Ambos son equivalentes para GPIO básico.

### P2 (ADC): RP2040 ≈ ESP32
- **Ventaja RP2040:** Lectura 16 bits (más suave), configuración simple
- **Ventaja ESP32:** Más canales ADC (18 vs 3)

### P3 (NTC): RP2040 ≈ ESP32
Similar, ambos adecuados para termistores.

### P4 (Presión): RP2040 ≈ ESP32
Similar, aunque MPX5500DP funciona mejor con 5V (usar divisor).

### P5 (Servo): RP2040 > ESP32
- **PWM 10× más estable** (jitter ~1 ns vs ~10 ns)
- **ADC 16× más suave** para control por potenciómetro
- **VSYS simplifica alimentación** de servos pequeños

### P6 (Potencia PWM): RP2040 > ESP32
- **PWM ultra estable** (ideal para altas frecuencias sin distorsión)
- **Control subporcentual preciso** con ADC 16 bits
- **VSYS para cargas pequeñas** (<500 mA)

### P7 (Stepper): RP2040 > ESP32
- **PIO para pulsos determinísticos** (jitter <10 ns)
- **GPIO alta velocidad** (2-4 MHz)
- **Bajo consumo idle** con PIO activo

### P8 (Integración): RP2040 ≈ ESP32
- **Ventaja RP2040:** PWM/ADC superior, VSYS, PIO
- **Ventaja ESP32:** Wi-Fi/BLE, más ADC, dual-core más potente

---

## Conclusión

El RP2040 destaca en aplicaciones que requieren:
- **Control preciso de actuadores** (PWM estable, PIO)
- **Lectura suave de sensores analógicos** (ADC 16 bits)
- **Alimentación simplificada** (VSYS para periféricos 5V)
- **Bajo costo** y facilidad de uso educativo

El ESP32 es preferible cuando se necesita:
- **Conectividad inalámbrica** (Wi-Fi, Bluetooth)
- **Múltiples entradas analógicas** (>3 canales ADC)
- **Mayor potencia de procesamiento** (240 MHz dual-core)

Ambas plataformas son complementarias y el código MicroPython es **altamente portable** entre ellas con mínimas adaptaciones (principalmente en inicialización ADC y nombres de pines).

---

**Última actualización:** 2025-11-04  
**Repositorio:** SISELA-Init  
**Plataforma:** RP2040 (Raspberry Pi Pico) + MicroPython v1.24+
