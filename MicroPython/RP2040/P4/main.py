"""
Práctica 4 — BMP180 Altímetro Barométrico (RP2040 + MicroPython)
main.py: Lectura I2C del BMP180 con compensación completa y cálculo de altitud

BMP180: Sensor digital de presión barométrica y temperatura (Bosch)
 - Interfaz: I2C (dirección 0x77)
 - Rango presión: 300–1100 hPa (30–110 kPa)
 - Rango temperatura: −40 a +85 °C
 - Resolución: hasta 0.01 hPa (modo ultra-alta resolución, oss=3)
 - Compensación: 11 coeficientes de calibración leídos de EEPROM

DIFERENCIAS RP2040 vs ESP32:
 - I2C: GP0/GP1 (I2C0) vs GPIO21/GPIO22
 - Frecuencia I2C: hasta 1 MHz en RP2040 vs 400 kHz ESP32
 - No requiere configuración ADC (sensor I2C, comunicación digital)
 - Alimentación: 3V3 directo (3.3V), VSYS (5V mediante regulador)

Algoritmo de altitud:
 h = 44330 × (1 − (P / P₀)^(1/5.255))   [metros]

Modos de operación:
  1) Datos crudos + coeficientes de calibración
  2) Temperatura y presión compensadas (algoritmo visible paso a paso)
  3) Altímetro barométrico (m y ft, ajuste QNH interactivo)
  4) Monitor CSV continuo (para altimeter_gui.py)
  5) Comparativa de alturas (medición guiada a diferentes niveles)
"""

# ============================================================================
# Imports & Polyfills
# ============================================================================
try:
    from machine import I2C, Pin
    import utime as time
    import uselect
    import sys
    MICROPYTHON = True
except ImportError:
    print("[PC Mode] Usando polyfills para análisis estático.")
    MICROPYTHON = False

    class _FakeI2C:
        def __init__(self, *a, **kw): pass
        def scan(self): return [0x77]
        def readfrom_mem(self, addr, reg, n):
            if reg == 0xD0: return bytes([0x55])
            return bytes(n)
        def writeto_mem(self, addr, reg, data): pass
    I2C = _FakeI2C

    class Pin:
        IN = 1; OUT = 2; PULL_UP = 3
        def __init__(self, *a, **kw): pass
        def value(self, v=None): return 0

    class time:
        @staticmethod
        def sleep_ms(ms): pass
        @staticmethod
        def ticks_ms(): return 0
        @staticmethod
        def ticks_diff(a, b): return 0

    class uselect:
        POLLIN = 1
        @staticmethod
        def poll():
            class _P:
                def register(self, *a): pass
                def poll(self, t): return []
            return _P()

    import sys

import math

# ============================================================================
# Configuración de hardware — RP2040
# ============================================================================
I2C_ID       = 0            # Bus I2C0
SDA_PIN      = 0            # GP0 (I2C0 SDA)
SCL_PIN      = 1            # GP1 (I2C0 SCL)
I2C_FREQ     = 100_000      # 100 kHz (modo estándar)

BMP_ADDR     = 0x77         # Dirección I2C del BMP180
BMP_OSS      = 1            # Sobremuestreo: 0=Ultra Low, 1=Estándar, 2=Alto, 3=Ultra

SAMPLE_RATE_MS = 200        # Periodo de muestreo (200 ms → 5 Hz)

# Referencia de presión a nivel del mar (Pa)
SEA_LEVEL_PRESSURE = 101325.0

# ============================================================================
# Inicialización de hardware
# ============================================================================
sensor = None

