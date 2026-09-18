"""
Práctica 5 — Control PWM para Servomotores (RP2040 + MicroPython)

Modos:
  1) Barrido 0–180–0 (sweep)
  2) Ángulo manual (ingresa valores 0–180)
  3) Pulso directo (us) para calibración
  4) Control por potenciómetro (ADC)
  5) Jitter de PWM (medición con osciloscopio)
  6) Muestreo y aliasing (ADC + generador de funciones)
  7) Respuesta al escalón del servo-lazo (requiere realimentación en ADC)
  8) Vista en vivo (ángulo + ADC), streaming continuo para tools/sisela_signal live
  q) Salir

Durante cualquier modo, escribe 'm' + ENTER para volver al menú.

🔄 ADAPTACIÓN RP2040:
- Pin PWM: GP18 (PWM channel 1A)
- Pin ADC: GP26 (ADC0) para potenciómetro
- ADC 16-bit: 0-65535 (mejor resolución que ESP32)
- Sin configuración atten() para ADC

Los modos 5–7 se apoyan en el banco (generador + osciloscopio) y en la toolkit PC
`tools/sisela_signal/`. El modo 8 transmite en continuo (no en bloque):
  python -m sisela_signal live --port COM5 --menu 8 --cols angle_deg,adc_raw
"""

# =============================================================================
# Imports & configuración
# =============================================================================
try:
    from machine import Pin, ADC
    import utime as time
    import uselect
    import sys
    MICROPYTHON = True
except ImportError:
    MICROPYTHON = False

from lib.servo import Servo

try:
    from siglab import BlockSampler, Stats, stream_csv
    HAVE_SIGLAB = True
except ImportError:
    HAVE_SIGLAB = False

# Parámetros de hardware (RP2040)
SERVO_PIN = 18            # GP18 (PWM1 A)
SERVO_FREQ = 50           # Hz (periodo 20 ms)
SERVO_MIN_US = 500        # pulso mínimo (us)
SERVO_MAX_US = 2400       # pulso máximo (us)
ANGLE_MIN = 0
ANGLE_MAX = 180

# Potenciómetro opcional (para modo 4)
ADC_PIN = 26              # GP26 (ADC0)
# RP2040: ADC siempre 0-3.3V, no requiere atten()

SWEEP_STEP = 2            # grados por paso en sweep
SWEEP_DELAY_MS = 20       # retardo entre pasos

# =============================================================================
# Inicialización hardware
# =============================================================================
if MICROPYTHON:
    try:
        servo = Servo(SERVO_PIN, freq=SERVO_FREQ, min_us=SERVO_MIN_US, max_us=SERVO_MAX_US,
                      angle_min=ANGLE_MIN, angle_max=ANGLE_MAX)
        print(f"[Servo] GP{SERVO_PIN} @ {SERVO_FREQ}Hz, {SERVO_MIN_US}-{SERVO_MAX_US}us")
    except (RuntimeError, ValueError, OSError) as e:
        print(f"[Error] No se pudo inicializar el servo: {e}")
        servo = None
else:
    servo = None

# =============================================================================
# Utilidades de menú
# =============================================================================
def menu_select(timeout_s=8):
    print("\n" + "="*48)
    print("MENÚ — Práctica 5: PWM Servos (RP2040)")
    print("="*48)
    print("1) Barrido 0–180–0")
    print("2) Ángulo manual (0–180)")
    print("3) Pulso directo (us)")
    print("4) Control por potenciómetro")
    print("5) Jitter de PWM (osciloscopio)")
    print("6) Muestreo y aliasing (ADC + generador)")
    print("7) Respuesta al escalón del servo-lazo")
    print("8) Vista en vivo (ángulo + ADC) — tools/sisela_signal live")
    print("q) Salir")
    print("="*48)
    print(f"Selecciona opción (timeout {timeout_s}s): ", end="")

    if not MICROPYTHON:
        return "1"

    poll = uselect.poll()
    poll.register(sys.stdin, uselect.POLLIN)
    start = time.ticks_ms()
    while True:
        if time.ticks_diff(time.ticks_ms(), start) / 1000.0 >= timeout_s:
            print("\n[Timeout] Reintentando menú…")
            return None
        events = poll.poll(100)
        if events:
            line = sys.stdin.readline().strip()
            if line:
                return line
        time.sleep_ms(50)


def check_menu_break():
    if not MICROPYTHON:
        return False
    poll = uselect.poll()
    poll.register(sys.stdin, uselect.POLLIN)
    events = poll.poll(0)
    if events:
        line = sys.stdin.readline().strip().lower()
        if line == 'm':
            print("\n[Menú] Regresando al menú…")
            return True
    return False


