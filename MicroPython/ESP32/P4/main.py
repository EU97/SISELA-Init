"""
Práctica 4 — BMP180 Altímetro Barométrico (ESP32 + MicroPython)
main.py: Lectura I2C del BMP180 con compensación completa y cálculo de altitud

BMP180: Sensor digital de presión barométrica y temperatura (Bosch)
 - Interfaz: I2C (dirección 0x77)
 - Rango presión: 300–1100 hPa (30–110 kPa)
 - Rango temperatura: −40 a +85 °C
 - Resolución: hasta 0.01 hPa (modo ultra-alta resolución, oss=3)
 - Compensación: 11 coeficientes de calibración leídos de EEPROM

Algoritmo de altitud:
 h = 44330 × (1 − (P / P₀)^(1/5.255))   [metros]
 P₀ = presión a nivel del mar (QNH), ISA estándar = 101325 Pa

Modos de operación:
  1) Datos crudos + coeficientes de calibración
  2) Temperatura y presión compensadas (algoritmo visible paso a paso)
  3) Altímetro barométrico (m y ft, ajuste QNH interactivo)
  4) Monitor CSV continuo (para altimeter_gui.py)
  5) Comparativa de alturas (medición guiada a diferentes niveles)
  6) Análisis de ruido y muestreo   (captura de bloque + estadística en placa)
  7) Filtro digital en vivo          (media móvil / mediana / EMA, CSV crudo+filtrado)

Los modos 6 y 7 alimentan la toolkit PC `tools/sisela_signal/`:
  python -m sisela_signal spectrum     --file cap.csv --col alt_m
  python -m sisela_signal characterize  --file cap.csv --col alt_m --mode allan
  python -m sisela_signal filter        --file cap.csv --col alt_raw --kind movavg --n 8
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

# siglab: utilidades de análisis de señales en la placa (lib/siglab.py).
# Importa también en CPython (se auto-adapta); en la placa vive en /lib.
try:
    from siglab import BlockSampler, Stats, MovAvg, Median, Ema
    HAVE_SIGLAB = True
except ImportError:
    HAVE_SIGLAB = False

# ============================================================================
# Configuración de hardware
# ============================================================================
I2C_ID       = 0            # Bus I2C
SDA_PIN      = 21           # GPIO21 (SDA por defecto ESP32)
SCL_PIN      = 22           # GPIO22 (SCL por defecto ESP32)
I2C_FREQ     = 100_000      # 100 kHz (modo estándar)

BMP_ADDR     = 0x77         # Dirección I2C del BMP180
BMP_OSS      = 1            # Sobremuestreo: 0=Ultra Low, 1=Estándar, 2=Alto, 3=Ultra

SAMPLE_RATE_MS = 200        # Periodo de muestreo (200 ms → 5 Hz)

# Referencia de presión a nivel del mar (Pa)
# ISA estándar: 101325 Pa.  Ajustar al QNH local para altitud real.
SEA_LEVEL_PRESSURE = 101325.0

# ============================================================================
# Inicialización de hardware
# ============================================================================
sensor = None

if MICROPYTHON:
    from bmp180 import BMP180

    i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=I2C_FREQ)
    devices = i2c.scan()
    print(f"I2C bus {I2C_ID}: SDA=GPIO{SDA_PIN}, SCL=GPIO{SCL_PIN}, {I2C_FREQ//1000} kHz")
    print(f"Dispositivos I2C: {['0x%02X' % d for d in devices]}")

    if BMP_ADDR in devices:
        sensor = BMP180(i2c, addr=BMP_ADDR, oss=BMP_OSS)
        print(f"BMP180 detectado en 0x{BMP_ADDR:02X}")
        oss_names = ["Ultra Low", "Estándar", "Alto", "Ultra Alto"]
        print(f"Sobremuestreo: modo {BMP_OSS} ({oss_names[BMP_OSS]})")
    else:
        print(f"[ERROR] BMP180 no encontrado en 0x{BMP_ADDR:02X}")
        print("Verifica: SDA→GPIO21, SCL→GPIO22, VCC→3V3, GND→GND")

# ============================================================================
# Utilidades REPL
# ============================================================================
def poll_input(timeout_ms=100):
    """Lee entrada REPL sin bloquear (retorna cadena o None)."""
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
    """Verifica si el usuario presionó 'm' para regresar al menú."""
    line = poll_input(0)
    if line and line.lower() == 'm':
        print("\n[Menú] Regresando al menú principal...")
        return True
    return False

def wait_enter(msg="Presiona ENTER para continuar..."):
    """Espera hasta que el usuario presione ENTER."""
    print(msg, end="")
    if not MICROPYTHON:
        return
    while True:
        line = poll_input(200)
        if line is not None:
            break
        time.sleep_ms(100)

def menu_select(timeout_s=8):
    """Muestra menú principal y espera selección con timeout."""
    print("\n" + "=" * 56)
    print("  MENÚ PRINCIPAL — Práctica 4: BMP180 Altímetro")
    print("=" * 56)
    print("  1) Datos crudos + coeficientes de calibración")
    print("  2) Temperatura y presión compensadas")
    print("  3) Altímetro barométrico (m / ft)")
    print("  4) Monitor CSV continuo (para visualización)")
    print("  5) Comparativa de alturas")
    print("  6) Análisis de ruido y muestreo")
    print("  7) Filtro digital en vivo")
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

    # Mostrar coeficientes de calibración
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
    """Muestra T y P compensadas con pasos del algoritmo visibles."""
    print("\n--- MODO 2: Temperatura y Presión Compensadas ---")
    if sensor is None:
        print("[ERROR] Sensor no inicializado."); return

    print("Algoritmo de compensación (Bosch BMP180 datasheet):")
    print("  T: UT → X1,X2 → B5 → T = (B5+8)/16  [0.1°C]")
    print("  P: UP → B6,B3,B4,B7 → correcciones → P  [Pa]")
    print("\nPresiona 'm' + ENTER para menú.\n")

    # Mostrar primeros pasos detallados
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
    """Muestra altitud en metros y pies con ajuste QNH interactivo."""
    global SEA_LEVEL_PRESSURE
    print("\n--- MODO 3: Altímetro Barométrico ---")
    if sensor is None:
        print("[ERROR] Sensor no inicializado."); return

    print(f"  QNH actual: {SEA_LEVEL_PRESSURE:.0f} Pa ({SEA_LEVEL_PRESSURE/100:.2f} hPa)")
    print("  Fórmula: h = 44330 × (1 − (P/P₀)^(1/5.255))")
    print("\nComandos durante operación:")
    print("  'q' + ENTER  → Ajustar QNH (nueva presión de referencia)")
    print("  'm' + ENTER  → Regresar al menú")
    print()

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
                print("  Ingresa nueva presión a nivel del mar (hPa), ej: 1013.25")
                print("  O ingresa 'a' seguido de altitud conocida (m), ej: a540")
                print("  Ingreso: ", end="")
                while True:
                    val = poll_input(500)
                    if val:
                        try:
                            if val.startswith('a') or val.startswith('A'):
                                alt_known = float(val[1:])
                                SEA_LEVEL_PRESSURE = sensor.sea_level_pressure(alt_known)
                                print(f"\n  [QNH] Calculado desde altitud {alt_known:.0f} m: {SEA_LEVEL_PRESSURE:.0f} Pa ({SEA_LEVEL_PRESSURE/100:.2f} hPa)")
                            else:
                                SEA_LEVEL_PRESSURE = float(val) * 100.0
                                print(f"\n  [QNH] Establecido: {SEA_LEVEL_PRESSURE:.0f} Pa ({SEA_LEVEL_PRESSURE/100:.2f} hPa)")
                        except ValueError:
                            print("\n  [Error] Valor inválido.")
                        break
                    time.sleep_ms(100)
        time.sleep_ms(SAMPLE_RATE_MS)

# ============================================================================
# Modo 4: Monitor CSV continuo
# ============================================================================
def mode_csv_monitor():
    """Emite datos CSV para herramienta de visualización altimeter_gui.py."""
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
    """Medición guiada en diferentes alturas para comparar y validar altímetro."""
    global SEA_LEVEL_PRESSURE
    print("\n--- MODO 5: Comparativa de Alturas ---")
    if sensor is None:
        print("[ERROR] Sensor no inicializado."); return

    print("Este modo guiado te permite medir presión y altitud en")
    print("diferentes ubicaciones (pisos de un edificio, escaleras, etc.)")
    print("para verificar el funcionamiento del altímetro barométrico.\n")

    # Paso 1: Establecer referencia
    print("═══ Paso 1: Referencia QNH ═══")
    print(f"QNH actual: {SEA_LEVEL_PRESSURE/100:.2f} hPa")
    print("¿Conoces tu altitud actual? (ingresa metros, o ENTER para ISA)")
    print("Ingreso: ", end="")

    while True:
        val = poll_input(500)
        if val is not None:
            if val == '':
                print(f"\n  Usando ISA estándar: {SEA_LEVEL_PRESSURE/100:.2f} hPa")
            else:
                try:
                    alt_ref = float(val)
                    SEA_LEVEL_PRESSURE = sensor.sea_level_pressure(alt_ref)
                    print(f"\n  QNH calibrado desde {alt_ref:.0f} m: {SEA_LEVEL_PRESSURE/100:.2f} hPa")
                except ValueError:
                    print("\n  Usando ISA estándar.")
            break
        time.sleep_ms(100)

    # Paso 2: Mediciones
    measurements = []
    NUM_SAMPLES_PER_POINT = 10  # Promedio de 10 lecturas por punto

    print("\n═══ Paso 2: Mediciones ═══")
    print("En cada ubicación, se tomarán 10 lecturas y se promediarán.")
    print("Ingresa nombre del punto (ej: 'Planta baja', 'Piso 2'),")
    print("o 'fin' para terminar y ver resumen.\n")

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

        print(f"  Midiendo '{name}' ({NUM_SAMPLES_PER_POINT} muestras)...")
        temps = []; pressures = []; altitudes = []

        for i in range(NUM_SAMPLES_PER_POINT):
            T, P, h = sensor.read_all(p0=SEA_LEVEL_PRESSURE)
            temps.append(T)
            pressures.append(P / 100.0)
            altitudes.append(h)
            time.sleep_ms(200)

        avg_T = sum(temps) / len(temps)
        avg_P = sum(pressures) / len(pressures)
        avg_h = sum(altitudes) / len(altitudes)
        std_h = math.sqrt(sum((x - avg_h)**2 for x in altitudes) / len(altitudes))

        measurement = {
            'name': name, 'num': point_num,
            'T': avg_T, 'P': avg_P, 'h': avg_h, 'std_h': std_h
        }
        measurements.append(measurement)

        print(f"  ✓ {name}: T={avg_T:.1f}°C  P={avg_P:.2f} hPa  Alt={avg_h:.1f} m (±{std_h:.2f} m)")
        point_num += 1
        print()

    # Paso 3: Resumen
    if len(measurements) < 2:
        print("\n[Info] Se necesitan al menos 2 puntos para comparar.")
        return

    print("\n" + "=" * 60)
    print("  RESUMEN DE COMPARATIVA DE ALTURAS")
    print("=" * 60)
    print(f"  QNH de referencia: {SEA_LEVEL_PRESSURE/100:.2f} hPa")
    print(f"  Puntos medidos: {len(measurements)}")
    print()

    # Tabla de mediciones
    print("  ┌─────┬──────────────────┬────────┬──────────┬──────────┬────────────┐")
    print("  │ #   │ Ubicación        │ T (°C) │ P (hPa)  │ Alt (m)  │ σ (m)      │")
    print("  ├─────┼──────────────────┼────────┼──────────┼──────────┼────────────┤")
    for m in measurements:
        name_trunc = m['name'][:16].ljust(16)
        print(f"  │ {m['num']:>3d} │ {name_trunc} │ {m['T']:5.1f}  │ {m['P']:8.2f} │ {m['h']:8.1f} │ ±{m['std_h']:<9.3f} │")
    print("  └─────┴──────────────────┴────────┴──────────┴──────────┴────────────┘")

    # Diferencias entre puntos consecutivos
    print("\n  Diferencias de altura:")
    for i in range(1, len(measurements)):
        prev = measurements[i-1]
        curr = measurements[i]
        dh = curr['h'] - prev['h']
        dp = curr['P'] - prev['P']
        print(f"    {prev['name']} → {curr['name']}: Δh = {dh:+.1f} m  (ΔP = {dp:+.2f} hPa)")

    # Diferencia total
    total_dh = measurements[-1]['h'] - measurements[0]['h']
    print(f"\n  Diferencia total ({measurements[0]['name']} → {measurements[-1]['name']}): Δh = {total_dh:+.1f} m ({total_dh*3.28084:+.0f} ft)")

    # Factor de validación: ~8.43 m/hPa a nivel del mar
    print("\n  Referencia: ~8.43 m por cada hPa de diferencia a nivel del mar")
    print("  (La atmósfera estándar ISA indica ~1 hPa cada 8.43 m cerca del suelo)")

    wait_enter("\n  Presiona ENTER para volver al menú...")

# ============================================================================
# Modo 6: Análisis de ruido y muestreo
# ============================================================================
def _ask_int(prompt, default):
    """Pide un entero por REPL con valor por defecto (timeout largo)."""
    print(prompt + " [{}]: ".format(default), end="")
    if not MICROPYTHON:
        return default
    while True:
        v = poll_input(500)
        if v is not None:
            try:
                return int(v) if v.strip() else default
            except ValueError:
                return default
        time.sleep_ms(100)

def mode_noise_sampling():
    """
    Captura un bloque de N muestras de altitud a Fs fija y reporta la Fs real,
    el jitter de muestreo y la estadística de ruido (σ, RMS, resolución efectiva).
    Emite el bloque en CSV para analizarlo en la PC (espectro, Allan).
    """
    print("\n--- MODO 6: Análisis de Ruido y Muestreo ---")
    if sensor is None:
        print("[ERROR] Sensor no inicializado."); return
    if not HAVE_SIGLAB:
        print("[ERROR] Falta lib/siglab.py en la placa."); return

    # El BMP180 tarda ~8–26 ms por lectura (OSS): Fs práctica 5–30 Hz.
    oss_dt = [5, 8, 14, 26][sensor.oss]
    fs_max = int(1000 // (2 * oss_dt + 2))
    print("OSS={}  → cada lectura ~{} ms  → Fs máx ~{} Hz".format(sensor.oss, 2 * oss_dt + 2, fs_max))
    fs = _ask_int("Fs de muestreo (Hz)", min(5, fs_max))
    n = _ask_int("Número de muestras", 256)
    if fs > fs_max:
        print("[aviso] Fs solicitada > Fs máx; el firmware no la alcanzará (verás el error en el reporte).")

    print("\nCapturando {} muestras de altitud a {} Hz...".format(n, fs))
    read_alt = lambda: sensor.read_all(p0=SEA_LEVEL_PRESSURE)[2]
    res = BlockSampler(read_alt, fs, n).run()

    st = Stats()
    for x in res.samples:
        st.add(x)
    # Resolución vertical del BMP180 cerca del suelo: ~8.43 m por hPa,
    # 0.01 hPa de resolución → ~8.4 cm por LSB de presión.
    print("\n" + res.report())
    print("Estadística de altitud:")
    print("  " + st.report("m"))
    print("  resolución efectiva ≈ {:.2f} 'bits' sobre un rango de 100 m".format(
        st.effective_bits(100.0)))
    print("  (ruido de altitud dominado por el ruido de presión del ADC sigma-delta)")

    print("\n--- CSV del bloque (para la toolkit PC) ---")
    print("t_us,alt_m")
    for i in range(len(res.samples)):
        print("{},{:.3f}".format(res.t_us[i], res.samples[i]))
    print("# fin  fs_real={:.2f}  jitter_us={:.2f}".format(res.fs_actual, res.jitter_us))
    print("\nEn la PC:")
    print("  python -m sisela_signal spectrum     --file cap.csv --col alt_m --psd")
    print("  python -m sisela_signal characterize  --file cap.csv --col alt_m --mode allan")
    wait_enter("\nENTER para volver al menú...")

# ============================================================================
# Modo 7: Filtro digital en vivo
# ============================================================================
def mode_live_filter():
    """
    Aplica un filtro digital a la altitud en tiempo real y emite CSV con la
    señal cruda y la filtrada, para comparar en la PC (tiempo + espectro) y
    medir la respuesta al escalón (subir/bajar el sensor por unas escaleras).
    """
    print("\n--- MODO 7: Filtro Digital en Vivo ---")
    if sensor is None:
        print("[ERROR] Sensor no inicializado."); return
    if not HAVE_SIGLAB:
        print("[ERROR] Falta lib/siglab.py en la placa."); return

    print("Filtros: [1] media móvil N   [2] mediana N   [3] EMA (alpha)")
    kind = _ask_int("Elige filtro", 1)
    if kind == 3:
        a_pct = _ask_int("alpha × 100 (1–100)", 20)
        filt = Ema(max(1, min(100, a_pct)) / 100.0)
        label = "ema_a{:.2f}".format(max(1, min(100, a_pct)) / 100.0)
    else:
        nwin = _ask_int("N (ventana)", 8)
        filt = MovAvg(nwin) if kind != 2 else Median(nwin)
        label = ("movavg_n{}" if kind != 2 else "median_n{}").format(nwin)

    print("\nCSV: t_us,alt_raw,alt_filt   ({})".format(label))
    print("Mueve el sensor (escaleras) para ver la respuesta al escalón.")
    print("Presiona 'm' + ENTER para detener.\n")
    print("t_us,alt_raw,alt_filt")

    start = time.ticks_us() if MICROPYTHON else 0
    i = 0
    while True:
        raw = sensor.read_all(p0=SEA_LEVEL_PRESSURE)[2]
        y = filt.add(raw)
        t = time.ticks_diff(time.ticks_us(), start) if MICROPYTHON else i * 200000
        print("{},{:.3f},{:.3f}".format(t, raw, y))
        i += 1
        if check_menu_break():
            break
        time.sleep_ms(SAMPLE_RATE_MS)
    print("# fin n={}".format(i))
    print("\nEn la PC:")
    print("  python -m sisela_signal filter        --file cap.csv --col alt_raw --kind movavg --n 8")
    print("  python -m sisela_signal characterize   --file cap.csv --col alt_filt --mode step")

# ============================================================================
# Main
# ============================================================================
def main():
    print("\n" + "=" * 56)
    print("  Práctica 4 — BMP180 Altímetro Barométrico")
    print("  ESP32 + MicroPython")
    print("=" * 56)
    print(f"  I2C: SDA=GPIO{SDA_PIN}, SCL=GPIO{SCL_PIN}, {I2C_FREQ//1000} kHz")
    print(f"  Sensor: BMP180 @ 0x{BMP_ADDR:02X}, OSS={BMP_OSS}")
    print(f"  QNH: {SEA_LEVEL_PRESSURE/100:.2f} hPa ({SEA_LEVEL_PRESSURE:.0f} Pa)")
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
        elif choice == '6':
            mode_noise_sampling()
        elif choice == '7':
            mode_live_filter()
        elif choice.lower() == 'q':
            print("\n[Salida] Programa terminado.")
            break
        else:
            print(f"\n[Opción inválida] '{choice}' no reconocida.")

if __name__ == "__main__":
    main()