if MICROPYTHON:
    from bmp180 import BMP180

    i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=I2C_FREQ)
    devices = i2c.scan()
    print(f"I2C bus {I2C_ID}: SDA=GP{SDA_PIN}, SCL=GP{SCL_PIN}, {I2C_FREQ//1000} kHz")
    print(f"Dispositivos I2C: {['0x%02X' % d for d in devices]}")

    if BMP_ADDR in devices:
        sensor = BMP180(i2c, addr=BMP_ADDR, oss=BMP_OSS)
        print(f"BMP180 detectado en 0x{BMP_ADDR:02X}")
        oss_names = ["Ultra Low", "Estándar", "Alto", "Ultra Alto"]
        print(f"Sobremuestreo: modo {BMP_OSS} ({oss_names[BMP_OSS]})")
    else:
        print(f"[ERROR] BMP180 no encontrado en 0x{BMP_ADDR:02X}")
        print("Verifica: SDA→GP0, SCL→GP1, VCC→3V3, GND→GND")

# ============================================================================
# Utilidades REPL
# ============================================================================
def poll_input(timeout_ms=100):
    """Lee entrada REPL sin bloquear."""
    if not MICROPYTHON:
        return None
    poll = uselect.poll()
    poll.register(sys.stdin, uselect.POLLIN)
    events = poll.poll(timeout_ms)
    if events:
        line = sys.stdin.readline().strip()
        return line if line else None
    return None

def check_menu_break():
    """Verifica 'm' para regresar al menú."""
    line = poll_input(0)
    if line and line.lower() == 'm':
        print("\n[Menú] Regresando al menú principal...")
        return True
    return False

def wait_enter(msg="Presiona ENTER para continuar..."):
    """Espera ENTER."""
    print(msg, end="")
    if not MICROPYTHON:
        return
    while True:
        line = poll_input(500)
        if line is not None:
            break
        time.sleep_ms(100)

def menu_select(timeout_s=8):
    """Menú principal con timeout."""
    print("\n" + "=" * 56)
    print("  MENÚ PRINCIPAL — Práctica 4: BMP180 Altímetro")
    print("=" * 56)
    print("  1) Datos crudos + coeficientes de calibración")
    print("  2) Temperatura y presión compensadas")
    print("  3) Altímetro barométrico (m / ft)")
    print("  4) Monitor CSV continuo (para visualización)")
    print("  5) Comparativa de alturas")
    print("  q) Salir")
    print("=" * 56)
    print(f"  Selecciona opción (timeout: {timeout_s}s): ", end="")

    if not MICROPYTHON:
        return "1"

    start = time.ticks_ms()
    while True:
        elapsed = time.ticks_diff(time.ticks_ms(), start) / 1000.0
        if elapsed >= timeout_s:
            print("\n[Timeout] Reintentando menú...")
            return None
        line = poll_input(100)
        if line:
            return line
        time.sleep_ms(50)

# ============================================================================
# Modo 1: Datos crudos + coeficientes
# ============================================================================
def mode_raw_data():
    """Muestra coeficientes de calibración y lecturas crudas UT/UP."""
    print("\n--- MODO 1: Datos Crudos + Coeficientes ---")
    if sensor is None:
        print("[ERROR] Sensor no inicializado."); return

    calib = sensor.get_calibration()
    print("\nCoeficientes de calibración (EEPROM 0xAA–0xBF):")
    print("  ┌─────────────────────────────────────┐")
    print(f"  │ AC1 = {calib['AC1']:>7d}  (signed)          │")
    print(f"  │ AC2 = {calib['AC2']:>7d}  (signed)          │")
    print(f"  │ AC3 = {calib['AC3']:>7d}  (signed)          │")
    print(f"  │ AC4 = {calib['AC4']:>7d}  (unsigned)        │")
    print(f"  │ AC5 = {calib['AC5']:>7d}  (unsigned)        │")
    print(f"  │ AC6 = {calib['AC6']:>7d}  (unsigned)        │")
    print(f"  │ B1  = {calib['B1']:>7d}  (signed)          │")
    print(f"  │ B2  = {calib['B2']:>7d}  (signed)          │")
    print(f"  │ MB  = {calib['MB']:>7d}  (signed)          │")
    print(f"  │ MC  = {calib['MC']:>7d}  (signed)          │")
    print(f"  │ MD  = {calib['MD']:>7d}  (signed)          │")
    print("  └─────────────────────────────────────┘")
    print(f"  OSS = {sensor.oss} ({BMP180._OSS_NAMES[sensor.oss]})")

    print("\nLecturas crudas continuas (presiona 'm' + ENTER para menú):\n")
    while True:
        ut = sensor.read_raw_temp()
        up = sensor.read_raw_pressure()
        print(f"  UT = {ut:6d}  |  UP = {up:8d}")
        if check_menu_break():
            break
        time.sleep_ms(SAMPLE_RATE_MS)