def _clip(x, a, b):
    return a if x < a else (b if x > b else x)


def _make_adc():
    """
    Devuelve (read_fn, full_scale_counts, vref). RP2040: ADC de 16 bits
    (0–65535), rango fijo 0–3.3 V, sin atten().
    """
    adc = ADC(ADC_PIN)
    return (adc.read_u16, 65535, 3.3)


def _ask(prompt, default):
    print("{} [{}]: ".format(prompt, default), end="")
    if not MICROPYTHON:
        return default
    poll = uselect.poll()
    poll.register(sys.stdin, uselect.POLLIN)
    while True:
        if poll.poll(500):
            s = sys.stdin.readline().strip()
            if not s:
                return default
            try:
                return type(default)(s)
            except ValueError:
                return default
        time.sleep_ms(100)


def wait_enter_p5(msg="ENTER para continuar..."):
    print(msg, end="")
    if not MICROPYTHON:
        return
    poll = uselect.poll()
    poll.register(sys.stdin, uselect.POLLIN)
    while not poll.poll(300):
        time.sleep_ms(100)
    try:
        sys.stdin.readline()
    except Exception:
        pass


# =============================================================================
# Modos
# =============================================================================
def mode_sweep():
    print("\n--- MODO 1: Barrido 0–180–0 ---\nEscribe 'm'+ENTER para regresar…\n")
    if not servo:
        print("[Error] Servo no inicializado.")
        return
    # Barrer ida y vuelta
    while True:
        for a in range(ANGLE_MIN, ANGLE_MAX + 1, SWEEP_STEP):
            servo.angle(a)
            if check_menu_break():
                return
            time.sleep_ms(SWEEP_DELAY_MS)
        for a in range(ANGLE_MAX, ANGLE_MIN - 1, -SWEEP_STEP):
            servo.angle(a)
            if check_menu_break():
                return
            time.sleep_ms(SWEEP_DELAY_MS)


def mode_angle_manual():
    print("\n--- MODO 2: Ángulo manual (0–180) ---")
    print("Introduce un ángulo y ENTER. 'm'+ENTER para volver.\n")
    if not servo:
        print("[Error] Servo no inicializado.")
        return
    if not MICROPYTHON:
        print("[PC] Modo interactivo no disponible fuera de la placa.")
        return
    while True:
        try:
            line = sys.stdin.readline().strip().lower()
            if line == 'm':
                return
            if not line:
                continue
            angle = int(line)
            angle = _clip(angle, ANGLE_MIN, ANGLE_MAX)
            us = servo.angle(angle)
            print(f"Ángulo→ {angle}°  (pulso ~{us}us)")
        except ValueError:
            print("Ingresa un número entero (0–180) o 'm' para salir.")


def mode_pulse_us():
    print("\n--- MODO 3: Pulso directo (us) ---")
    print("Introduce microsegundos (p.ej. 1500). 'm' para volver.\n")
    if not servo:
        print("[Error] Servo no inicializado.")
        return
    if not MICROPYTHON:
        print("[PC] Modo interactivo no disponible fuera de la placa.")
        return
    while True:
        try:
            line = sys.stdin.readline().strip().lower()
            if line == 'm':
                return
            if not line:
                continue
            micros = int(line)
            micros = servo.pulse_us(micros)
            print(f"Pulso→ {micros}us")
        except ValueError:
            print("Ingresa microsegundos (ej. 500–2400) o 'm' para salir.")


def mode_pot_control():
    print("\n--- MODO 4: Control por potenciómetro ---\nEscribe 'm'+ENTER para regresar…\n")
    if not servo:
        print("[Error] Servo no inicializado.")
        return
    if not MICROPYTHON:
        print("[PC] No disponible.")
        return
    try:
        # RP2040: ADC usa pin número directamente, sin Pin()
        adc = ADC(ADC_PIN)
        # RP2040: No requiere atten(), siempre 0-3.3V
        print(f"[ADC] GP{ADC_PIN} configurado (16-bit, 0-3.3V)")
    except (ValueError, OSError) as e:
        print(f"[Error] No se pudo inicializar ADC en GP{ADC_PIN}: {e}")
        return

    last_angle = -999
    while True:
        # RP2040: read_u16() devuelve 0-65535 (16 bits)
        raw = adc.read_u16()
        angle = int(ANGLE_MIN + (raw / 65535.0) * (ANGLE_MAX - ANGLE_MIN))
        if angle != last_angle:
            servo.angle(angle)
            print(f"ADC={raw:5d} → {angle:3d}°")
            last_angle = angle
        if check_menu_break():
            break
        time.sleep_ms(20)


