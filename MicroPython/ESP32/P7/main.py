"""
Práctica 7 — Motores a pasos (ESP32 + MicroPython)

Soporte:
- A4988/DRV8825 (STEP/DIR/EN)
- ULN2003 + 28BYJ-48 (secuencia IN1..IN4)
- Fin de carrera opcional en GPIO4 (pull-up, contacto a GND)

Modos:
  0) Configurar driver (A4988/ULN2003)
  1) Jog continuo (CW/CCW, RPM)
  2) Mover N pasos (con rampa opcional)
  3) Barrido de velocidad
  4) Homing con fin de carrera
  5) Información / ayuda

Salir/menú: escribir 'm' + ENTER en el terminal para abortar un modo.
"""

# =============================================================================
# Imports y configuración
# =============================================================================
try:
    from machine import Pin
    import utime as time
    import uselect
    import sys
    MICROPYTHON = True
except ImportError:
    MICROPYTHON = False

from lib.stepper_a4988 import StepperA4988
from lib.stepper_uln2003 import StepperULN2003

# Pines por defecto (ver PINES.md)
# A4988/DRV8825
PIN_STEP = 18
PIN_DIR = 19
PIN_EN = 5  # activo en LOW (opcional)

# ULN2003 + 28BYJ-48
PIN_IN1 = 26
PIN_IN2 = 25
PIN_IN3 = 33
PIN_IN4 = 32

# Fin de carrera
PIN_ENDSTOP = 4

# Estado de configuración
DRIVER = 'A4988'  # 'A4988' o 'ULN2003'
STEPS_PER_REV_DEFAULT = {
    'A4988': 200,    # NEMA17 típicamente 200 pasos/rev (full-step sin microstepping)
    'ULN2003': 2048, # 28BYJ-48 (half-step) ≈ 2048 pasos por vuelta de salida
}


# =============================================================================
# Utilidades de IO y menú
# =============================================================================

def menu_select(timeout_s=8):
    print("\n" + "="*56)
    print("MENÚ — Práctica 7: Motores a pasos")
    print("="*56)
    print("0) Configurar driver (A4988/ULN2003)")
    print("1) Jog continuo (CW/CCW, RPM)")
    print("2) Mover N pasos (con rampa opcional)")
    print("3) Barrido de velocidad")
    print("4) Homing con fin de carrera")
    print("5) Info / ayuda")
    print("q) Salir")
    print("="*56)
    print(f"[Driver:{DRIVER}] Selecciona opción (timeout {timeout_s}s): ", end="")

    if not MICROPYTHON:
        return "5"  # en PC: mostrar info por defecto

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


def rpm_to_interval_us(rpm, steps_per_rev):
    # tiempo por paso [us] = (60 s / (rpm * pasos/rev)) * 1e6
    if rpm <= 0 or steps_per_rev <= 0:
        return 0
    return int(60_000_000 / (rpm * steps_per_rev))


def build_driver(base_interval_us=None, halfstep=True):
    """Crea instancia de driver según DRIVER global.
    base_interval_us se usa para A4988 como min_step_interval_us.
    Para ULN2003, ajustaremos 'delay' en ms si se requiere.
    """
    if DRIVER == 'A4988':
        iv = base_interval_us or 800
        drv = StepperA4988(PIN_STEP, PIN_DIR, PIN_EN, step_pulse_us=5, min_step_interval_us=iv)
        return drv
    else:
        # ULN2003: delay en ms predeterminado 3 ms
        drv = StepperULN2003(PIN_IN1, PIN_IN2, PIN_IN3, PIN_IN4, halfstep=halfstep, step_delay_ms=3)
        return drv


def endstop_pin():
    try:
        p = Pin(PIN_ENDSTOP, Pin.IN, Pin.PULL_UP)
        return p
    except Exception:
        return None


# =============================================================================
# Modos
# =============================================================================

def mode_config_driver():
    global DRIVER
    print("\n--- MODO 0: Configurar driver ---")
    print("Elige controlador:\n  1) A4988/DRV8825\n  2) ULN2003 + 28BYJ-48")
    sel = input("> ") if MICROPYTHON else "1"
    DRIVER = 'ULN2003' if sel.strip() == '2' else 'A4988'
    print(f"Driver activo: {DRIVER}")