# ============================================================================
# Modo 2: Temperatura y presión compensadas
# ============================================================================
def mode_compensated():
    """T y P compensadas con pasos del algoritmo visibles."""
    print("\n--- MODO 2: Temperatura y Presión Compensadas ---")
    if sensor is None:
        print("[ERROR] Sensor no inicializado."); return

    print("Algoritmo de compensación (Bosch BMP180 datasheet):")
    print("  T: UT → X1,X2 → B5 → T = (B5+8)/16  [0.1°C]")
    print("  P: UP → B6,B3,B4,B7 → correcciones → P  [Pa]")
    print("\nPresiona 'm' + ENTER para menú.\n")

    td = sensor.temperature_detailed()
    print("── Compensación de Temperatura ──")
    print(f"  UT   = {td['UT']}")
    print(f"  X1   = (UT − AC6) × AC5 / 2¹⁵ = {td['X1']}")
    print(f"  X2   = MC × 2¹¹ / (X1 + MD)   = {td['X2']}")
    print(f"  B5   = X1 + X2 = {td['B5']}")
    print(f"  T    = (B5 + 8) / 16 = {td['T_raw']}  →  {td['T_C']:.1f} °C")

    pd = sensor.pressure_detailed()
    print("\n── Compensación de Presión ──")
    print(f"  UP   = {pd['UP']}")
    print(f"  B5   = {pd['B5']},  B6 = {pd['B6']}")
    print(f"  B3   = {pd['B3']},  B4 = {pd['B4']}")
    print(f"  B7   = {pd['B7']}")
    print(f"  P    = {pd['P_Pa']} Pa  →  {pd['P_hPa']:.2f} hPa")

    print("\n── Lecturas continuas ──\n")
    while True:
        T, P, _ = sensor.read_all()
        P_hPa = P / 100.0
        print(f"  T: {T:6.1f} °C  |  P: {P_hPa:8.2f} hPa  ({P} Pa)")
        if check_menu_break():
            break
        time.sleep_ms(SAMPLE_RATE_MS)

# ============================================================================
# Modo 3: Altímetro barométrico
# ============================================================================
def mode_altimeter():
    """Altitud en metros y pies con ajuste QNH interactivo."""
    global SEA_LEVEL_PRESSURE
    print("\n--- MODO 3: Altímetro Barométrico ---")
    if sensor is None:
        print("[ERROR] Sensor no inicializado."); return

    print(f"  QNH actual: {SEA_LEVEL_PRESSURE:.0f} Pa ({SEA_LEVEL_PRESSURE/100:.2f} hPa)")
    print("  Fórmula: h = 44330 × (1 − (P/P₀)^(1/5.255))")
    print("\n  'q' + ENTER → Ajustar QNH     'm' + ENTER → Menú\n")

    while True:
        T, P, h = sensor.read_all(p0=SEA_LEVEL_PRESSURE)
        P_hPa = P / 100.0
        h_ft = h * 3.28084

        print(f"  Alt: {h:7.1f} m ({h_ft:7.0f} ft)  |  P: {P_hPa:7.2f} hPa  |  T: {T:5.1f} °C  |  QNH: {SEA_LEVEL_PRESSURE/100:.1f} hPa")

        line = poll_input(0)
        if line:
            if line.lower() == 'm':
                print("\n[Menú] Regresando...")
                break
            elif line.lower() == 'q':
                print("\n  Ajuste de QNH:")
                print(f"  Actual: {SEA_LEVEL_PRESSURE:.0f} Pa ({SEA_LEVEL_PRESSURE/100:.2f} hPa)")
                print("  Ingresa nueva presión (hPa), ej: 1013.25")
                print("  O 'a' + altitud conocida (m), ej: a540")
                print("  Ingreso: ", end="")
                while True:
                    val = poll_input(500)
                    if val:
                        try:
                            if val.startswith('a') or val.startswith('A'):
                                alt_known = float(val[1:])
                                SEA_LEVEL_PRESSURE = sensor.sea_level_pressure(alt_known)
                                print(f"\n  [QNH] Desde {alt_known:.0f} m: {SEA_LEVEL_PRESSURE/100:.2f} hPa")
                            else:
                                SEA_LEVEL_PRESSURE = float(val) * 100.0
                                print(f"\n  [QNH] Establecido: {SEA_LEVEL_PRESSURE/100:.2f} hPa")
                        except ValueError:
                            print("\n  [Error] Valor inválido.")
                        break
                    time.sleep_ms(100)
        time.sleep_ms(SAMPLE_RATE_MS)

