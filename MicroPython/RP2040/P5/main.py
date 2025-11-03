"""
Práctica 5 — Control PWM para Servomotores (RP2040 + MicroPython)

Modos:
  1) Barrido 0–180–0 (sweep)
  2) Ángulo manual (ingresa valores 0–180)
  3) Pulso directo (us) para calibración
  4) Control por potenciómetro (ADC)
  q) Salir

Durante cualquier modo, escribe 'm' + ENTER para volver al menú.

🔄 ADAPTACIÓN RP2040:
- Pin PWM: GP18 (PWM channel 1A)
- Pin ADC: GP26 (ADC0) para potenciómetro
- ADC 16-bit: 0-65535 (mejor resolución que ESP32)
- Sin configuración atten() para ADC
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
        elif choice.lower() == 'q':
            print("\n[Salida] Programa terminado.")
            break
        else:
            print(f"[Inválida] '{choice}' no reconocida.")


if __name__ == "__main__":
    main()
