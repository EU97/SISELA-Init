"""
Programa principal (main.py) — ESP32 + MicroPython

Incluye:
  - Paso 4/5: 3 salidas (LEDs) y lectura de entradas (2 botones con pull-up)
  - Paso 6: Integración de todo
  - Menú por monitor serial para seleccionar el modo a ejecutar

Atajos del REPL durante la ejecución:
  - Escribe 'm' + ENTER para volver al menú.

Nota: Ajusta los pines a tu placa si es necesario.
"""

from machine import Pin
try:
    import utime as time  # MicroPython
except ImportError:  # editor/PC
    import time
import sys
try:
    import uselect  # Para lectura no bloqueante desde el REPL
except ImportError:
    # Algunos analizadores locales pueden no encontrar este módulo; en la placa sí existe.
    uselect = None

# Compatibilidad en editores/PC: polyfills mínimos
if not hasattr(time, "sleep_ms"):
    def _sleep_ms(ms):
        time.sleep(ms / 1000.0)
    time.sleep_ms = _sleep_ms  # type: ignore

if not hasattr(time, "ticks_ms"):
    def _ticks_ms():
        return int(time.time() * 1000)
    time.ticks_ms = _ticks_ms  # type: ignore

if not hasattr(time, "ticks_diff"):
    def _ticks_diff(a, b):
        return a - b
    time.ticks_diff = _ticks_diff  # type: ignore

# ==========================
# Configuración de pines
# ==========================

# LEDs (salidas)
LED1_PIN = 2   # LED integrado habitual
LED2_PIN = 4   # Cambia si tu placa usa otros pines disponibles
LED3_PIN = 5

# Botones (entradas con pull-up)
BTN1_PIN = 13
BTN2_PIN = 14

LED_ON_LEVEL = 1  # 1 si el LED enciende con nivel alto; 0 para activo-bajo


def make_led(pin_no):
    return Pin(pin_no, Pin.OUT, value=0 if LED_ON_LEVEL else 1)


def make_button(pin_no):
    # Pull-up interno; botón a GND => pulsado (nivel 0)
    return Pin(pin_no, Pin.IN, Pin.PULL_UP)


led1 = make_led(LED1_PIN)
led2 = make_led(LED2_PIN)
led3 = make_led(LED3_PIN)
btn1 = make_button(BTN1_PIN)
btn2 = make_button(BTN2_PIN)


# ==========================
# Utilidades REPL / Menú
# ==========================

def _new_poll():
    if uselect is None:
        return None
    p = uselect.poll()
    try:
        p.register(sys.stdin, uselect.POLLIN)
    except Exception:
        return None
    return p


def read_line_timeout(timeout_ms=0, poll_obj=None):
    """Lee una línea del REPL con timeout; devuelve str o None."""
    if uselect is None:
        # Sin uselect no hay lectura no bloqueante; evita bloqueo devolviendo None
        return None
    p = poll_obj or _new_poll()
    if p is None:
        return None
    res = p.poll(timeout_ms)
    if res:
        try:
            line = sys.stdin.readline()
            return line.strip() if line else None
        except Exception:
            return None
    return None


def flush_input(poll_obj=None):
    # Limpia cualquier entrada pendiente para no arrastrar comandos anteriores
    if uselect is None:
        return
    p = poll_obj or _new_poll()
    if p is None:
        return
    while True:
        res = p.poll(0)
        if not res:
            break
        try:
            _ = sys.stdin.readline()
        except Exception:
            break


def menu_select(timeout_s=8):
    print("\n=== Menú de modos (elige una opción y ENTER) ===")
    print("1) Blink LED1")
    print("2) Secuencia 3 LEDs (chaser)")
    print("3) Monitor de entradas (BTN1/BTN2)")
    print("4) Integrado (botones controlan patrón/velocidad)")
    print("(Esperando {}s; por defecto: 4)".format(timeout_s))
    poll = _new_poll()
    flush_input(poll)

    # Cuenta atrás sencilla
    for _ in range(timeout_s):
        line = read_line_timeout(1000, poll)
        if line:
            sel = line.strip().lower()
            if sel in ("1", "2", "3", "4"):
                return int(sel)
            print("Entrada no válida: {}".format(sel))
            print("Selecciona 1, 2, 3 o 4:")
    return 4  # por defecto integrado


def check_menu_break(poll_obj=None):
    """Devuelve True si el usuario escribe 'm' o 'menu' para volver al menú."""
    line = read_line_timeout(0, poll_obj)
    if not line:
        return False
    s = line.strip().lower()
    return s in ("m", "menu", "q", "exit")


# ==========================
# Subrutinas (modos)
# ==========================

def set_all_leds(v):
    led1.value(LED_ON_LEVEL if v else (0 if LED_ON_LEVEL else 1))
    led2.value(LED_ON_LEVEL if v else (0 if LED_ON_LEVEL else 1))
    led3.value(LED_ON_LEVEL if v else (0 if LED_ON_LEVEL else 1))