# ============================================================================
# Modo 4: Monitor CSV continuo
# ============================================================================
def mode_csv_monitor():
    """Emite datos CSV para altimeter_gui.py."""
    global SEA_LEVEL_PRESSURE
    print("\n--- MODO 4: Monitor CSV Continuo ---")
    if sensor is None:
        print("[ERROR] Sensor no inicializado."); return

    print("Formato: timestamp_ms,temp_C,pressure_hPa,altitude_m")
    print("Presiona 'm' + ENTER para detener.\n")
    print("timestamp_ms,temp_C,pressure_hPa,altitude_m")

    start_t = time.ticks_ms()
    while True:
        t = time.ticks_diff(time.ticks_ms(), start_t)
        T, P, h = sensor.read_all(p0=SEA_LEVEL_PRESSURE)
        P_hPa = P / 100.0
        print(f"{t},{T:.1f},{P_hPa:.2f},{h:.1f}")
        if check_menu_break():
            break
        time.sleep_ms(SAMPLE_RATE_MS)

# ============================================================================
# Modo 5: Comparativa de alturas
# ============================================================================
def mode_height_comparison():
    """Medición guiada en diferentes alturas."""
    global SEA_LEVEL_PRESSURE
    print("\n--- MODO 5: Comparativa de Alturas ---")
    if sensor is None:
        print("[ERROR] Sensor no inicializado."); return

    print("Mide presión y altitud en diferentes ubicaciones")
    print("(pisos de un edificio, escaleras, etc.)\n")

    # Paso 1: Referencia
    print("═══ Paso 1: Referencia QNH ═══")
    print(f"QNH actual: {SEA_LEVEL_PRESSURE/100:.2f} hPa")
    print("Ingresa altitud conocida (m), o ENTER para ISA: ", end="")

    while True:
        val = poll_input(500)
        if val is not None:
            if val == '':
                print(f"\n  ISA: {SEA_LEVEL_PRESSURE/100:.2f} hPa")
            else:
                try:
                    alt_ref = float(val)
                    SEA_LEVEL_PRESSURE = sensor.sea_level_pressure(alt_ref)
                    print(f"\n  QNH desde {alt_ref:.0f} m: {SEA_LEVEL_PRESSURE/100:.2f} hPa")
                except ValueError:
                    print("\n  Usando ISA.")
            break
        time.sleep_ms(100)

    # Paso 2: Mediciones
    measurements = []
    NUM_SAMPLES = 10

    print("\n═══ Paso 2: Mediciones ═══")
    print(f"Se tomarán {NUM_SAMPLES} lecturas por punto.")
    print("Ingresa nombre del punto o 'fin' para resumen.\n")

    point_num = 1
    while True:
        print(f"── Punto {point_num} ──")
        print("Nombre (o 'fin'): ", end="")
        name = None
        while True:
            val = poll_input(500)
            if val is not None:
                name = val
                break
            time.sleep_ms(100)

        if name.lower() == 'fin':
            break

        print(f"  Midiendo '{name}' ({NUM_SAMPLES} muestras)...")
        temps = []; pressures = []; altitudes = []
        for _ in range(NUM_SAMPLES):
            T, P, h = sensor.read_all(p0=SEA_LEVEL_PRESSURE)
            temps.append(T)
            pressures.append(P / 100.0)
            altitudes.append(h)
            time.sleep_ms(200)

        avg_T = sum(temps) / len(temps)
        avg_P = sum(pressures) / len(pressures)
        avg_h = sum(altitudes) / len(altitudes)
        std_h = math.sqrt(sum((x - avg_h)**2 for x in altitudes) / len(altitudes))

        measurements.append({
            'name': name, 'num': point_num,
            'T': avg_T, 'P': avg_P, 'h': avg_h, 'std_h': std_h
        })
        print(f"  ✓ {name}: T={avg_T:.1f}°C  P={avg_P:.2f} hPa  Alt={avg_h:.1f} m (±{std_h:.2f} m)")
        point_num += 1
        print()

    # Paso 3: Resumen
    if len(measurements) < 2:
        print("\n[Info] Se necesitan al menos 2 puntos.")
        return

    print("\n" + "=" * 60)
    print("  RESUMEN DE COMPARATIVA DE ALTURAS")
    print("=" * 60)
    print(f"  QNH: {SEA_LEVEL_PRESSURE/100:.2f} hPa")

    print("  ┌─────┬──────────────────┬────────┬──────────┬──────────┬────────────┐")
    print("  │ #   │ Ubicación        │ T (°C) │ P (hPa)  │ Alt (m)  │ σ (m)      │")
    print("  ├─────┼──────────────────┼────────┼──────────┼──────────┼────────────┤")
    for m in measurements:
        n = m['name'][:16].ljust(16)
        print(f"  │ {m['num']:>3d} │ {n} │ {m['T']:5.1f}  │ {m['P']:8.2f} │ {m['h']:8.1f} │ ±{m['std_h']:<9.3f} │")
    print("  └─────┴──────────────────┴────────┴──────────┴──────────┴────────────┘")

    print("\n  Diferencias:")
    for i in range(1, len(measurements)):
        prev = measurements[i-1]; curr = measurements[i]
        dh = curr['h'] - prev['h']; dp = curr['P'] - prev['P']
        print(f"    {prev['name']} → {curr['name']}: Δh = {dh:+.1f} m  (ΔP = {dp:+.2f} hPa)")

    total_dh = measurements[-1]['h'] - measurements[0]['h']
    print(f"\n  Total: Δh = {total_dh:+.1f} m ({total_dh*3.28084:+.0f} ft)")
    print("  Referencia: ~8.43 m por hPa (ISA, cerca del suelo)")
    wait_enter("\n  ENTER para menú...")