def mode_jog():
    print("\n--- MODO 1: Jog continuo ---")
    spr_default = STEPS_PER_REV_DEFAULT.get(DRIVER, 200)
    try:
        val = input(f"Pasos/rev [{spr_default}]: ") if MICROPYTHON else "200"
        steps_per_rev = int(val) if val.strip() else spr_default
    except Exception:
        steps_per_rev = spr_default
    try:
        val = input("RPM [10]: ") if MICROPYTHON else "10"
        rpm = max(1, int(val) if val.strip() else 10)
    except Exception:
        rpm = 10
    cw = True if (input("Sentido 1=CW, 2=CCW [1]: ") if MICROPYTHON else "1").strip() != '2' else False

    if DRIVER == 'A4988':
        iv_us = rpm_to_interval_us(rpm, steps_per_rev)
        drv = build_driver(base_interval_us=iv_us)
        print("Presiona 'm'+ENTER para regresar…")
        while True:
            drv.move_steps(200, cw=cw, interval_us=iv_us)
            if check_menu_break():
                break
    else:
        # ULN2003: convertir a delay ms por paso
        step_ms = max(1, int(rpm_to_interval_us(rpm, steps_per_rev) / 1000))
        drv = build_driver()
        drv.delay = step_ms
        print("Presiona 'm'+ENTER para regresar…")
        while True:
            drv.step(64, cw=cw)
            if check_menu_break():
                break


def mode_move_n_steps():
    print("\n--- MODO 2: Mover N pasos ---")
    spr_default = STEPS_PER_REV_DEFAULT.get(DRIVER, 200)
    try:
        val = input("N pasos (ej. 800): ") if MICROPYTHON else "800"
        nsteps = max(1, int(val))
    except Exception:
        nsteps = 800
    cw = True if (input("Sentido 1=CW, 2=CCW [1]: ") if MICROPYTHON else "1").strip() != '2' else False
    use_ramp = (input("Usar rampa lineal? 1=Sí, 2=No [1]: ") if MICROPYTHON else "1").strip() != '2'
    try:
        val = input(f"Pasos/rev [{spr_default}]: ") if MICROPYTHON else "200"
        steps_per_rev = int(val) if val.strip() else spr_default
    except Exception:
        steps_per_rev = spr_default
    try:
        rpm = int(input("RPM objetivo [20]: ") if MICROPYTHON else "20")
    except Exception:
        rpm = 20

    if DRIVER == 'A4988':
        iv_us = rpm_to_interval_us(max(1, rpm), steps_per_rev)
        drv = build_driver(base_interval_us=iv_us)
        if use_ramp:
            drv.move_ramped(nsteps, cw=cw, iv_start_us=3000, iv_end_us=max(600, iv_us))
        else:
            drv.move_steps(nsteps, cw=cw, interval_us=iv_us)
    else:
        drv = build_driver()
        step_ms = max(1, int(rpm_to_interval_us(max(1, rpm), steps_per_rev) / 1000))
        drv.delay = step_ms
        drv.step(nsteps, cw=cw)


