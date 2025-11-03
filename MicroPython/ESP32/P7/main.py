"""
Práctica 7 — Control de Motores a Pasos

Modos de la práctica:
  1) Jog: avanza/retrocede paso a paso (manual)
  2) Mover N pasos con velocidad y dirección configurables
  3) Barrido: avanza hasta límite, retrocede, repite
  4) Homing: buscar fin de carrera (si está conectado)
  5) Info del driver: muestra configuración actual

Presiona 'm' + ENTER en cualquier modo para regresar al menú.
"""

import sys
import uselect
import utime as time
from machine import Pin

# Importar drivers según disponibilidad
try:
    from lib.stepper_a4988 import StepperA4988
except ImportError:
    StepperA4988 = None

try:
    from lib.stepper_uln2003 import StepperULN2003
except ImportError:
    StepperULN2003 = None


# --- Configuración global ---
DRIVER_TYPE = "A4988"  # Cambiar a "ULN2003" para usar 28BYJ-48

# Pines para A4988/DRV8825
A4988_STEP_PIN = 18
A4988_DIR_PIN = 19
A4988_EN_PIN = 5  # Opcional

# Pines para ULN2003 (28BYJ-48)
ULN2003_PINS = [26, 25, 33, 32]  # IN1, IN2, IN3, IN4

# Fin de carrera opcional
ENDSTOP_PIN = 4  # GPIO4, pull-up interno, contacto a GND

# Parámetros de movimiento
DEFAULT_RPM = 60
DEFAULT_STEPS = 200  # Para NEMA 17 con A4988 (1/1 microstepping)


def _stdin_key_available():
    """True si hay datos en stdin sin bloquear."""
    sp = uselect.poll()
    sp.register(sys.stdin, uselect.POLLIN)
    res = sp.poll(0)
    return bool(res)


def _readline_nonblocking():
    """Lee línea si hay datos disponibles, en otro caso cadena vacía."""
    if _stdin_key_available():
        return sys.stdin.readline().strip()
    return ""


def rpm_to_interval_us(rpm: float, steps_per_rev: int) -> int:
    """Convierte RPM a intervalo entre pasos en microsegundos."""
    if rpm <= 0:
        return 100000  # muy lento
    steps_per_sec = (rpm * steps_per_rev) / 60.0
    if steps_per_sec <= 0:
        return 100000
    interval_sec = 1.0 / steps_per_sec
    return int(interval_sec * 1_000_000)


def _build_driver(driver_type: str):
    """Construye el driver según el tipo seleccionado."""
    if driver_type == "A4988":
        if StepperA4988 is None:
            print("[ERROR] Driver A4988 no disponible. Verifica lib/stepper_a4988.py")
            return None
        en_pin = Pin(A4988_EN_PIN, Pin.OUT) if A4988_EN_PIN else None
        driver = StepperA4988(
            step_pin=A4988_STEP_PIN,
            dir_pin=A4988_DIR_PIN,
            enable_pin=en_pin
        )
        driver.enable()
        return driver
    elif driver_type == "ULN2003":
        if StepperULN2003 is None:
            print("[ERROR] Driver ULN2003 no disponible. Verifica lib/stepper_uln2003.py")
            return None
        driver = StepperULN2003(pins=ULN2003_PINS)
        return driver
    else:
        print("[ERROR] Tipo de driver desconocido: {}".format(driver_type))
        return None


def _setup_endstop():
    """Configura el pin de fin de carrera con pull-up interno."""
    endstop = Pin(ENDSTOP_PIN, Pin.IN, Pin.PULL_UP)
    return endstop


def mode_jog(driver):
    """Modo Jog: avanza (+) o retrocede (-) paso a paso."""
    print("\n[Modo 1] Jog. Presiona '+' avanza, '-' retrocede, 'm' menú.")
    interval_us = rpm_to_interval_us(DEFAULT_RPM, DEFAULT_STEPS)
    while True:
        line = _readline_nonblocking().lower()
        if line == "m":
            return
        elif line == "+":
            driver.step(1, interval_us)
            print("→ Adelante")
        elif line == "-":
            driver.step(-1, interval_us)
            print("← Atrás")
        time.sleep_ms(10)


def mode_move_n_steps(driver):
    """Modo mover N pasos: pide número de pasos, dirección y RPM."""
    print("\n[Modo 2] Mover N pasos. 'm' para menú.")
    while True:
        print("\nIngresa pasos (ej: 200 o -200 para retroceder): ", end="")
        line = sys.stdin.readline().strip()
        if not line:
            continue
        if line.lower() == "m":
            return
        try:
            steps = int(line)
        except ValueError:
            print("Entrada inválida. Usa números enteros o 'm'.")
            continue

        print("Ingresa RPM (default {}): ".format(DEFAULT_RPM), end="")
        rpm_line = sys.stdin.readline().strip()
        if rpm_line.lower() == "m":
            return
        if rpm_line:
            try:
                rpm = float(rpm_line)
            except ValueError:
                rpm = DEFAULT_RPM
        else:
            rpm = DEFAULT_RPM

        interval_us = rpm_to_interval_us(rpm, DEFAULT_STEPS)
        print("Moviendo {} pasos a {} RPM...".format(steps, rpm))
        driver.step(steps, interval_us)
        print("Movimiento completado.")


