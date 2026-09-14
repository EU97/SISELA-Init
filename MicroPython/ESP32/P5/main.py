"""
Práctica 5 — Control PWM para Servomotores (ESP32 + MicroPython)

Modos:
  1) Barrido 0–180–0 (sweep)
  2) Ángulo manual (ingresa valores 0–180)
  3) Pulso directo (us) para calibración
  4) Control por potenciómetro (ADC)
  5) Jitter de PWM (medición con osciloscopio)
  6) Muestreo y aliasing (ADC + generador de funciones)
  7) Respuesta al escalón del servo-lazo (requiere realimentación en ADC)
  q) Salir

Durante cualquier modo, escribe 'm' + ENTER para volver al menú.

Los modos 5–7 se apoyan en el banco (generador + osciloscopio) y en la toolkit PC
`tools/sisela_signal/`:
  python -m sisela_signal spectrum      --file cap.csv --col v --metrics --full-scale 3.3
  python -m sisela_signal alias         --file cap.csv --true-f 3000
  python -m sisela_signal characterize  --file step.csv --col v --mode step
  python -m sisela_signal scope --scope --file RigolCH1.csv   # jitter de PWM del modo 5
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
    from siglab import BlockSampler, Stats
    HAVE_SIGLAB = True
except ImportError:
    HAVE_SIGLAB = False

# Parámetros de hardware
SERVO_PIN = 18            # Señal PWM al servo
SERVO_FREQ = 50           # Hz (periodo 20 ms)
SERVO_MIN_US = 500        # pulso mínimo (us)
SERVO_MAX_US = 2400       # pulso máximo (us)
ANGLE_MIN = 0
ANGLE_MAX = 180

# Potenciómetro opcional (para modo 4)
ADC_PIN = 34              # GPIO34 (entrada ADC)
ADC_ATTEN = 3             # 11dB → 0..3.3V (ADC.ATTN_11DB)

SWEEP_STEP = 2            # grados por paso en sweep
SWEEP_DELAY_MS = 20       # retardo entre pasos

# =============================================================================
# Inicialización hardware
# =============================================================================
if MICROPYTHON:
    try:
        servo = Servo(SERVO_PIN, freq=SERVO_FREQ, min_us=SERVO_MIN_US, max_us=SERVO_MAX_US,
                      angle_min=ANGLE_MIN, angle_max=ANGLE_MAX)
        print(f"[Servo] GPIO{SERVO_PIN} @ {SERVO_FREQ}Hz, {SERVO_MIN_US}-{SERVO_MAX_US}us")
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
    print("MENÚ — Práctica 5: PWM Servos")
    print("="*48)
    print("1) Barrido 0–180–0")
    print("2) Ángulo manual (0–180)")
    print("3) Pulso directo (us)")
    print("4) Control por potenciómetro")
    print("5) Jitter de PWM (osciloscopio)")
    print("6) Muestreo y aliasing (ADC + generador)")
    print("7) Respuesta al escalón del servo-lazo")
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
    Devuelve (read_fn, full_scale_counts, vref) para el pin ADC del potenciómetro
    o de la señal del generador. ESP32: 12 bit (0–4095) con atenuación 11 dB.
    """
    adc = ADC(Pin(ADC_PIN))
    try:
        adc.atten(ADC.ATTN_11DB)      # 0..~3.3 V
    except AttributeError:
        pass
    return (adc.read, 4095, 3.3)


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
        adc = ADC(Pin(ADC_PIN))
        # Constantes de ADC en ESP32
        try:
            adc.atten(ADC.ATTN_11DB)  # 0..3.3V
        except AttributeError:
            pass
    except (ValueError, OSError) as e:
        print(f"[Error] No se pudo inicializar ADC en GPIO{ADC_PIN}: {e}")
        return

    last_angle = -999
    while True:
        raw = adc.read()  # 0..4095
        angle = int(ANGLE_MIN + (raw / 4095.0) * (ANGLE_MAX - ANGLE_MIN))
        if angle != last_angle:
            servo.angle(angle)
            print(f"ADC={raw:4d} → {angle:3d}°")
            last_angle = angle
        if check_menu_break():
            break
        time.sleep_ms(20)