# =============================================================================
# Modo 5: Jitter de PWM (medición con osciloscopio)
# =============================================================================
def mode_pwm_jitter():
    """Fija un ancho de pulso constante para que el osciloscopio mida su estabilidad."""
    print("\n--- MODO 5: Jitter de PWM (osciloscopio) ---")
    if not servo:
        print("[Error] Servo no inicializado."); return
    print("Sonda CH1 en la señal del servo (GP{}), pinza a GND.".format(SERVO_PIN))
    print("Osciloscopio: 1 ms/div, trigger flanco de subida ~1.5 V,")
    print("Measure -> Pulse Width -> estadística Min/Max/Mean/StdDev.\n")
    us = _ask("Ancho de pulso a mantener (us)", 1500)
    hold_s = _ask("Segundos por punto", 30)
    servo.pulse_us(int(us))
    duty = None
    if hasattr(servo, "_pwm") and hasattr(servo._pwm, "duty_u16"):
        try:
            duty = servo._pwm.duty_u16()
        except Exception:
            duty = None
    print("Pulso nominal: {} us   periodo: {:.0f} us (50 Hz)".format(int(us), 1_000_000 / SERVO_FREQ))
    if duty is not None:
        print("Registro duty_u16 leído: {}  (esperado ~{:.0f})".format(
            duty, int(us) * 65535 / (1_000_000 / SERVO_FREQ)))
    print("\nManteniendo {} us durante {} s...  ('m' + ENTER aborta)".format(int(us), int(hold_s)))
    t0 = time.ticks_ms() if MICROPYTHON else 0
    while MICROPYTHON:
        if time.ticks_diff(time.ticks_ms(), t0) / 1000.0 >= hold_s:
            break
        if check_menu_break():
            return
        time.sleep_ms(200)
    print("\nExporta la traza del osciloscopio y en la PC:")
    print("  python -m sisela_signal characterize --scope --file scopeCH1.csv --col CH1 --mode adc")
    print("\nEsperado: ESP32 σ ~ 100 ns (LEDC), RP2040 σ ~ 10 ns (PWM slice).")
    wait_enter_p5("\nENTER para volver al menú...")


# =============================================================================
# Modo 6: Muestreo y aliasing (ADC + generador de funciones)
# =============================================================================
def mode_sampling_alias():
    """Muestrea la señal del generador en el ADC a una Fs elegida y emite el bloque en CSV."""
    print("\n--- MODO 6: Muestreo y Aliasing (ADC + generador) ---")
    if not HAVE_SIGLAB:
        print("[ERROR] Falta lib/siglab.py en la placa."); return
    if not MICROPYTHON:
        print("[PC] No disponible."); return
    print("Generador -> GP{}: seno, amplitud <= 2 Vpp, OFFSET +1.65 V (0–3.3 V).".format(ADC_PIN))
    print("⚠️ Verifica con el osciloscopio que la señal está dentro de 0–3.3 V ANTES de conectar.\n")
    fs = _ask("Fs de muestreo (Hz)", 2000)
    n = _ask("Número de muestras", 2048)
    read_fn, full, vref = _make_adc()

    print("\nCapturando {} muestras a {} Hz...".format(n, fs))
    res = BlockSampler(read_fn, fs, n).run()
    print(res.report())
    print("Nyquist: Fs/2 = {:.1f} Hz. Frecuencias del generador > {:.1f} Hz se pliegan (alias).".format(
        fs / 2.0, fs / 2.0))

    print("\nt_us,counts,v")
    for i in range(len(res.samples)):
        c = res.samples[i]
        print("{},{},{:.4f}".format(res.t_us[i], c, c / full * vref))
    print("# fin fs_real={:.2f} jitter_us={:.2f} full_scale={}".format(
        res.fs_actual, res.jitter_us, full))
    print("\nEn la PC (repite variando la frecuencia del generador):")
    print("  python -m sisela_signal spectrum --file cap.csv --col v --metrics --full-scale 3.3")
    print("  python -m sisela_signal alias    --file cap.csv --true-f <f_generador>")
    wait_enter_p5("\nENTER para volver al menú...")


