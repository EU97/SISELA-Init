"""
Práctica 6 — OLED SSD1306 por I2C (ESP32 + MicroPython)

Visualización local en pantalla OLED 128x64 de variables medidas.
Se integra opcionalmente un sensor BMP280 (si está presente en el mismo bus I2C)
para mostrar temperatura, presión y altitud estimada.

Modos:
  1) Dashboard: T/Presión/Altitud en texto
  2) Mini-gráfica: traza temporal de presión (hPa) o altitud (m)
  3) Scan I2C: muestra dispositivos detectados (hex)
  4) Demo OLED: texto rebotando

Salir/menú: escribir 'm' + ENTER en el terminal.
"""
# =============================================================================
# Imports & configuración
# =============================================================================
try:
    from machine import I2C, Pin
    import utime as time
    import uselect
    import sys
    MICROPYTHON = True
except ImportError:
    MICROPYTHON = False

from lib.ssd1306 import SSD1306_I2C
try:
    from lib.bmp280 import BMP280
except Exception:
    BMP280 = None

I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
I2C_FREQ = 400_000

OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_ADDR = 0x3C

SAMPLE_MS = 500

# =============================================================================
# Utilidades
# =============================================================================

def pressure_to_altitude(press_Pa, press_sea_level_Pa=101325.0):
    return 44330.0 * (1.0 - (press_Pa / press_sea_level_Pa) ** 0.1903)


def menu_select(timeout_s=6):
    print("\n" + "="*48)
    print("MENÚ — Práctica 6: OLED SSD1306 (I2C)")
    print("="*48)
    print("1) Dashboard (T/P/Alt)")
    print("2) Mini-gráfica")
    print("3) Scan I2C")
    print("4) Demo OLED")
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

# =============================================================================
# Inicialización hardware
# =============================================================================
if MICROPYTHON:
    i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
    print(f"[I2C] SCL=GPIO{I2C_SCL_PIN}, SDA=GPIO{I2C_SDA_PIN}, {I2C_FREQ}Hz")
    devs = i2c.scan()
    print(f"[I2C] Dispositivos: {[hex(d) for d in devs]}")
    oled = SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c, addr=OLED_ADDR)
    print("[OLED] SSD1306 inicializada (128x64)")

    # Intentar BMP280 en 0x76 y luego 0x77
    bmp = None
    if BMP280:
        for addr in (0x76, 0x77):
            try:
                bmp = BMP280(i2c, addr=addr)
                print(f"[BMP280] Detectado en 0x{addr:02X}")
                break
            except Exception:
                pass
        if bmp is None:
            print("[BMP280] No detectado. Se usará demo sin sensor.")
else:
    i2c = None
    oled = None
    bmp = None

# =============================================================================
# Modos
# =============================================================================

def mode_dashboard():
    print("\n--- MODO 1: Dashboard ---\nEscribe 'm'+ENTER para regresar…\n")
    while True:
        oled.fill(0)
        if bmp:
            t, p = bmp.read()
            hpa = p / 100.0
            alt = pressure_to_altitude(p)
            oled.text("BMP280:", 0, 0)
            oled.text("T: %5.2f C" % t, 0, 16)
            oled.text("P: %7.2f hPa" % hpa, 0, 28)
            oled.text("Alt: %6.1f m" % alt, 0, 40)
        else:
            oled.text("SIN SENSOR", 0, 0)
            oled.text("Conecta BMP280", 0, 16)
            oled.text("I2C 0x76/0x77", 0, 28)
            oled.text("SSD1306 lista", 0, 40)
        oled.show()
        if check_menu_break():
            break
        time.sleep_ms(SAMPLE_MS)


def _map(value, in_min, in_max, out_min, out_max):
    if value < in_min:
        value = in_min
    if value > in_max:
        value = in_max
    return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)


def mode_minigraph(variable="altitude"):
    print("\n--- MODO 2: Mini-gráfica ---\nEscribe 'm'+ENTER para regresar…\n")
    x = 0
    center_hpa = 1013.0
    span_hpa = 40.0  # 1013 +/- 20 hPa
    while True:
        oled.fill_rect(x, 0, 1, OLED_HEIGHT, 0)  # limpiar columna actual
        if bmp:
            t, p = bmp.read()
            hpa = p / 100.0
            alt = pressure_to_altitude(p)
            if variable == "altitude":
                # Escala 0..200 m al alto de la pantalla
                y = OLED_HEIGHT - 1 - _map(alt, 0, 200, 0, OLED_HEIGHT - 1)
            else:
                # Escala presión alrededor de 1013 hPa
                y = OLED_HEIGHT - 1 - _map(hpa, center_hpa - span_hpa/2, center_hpa + span_hpa/2, 0, OLED_HEIGHT - 1)
            if 0 <= y < OLED_HEIGHT:
                oled.pixel(x, y, 1)
            # Encabezado
            oled.fill_rect(0, 0, OLED_WIDTH, 10, 0)
            txt = ("Alt %.0fm" % alt) if variable == "altitude" else ("P %.1fhPa" % hpa)
            oled.text(txt, 0, 0)
        else:
            oled.text("SIN SENSOR", 0, 0)
        oled.show()
        x = (x + 1) % OLED_WIDTH
        if check_menu_break():
            break
        time.sleep_ms(SAMPLE_MS)


def mode_scan():
    print("\n--- MODO 3: Scan I2C ---\nEscribe 'm'+ENTER para regresar…\n")
    while True:
        devs = i2c.scan()
        oled.fill(0)
        oled.text("SCAN I2C:", 0, 0)
        y = 12
        line = ""
        for d in devs:
            token = "%02X " % d
            if len(line) + len(token) > 20:
                oled.text(line, 0, y); y += 10; line = ""
            line += token
        if line:
            oled.text(line, 0, y)
        oled.show()
        if check_menu_break():
            break
        time.sleep_ms(750)


def mode_demo():
    print("\n--- MODO 4: Demo OLED ---\nEscribe 'm'+ENTER para regresar…\n")
    text = "SISELA P6"
    x, y = 0, 20
    vx, vy = 2, 2
    while True:
        oled.fill(0)
        oled.text(text, x, y, 1)
        oled.show()
        x += vx; y += vy
        if x <= 0 or x >= OLED_WIDTH - len(text)*8: vx *= -1
        if y <= 0 or y >= OLED_HEIGHT - 8: vy *= -1
        if check_menu_break():
            break
        time.sleep_ms(30)

# =============================================================================
# Main
# =============================================================================

def main():
    print("\n" + "="*60)
    print("Práctica 6 — OLED SSD1306 (I2C)")
    print("ESP32 + MicroPython")
    print("="*60)
    if not MICROPYTHON:
        print("[PC] Simulación limitada.")
        return
    while True:
        choice = menu_select(timeout_s=6)
        if choice is None:
            continue
        if choice == '1':
            mode_dashboard()
        elif choice == '2':
            # Elegir variable de la mini-gráfica (presión/altitud). Por defecto altitud.
            mode_minigraph(variable="altitude")
        elif choice == '3':
            mode_scan()
        elif choice == '4':
            mode_demo()
        elif choice.lower() == 'q':
            print("\n[Salida] Programa terminado.")
            break
        else:
            print(f"[Inválida] '{choice}' no reconocida.")


if __name__ == "__main__":
    main()