def blink_led1(period_s=1.0):
    print("[modo 1] Blink LED1 en GPIO {}".format(LED1_PIN))
    poll = _new_poll()
    state = False
    try:
        while True:
            if check_menu_break(poll):
                print("Volviendo al menú…")
                return
            state = not state
            led1.value(LED_ON_LEVEL if state else (0 if LED_ON_LEVEL else 1))
            print("LED1 {}".format("ON" if state else "OFF"))
            time.sleep(period_s)
    except KeyboardInterrupt:
        print("Interrumpido. Volviendo al menú…")


def chaser(period_s=0.3):
    print("[modo 2] Secuencia en 3 LEDs: {}, {}, {}".format(LED1_PIN, LED2_PIN, LED3_PIN))
    poll = _new_poll()
    leds = [led1, led2, led3]
    idx = 0
    try:
        while True:
            if check_menu_break(poll):
                print("Volviendo al menú…")
                return
            # Apaga todos y enciende uno
            for l in leds:
                l.value(0 if LED_ON_LEVEL else 1)
            leds[idx].value(LED_ON_LEVEL)
            idx = (idx + 1) % len(leds)
            time.sleep(period_s)
    except KeyboardInterrupt:
        print("Interrumpido. Volviendo al menú…")


def monitor_inputs(sample_ms=200):
    print("[modo 3] Monitor de entradas BTN1={} BTN2={} (pull-up, activo LOW)".format(BTN1_PIN, BTN2_PIN))
    poll = _new_poll()
    try:
        while True:
            if check_menu_break(poll):
                print("Volviendo al menú…")
                return
            b1 = 0 if btn1.value() == 0 else 1  # 0=pressed
            b2 = 0 if btn2.value() == 0 else 1
            # Refleja en LED2/LED3 (encendido si pulsado)
            led2.value(LED_ON_LEVEL if btn1.value() == 0 else (0 if LED_ON_LEVEL else 1))
            led3.value(LED_ON_LEVEL if btn2.value() == 0 else (0 if LED_ON_LEVEL else 1))
            print("BTN1={} BTN2={}".format("PRESSED" if b1 == 0 else "RELEASED", "PRESSED" if b2 == 0 else "RELEASED"))
            time.sleep_ms(sample_ms)
    except KeyboardInterrupt:
        print("Interrumpido. Volviendo al menú…")


def integrated_mode():
    """
    Modo integrado (paso 6):
      - BTN1 (activo LOW) alterna el patrón: chaser <-> parpadeo conjunto
      - BTN2 cicla la velocidad: [0.2, 0.5, 1.0] s
    """
    print("[modo 4] Integrado: BTN1=patrón, BTN2=velocidad. Escribe 'm' + ENTER para menú.")
    poll = _new_poll()

    speeds = [0.2, 0.5, 1.0]
    speed_idx = 1
    pattern = 0  # 0=chaser, 1=blink all

    last_b1 = btn1.value()
    last_b2 = btn2.value()
    last_toggle = time.ticks_ms()

    pos = 0
    try:
        while True:
            if check_menu_break(poll):
                print("Volviendo al menú…")
                return

            # Lectura con debounce sencillo (detección de flanco)
            now = time.ticks_ms()
            b1 = btn1.value()
            b2 = btn2.value()
            changed = False

            if b1 != last_b1 and time.ticks_diff(now, last_toggle) > 120:
                last_toggle = now
                last_b1 = b1
                if b1 == 0:  # pulsado
                    pattern ^= 1
                    print("Pattern -> {}".format("blink-all" if pattern else "chaser"))
                    changed = True

            if b2 != last_b2 and time.ticks_diff(now, last_toggle) > 120 and not changed:
                last_toggle = now
                last_b2 = b2
                if b2 == 0:  # pulsado
                    speed_idx = (speed_idx + 1) % len(speeds)
                    print("Speed -> {} s".format(speeds[speed_idx]))

            # Ejecuta patrón
            s = speeds[speed_idx]
            if pattern == 0:
                # chaser
                leds = [led1, led2, led3]
                for l in leds:
                    l.value(0 if LED_ON_LEVEL else 1)
                leds[pos].value(LED_ON_LEVEL)
                pos = (pos + 1) % len(leds)
            else:
                # blink all
                v = 1 if (now // int(s * 1000)) % 2 == 0 else 0
                set_all_leds(v)

            time.sleep(s)
    except KeyboardInterrupt:
        print("Interrumpido. Volviendo al menú…")


def main():
    print("[main] ESP32 listo. Escribe 'm' en cualquier modo para volver al menú.")
    while True:
        sel = menu_select()
        if sel == 1:
            blink_led1()
        elif sel == 2:
            chaser()
        elif sel == 3:
            monitor_inputs()
        else:
            integrated_mode()


if __name__ == "__main__":
    main()