def mode_speed_sweep():
    print("\n--- MODO 3: Barrido de velocidad ---")
    spr_default = STEPS_PER_REV_DEFAULT.get(DRIVER, 200)
    try:
        val = input(f"Pasos/rev [{spr_default}]: ") if MICROPYTHON else "200"
        steps_per_rev = int(val) if val.strip() else spr_default
    except Exception:
        steps_per_rev = spr_default
    try:
        rpm_lo = int(input("RPM inicio [5]: ") if MICROPYTHON else "5")
        rpm_hi = int(input("RPM fin [60]: ") if MICROPYTHON else "60")
    except Exception:
        rpm_lo, rpm_hi = 5, 60
    cw = True if (input("Sentido 1=CW, 2=CCW [1]: ") if MICROPYTHON else "1").strip() != '2' else False
    steps_total = steps_per_rev // 2

    if DRIVER == 'A4988':
        drv = build_driver()
        print("Barriendo… (presiona 'm' para abortar)")
        for rpm in range(max(1, rpm_lo), max(1, rpm_hi)+1, 2):
            iv = rpm_to_interval_us(rpm, steps_per_rev)
            drv.move_steps(steps_total // 10, cw=cw, interval_us=iv)
            if check_menu_break():
                break
    else:
        drv = build_driver()
        print("Barriendo… (presiona 'm' para abortar)")
        for rpm in range(max(1, rpm_lo), max(1, rpm_hi)+1, 2):
            step_ms = max(1, int(rpm_to_interval_us(rpm, steps_per_rev) / 1000))
            drv.delay = step_ms
            drv.step(64, cw=cw)
            if check_menu_break():
                break


def mode_homing():
    print("\n--- MODO 4: Homing con fin de carrera ---")
    p = endstop_pin()
    if p is None:
        print("[Endstop] No disponible. Ver PIN_ENDSTOP en el código/PINES.md")
        input("ENTER para regresar…")
        return
    cw_home = (input("Dirección hacia home 1=CW, 2=CCW [2]: ") if MICROPYTHON else "2").strip() == '1'
    max_steps = 5000
    try:
        val = input("Máximo pasos búsqueda [5000]: ") if MICROPYTHON else "5000"
        if val.strip():
            max_steps = max(100, int(val))
    except Exception:
        pass

    # Velocidad segura
    spr_default = STEPS_PER_REV_DEFAULT.get(DRIVER, 200)
    rpm = 10
    if DRIVER == 'A4988':
        iv_us = rpm_to_interval_us(rpm, spr_default)
        drv = build_driver(base_interval_us=iv_us)
        drv.set_dir(cw_home)
        for _ in range(max_steps):
            if p.value() == 0:  # activo en LOW
                print("[Homing] Endstop alcanzado.")
                break
            drv.step_once(iv_us)
            if check_menu_break():
                break
    else:
        drv = build_driver()
        drv.delay = max(2, int(rpm_to_interval_us(rpm, spr_default)/1000))
        for _ in range(max_steps):
            if p.value() == 0:
                print("[Homing] Endstop alcanzado.")
                break
            drv.step(1, cw=cw_home)
            if check_menu_break():
                break


def mode_info():
    print("\n--- MODO 5: Información / ayuda ---\n")
    print("Conexiones por defecto (ver PINES.md):")
    print(f"  Driver: {DRIVER}")
    if DRIVER == 'A4988':
        print(f"  STEP={PIN_STEP}, DIR={PIN_DIR}, EN={PIN_EN} (LOW=enable)")
        print("  Pasos/rev típicos: 200 (sin microstepping). Ajusta según MS1/2/3.")
    else:
        print(f"  IN1={PIN_IN1}, IN2={PIN_IN2}, IN3={PIN_IN3}, IN4={PIN_IN4}")
        print("  28BYJ‑48 half‑step ≈ 2048 pasos por vuelta de salida.")
    print(f"  Endstop (opcional): GPIO{PIN_ENDSTOP} con pull‑up, contacto a GND.")
    print("\nAtajos:")
    print("  'm' + ENTER: regresa al menú desde cualquier modo.")
    input("ENTER para regresar…")


# =============================================================================
# Main
# =============================================================================

def main():
    print("\n" + "="*60)
    print("Práctica 7 — Motores a pasos")
    print("ESP32 + MicroPython")
    print("="*60)
    while True:
        choice = menu_select(timeout_s=8)
        if choice is None:
            continue
        if choice == '0':
            mode_config_driver()
        elif choice == '1':
            mode_jog()
        elif choice == '2':
            mode_move_n_steps()
        elif choice == '3':
            mode_speed_sweep()
        elif choice == '4':
            mode_homing()
        elif choice == '5':
            mode_info()
        elif choice and choice.lower() == 'q':
            print("\n[Salida] Programa terminado.")
            break
        else:
            print(f"[Inválida] '{choice}' no reconocida.")


if __name__ == "__main__":
    main()