# ============================================================================
# Main
# ============================================================================
def main():
    print("\n" + "=" * 56)
    print("  Práctica 4 — BMP180 Altímetro Barométrico")
    print("  RP2040 (Raspberry Pi Pico) + MicroPython")
    print("=" * 56)
    print(f"  I2C: SDA=GP{SDA_PIN}, SCL=GP{SCL_PIN}, {I2C_FREQ//1000} kHz")
    print(f"  Sensor: BMP180 @ 0x{BMP_ADDR:02X}, OSS={BMP_OSS}")
    print(f"  QNH: {SEA_LEVEL_PRESSURE/100:.2f} hPa")
    if sensor:
        T, P, h = sensor.read_all(p0=SEA_LEVEL_PRESSURE)
        print(f"  Lectura inicial: T={T:.1f}°C, P={P/100:.2f} hPa, Alt={h:.1f} m")
    print("=" * 56)

    while True:
        choice = menu_select(timeout_s=8)
        if choice is None:
            continue
        if choice == '1':
            mode_raw_data()
        elif choice == '2':
            mode_compensated()
        elif choice == '3':
            mode_altimeter()
        elif choice == '4':
            mode_csv_monitor()
        elif choice == '5':
            mode_height_comparison()
        elif choice.lower() == 'q':
            print("\n[Salida] Programa terminado.")
            break
        else:
            print(f"\n[Opción inválida] '{choice}'")

if __name__ == "__main__":
    main()