# =============================================================================
# Modo 7: Respuesta al escalón del servo-lazo
# =============================================================================
def mode_step_response():
    """Comanda un escalón de ángulo y muestrea la realimentación de posición (ADC)."""
    print("\n--- MODO 7: Respuesta al Escalón del Servo-lazo ---")
    if not servo:
        print("[Error] Servo no inicializado."); return
    if not HAVE_SIGLAB or not MICROPYTHON:
        print("[ERROR] Requiere lib/siglab.py y ejecución en placa."); return
    print("Conecta un potenciómetro de realimentación al eje del servo -> GP{}.".format(ADC_PIN))
    a0 = _ask("Ángulo inicial", 60)
    a1 = _ask("Ángulo final", 120)
    fs = _ask("Fs de muestreo (Hz)", 500)
    n = _ask("Muestras (cubre el transitorio)", 500)
    read_fn, full, vref = _make_adc()

    servo.angle(int(a0))
    time.sleep_ms(600)
    print("\nEscalón {}° -> {}°  (el escalón ocurre tras ~10 % del bloque)".format(int(a0), int(a1)))
    print("t_us,counts,v")
    pre = max(1, n // 10)
    res_pre = BlockSampler(read_fn, fs, pre).run()
    servo.angle(int(a1))
    res_post = BlockSampler(read_fn, fs, n - pre).run()
    off = res_pre.t_us[-1] if pre else 0
    for i in range(pre):
        c = res_pre.samples[i]
        print("{},{},{:.4f}".format(res_pre.t_us[i], c, c / full * vref))
    for i in range(n - pre):
        c = res_post.samples[i]
        print("{},{},{:.4f}".format(off + res_post.t_us[i], c, c / full * vref))
    print("# fin escalon={}->{} fs~{}".format(int(a0), int(a1), fs))
    print("\nEn la PC:")
    print("  python -m sisela_signal characterize --file step.csv --col v --mode step")
    wait_enter_p5("\nENTER para volver al menú...")


# =============================================================================
# Modo 8: Vista en vivo (ángulo + ADC), streaming continuo
# =============================================================================
def mode_live_view():
    """Modo 8: transmite continuamente ángulo comandado + lectura ADC como CSV
    `t_us,angle_deg,adc_raw`, para `tools/sisela_signal live` (vista en tiempo
    real, sin necesidad de capturar primero). A diferencia de los Modos 5-7
    (BlockSampler, precisión de muestreo crítica), este modo no mide jitter ni
    tiempos críticos, así que puede imprimir en vivo sin afectar la medición."""
    print("\n--- MODO 8: Vista en vivo (ángulo + ADC) ---")
    if not servo:
        print("[Error] Servo no inicializado."); return
    if not HAVE_SIGLAB or not MICROPYTHON:
        print("[ERROR] Requiere lib/siglab.py y ejecución en placa."); return
    read_fn, full, vref = _make_adc()
    print("Barrido lento 0-{}-0 mientras transmite. 'm'+ENTER aborta.".format(ANGLE_MAX))
    print("En la PC: python -m sisela_signal live --port COMx --menu 8 --cols angle_deg,adc_raw")
    state = {"angle": ANGLE_MIN, "dir": 1}

    def _read():
        a = state["angle"]
        servo.angle(a)
        raw = read_fn()
        state["angle"] += state["dir"] * 2
        if state["angle"] >= ANGLE_MAX:
            state["angle"], state["dir"] = ANGLE_MAX, -1
        elif state["angle"] <= ANGLE_MIN:
            state["angle"], state["dir"] = ANGLE_MIN, 1
        return (a, raw)

    stream_csv(_read, 20.0, cols=("angle_deg", "adc_raw"), max_samples=0)
    servo.angle((ANGLE_MIN + ANGLE_MAX) // 2)


# =============================================================================
# Main
# =============================================================================
def main():
    print("\n" + "="*60)
    print("Práctica 5 — Control PWM para Servomotores (RP2040)")
    print("Raspberry Pi Pico + MicroPython")
    print("="*60)
    if not MICROPYTHON:
        print("[PC] Simulación limitada.")
        return
    if not servo:
        print("[Error crítico] Servo no disponible. Verifica conexión del pin y reinicia.")
        return
    while True:
        choice = menu_select(timeout_s=8)
        if choice is None:
            continue
        if choice == '1':
            mode_sweep()
        elif choice == '2':
            mode_angle_manual()
        elif choice == '3':
            mode_pulse_us()
        elif choice == '4':
            mode_pot_control()
        elif choice == '5':
            mode_pwm_jitter()
        elif choice == '6':
            mode_sampling_alias()
        elif choice == '7':
            mode_step_response()
        elif choice == '8':
            mode_live_view()
        elif choice.lower() == 'q':
            print("\n[Salida] Programa terminado.")
            break
        else:
            print(f"[Inválida] '{choice}' no reconocida.")


if __name__ == "__main__":
    main()