def mode_sweep(driver, endstop=None):
    """Modo barrido: avanza hasta límite, retrocede, repite."""
    print("\n[Modo 3] Barrido. Avanza hasta fin de carrera (o límite), retrocede. 'm' menú.")
    interval_us = rpm_to_interval_us(DEFAULT_RPM, DEFAULT_STEPS)
    max_steps_forward = 400  # Límite si no hay endstop

    while True:
        # Avanzar
        print("→ Avanzando...")
        moved = 0
        for _ in range(max_steps_forward):
            if endstop and endstop.value() == 0:
                print("Fin de carrera alcanzado.")
                break
            driver.step(1, interval_us)
            moved += 1
            if _readline_nonblocking().lower() == "m":
                return
            time.sleep_ms(1)

        time.sleep(1)

        # Retroceder
        print("← Retrocediendo...")
        for _ in range(moved):
            driver.step(-1, interval_us)
            if _readline_nonblocking().lower() == "m":
                return
            time.sleep_ms(1)

        time.sleep(1)


def mode_homing(driver, endstop):
    """Modo homing: busca el fin de carrera retrocediendo."""
    print("\n[Modo 4] Homing. Retrocede hasta fin de carrera. 'm' menú.")
    if endstop is None:
        print("[WARN] Fin de carrera no configurado en GPIO{}. Abortando.".format(ENDSTOP_PIN))
        time.sleep(2)
        return

    interval_us = rpm_to_interval_us(DEFAULT_RPM // 2, DEFAULT_STEPS)  # Más lento
    max_steps = 1000  # Límite de seguridad

    print("Iniciando homing (retrocediendo)...")
    for i in range(max_steps):
        if endstop.value() == 0:
            print("Fin de carrera alcanzado en {} pasos.".format(i))
            # Avanzar un poco para liberar
            time.sleep_ms(200)
            driver.step(10, interval_us)
            print("Liberado 10 pasos. Homing completado.")
            time.sleep(1)
            return
        driver.step(-1, interval_us)
        if _readline_nonblocking().lower() == "m":
            return
        time.sleep_ms(5)

    print("Homing no completado (límite de {} pasos alcanzado).".format(max_steps))
    time.sleep(1)


def mode_info(_driver, driver_type: str):
    """Muestra información del driver actual."""
    print("\n[Modo 5] Info del driver")
    print("Tipo: {}".format(driver_type))
    if driver_type == "A4988":
        print("  STEP: GPIO{}".format(A4988_STEP_PIN))
        print("  DIR: GPIO{}".format(A4988_DIR_PIN))
        print("  ENABLE: GPIO{}".format(A4988_EN_PIN if A4988_EN_PIN else "N/A"))
        print("  Pasos por revolución (1/1): {}".format(DEFAULT_STEPS))
    elif driver_type == "ULN2003":
        print("  Pines IN1-IN4: {}".format(ULN2003_PINS))
        print("  Motor: 28BYJ-48 (4096 pasos/rev en modo half-step)")
    print("  RPM por defecto: {}".format(DEFAULT_RPM))
    print("  Fin de carrera: GPIO{} {}".format(
        ENDSTOP_PIN,
        "(configurado)" if _setup_endstop() else "(no disponible)"
    ))
    input("\nPresiona ENTER para regresar al menú...")


MENU = """
==============================
 Práctica 7 — Motores a Pasos
 Driver: {}
------------------------------
 1) Jog (+ / -)
 2) Mover N pasos
 3) Barrido (con/sin endstop)
 4) Homing (requiere endstop)
 5) Info del driver
==============================
"""


def main():
    driver = _build_driver(DRIVER_TYPE)
    if driver is None:
        print("[FATAL] No se pudo inicializar el driver. Revisa la configuración.")
        return

    endstop = _setup_endstop()
    if endstop:
        print("[INFO] Fin de carrera configurado en GPIO{}.".format(ENDSTOP_PIN))
    else:
        print("[INFO] Fin de carrera no disponible.")

    try:
        while True:
            print(MENU.format(DRIVER_TYPE))
            sel = input("Selecciona opción: ")
            if not sel:
                continue
            if sel == "1":
                mode_jog(driver)
            elif sel == "2":
                mode_move_n_steps(driver)
            elif sel == "3":
                mode_sweep(driver, endstop)
            elif sel == "4":
                mode_homing(driver, endstop)
            elif sel == "5":
                mode_info(driver, DRIVER_TYPE)
            else:
                print("Opción no válida.")
    finally:
        if hasattr(driver, 'disable'):
            driver.disable()
        if hasattr(driver, 'release'):
            driver.release()


if __name__ == "__main__":
    main()