# =============================================================================
# Modo 5: Jitter de PWM (medición con osciloscopio)
# =============================================================================
def mode_pwm_jitter():
    """
    Fija un ancho de pulso constante y lo mantiene para que el osciloscopio
    mida la estabilidad (Measure -> Pulse Width -> Std Dev). La PC procesa el
    CSV exportado del osciloscopio con `sisela_signal scope`/`characterize`.
    """
    print("\n--- MODO 5: Jitter de PWM (osciloscopio) ---")
    if not servo:
        print("[Error] Servo no inicializado."); return
    print("Sonda CH1 en la señal del servo (GPIO{}), pinza a GND.".format(SERVO_PIN))
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
    while True:
        if MICROPYTHON and time.ticks_diff(time.ticks_ms(), t0) / 1000.0 >= hold_s:
            break
        if not MICROPYTHON:
            break
        if check_menu_break():
            return
        time.sleep_ms(200)
    print("\nExporta la traza del osciloscopio y en la PC:")
    print("  python -m sisela_signal characterize --scope --file scopeCH1.csv --col CH1 --mode adc")
    print("  (o abre el histograma de ancho de pulso del propio osciloscopio)")
    print("\nEsperado: ESP32 σ ~ 100 ns (LEDC), RP2040 σ ~ 10 ns (PWM slice).")
    wait_enter_p5("\nENTER para volver al menú...")


# =============================================================================
# Modo 6: Muestreo y aliasing (ADC + generador de funciones)
# =============================================================================
def mode_sampling_alias():
    """
    Muestrea la señal del generador (seno 0–3.3 V, offset 1.65 V) en el pin ADC
    a una Fs elegida y emite el bloque en CSV. Barriendo la frecuencia del
    generador por encima de Fs/2 se observa el aliasing en la PC.
    """
    print("\n--- MODO 6: Muestreo y Aliasing (ADC + generador) ---")
    if not HAVE_SIGLAB:
        print("[ERROR] Falta lib/siglab.py en la placa."); return
    if not MICROPYTHON:
        print("[PC] No disponible."); return
    print("Generador -> GPIO{}: seno, amplitud <= 2 Vpp, OFFSET +1.65 V (0–3.3 V).".format(ADC_PIN))
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
    """
    Comanda un escalón de ángulo y muestrea la realimentación de posición
    (potenciómetro acoplado al eje de salida -> ADC) durante el transitorio.
    La PC calcula rise time, sobreimpulso y tiempo de estabilización.
    """
    print("\n--- MODO 7: Respuesta al Escalón del Servo-lazo ---")
    if not servo:
        print("[Error] Servo no inicializado."); return
    if not HAVE_SIGLAB or not MICROPYTHON:
        print("[ERROR] Requiere lib/siglab.py y ejecución en placa."); return
    print("Conecta un potenciómetro de realimentación al eje del servo -> GPIO{}.".format(ADC_PIN))
    a0 = _ask("Ángulo inicial", 60)
    a1 = _ask("Ángulo final", 120)
    fs = _ask("Fs de muestreo (Hz)", 500)
    n = _ask("Muestras (cubre el transitorio)", 500)
    read_fn, full, vref = _make_adc()

    servo.angle(int(a0))
    time.sleep_ms(600)
    print("\nEscalón {}° -> {}°  (el escalón ocurre tras ~10 % del bloque)".format(int(a0), int(a1)))
    print("t_us,counts,v")
    # planificación simple: pre-muestras, escalón, resto del bloque
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
# Main
# =============================================================================
def main():
    print("\n" + "="*60)
    print("Práctica 5 — Control PWM para Servomotores")
    print("ESP32 + MicroPython")
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
        elif choice.lower() == 'q':
            print("\n[Salida] Programa terminado.")
            break
        else:
            print(f"[Inválida] '{choice}' no reconocida.")


if __name__ == "__main__":
    main()
