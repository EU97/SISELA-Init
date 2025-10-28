"""
Práctica 4 — MPX5500DP Pressure Sensor (ESP32 + MicroPython)
main.py: Lectura ADC de sensor de presión y conversión a kPa con calibración opcional

MPX5500DP: Sensor piezoresistivo de presión absoluta 20–520 kPa
Transfer function: Vout = VS × (0.2 × P + 0.2)  donde P en kPa, VS=5V nominal
Para VS=3.3V: Vout(kPa) = 3.3 × (0.2 × P + 0.2) = 0.66 + 0.0013P
Rango de salida: ~0.66V (20 kPa) a 4.0V (520 kPa) @ VS=3.3V

ATENCIÓN: MPX5500DP funciona con VS=4.75–5.25V. Con VS=3.3V la sensibilidad
disminuye pero el sensor sigue operativo. Para máxima precisión usa 5V con
divisor de voltaje para el ADC (ej: 10kΩ + 10kΩ) o buffer de 3.3V.
"""

# ============================================================================
# Imports & Polyfills
# ============================================================================
try:
    from machine import ADC, Pin
    import utime as time
    import uselect
    import ujson as json
    import sys
    MICROPYTHON = True
except ImportError:
    # Polyfills para análisis fuera de la placa
    print("[PC Mode] Usando polyfills para análisis estático.")
    MICROPYTHON = False
    
    class ADC:
        ATTN_11DB = 3
        WIDTH_12BIT = 12
        def __init__(self, pin): pass
        def atten(self, val): pass
        def width(self, val): pass
        def read(self): return 2048
    
    class Pin:
        IN = 1
        OUT = 2
        PULL_UP = 3
        def __init__(self, pin, mode=None, pull=None): pass
        def value(self, val=None): return 0
    
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
        def poll(): return _FakePoll()
    
    class _FakePoll:
        def register(self, stream, mode): pass
        def poll(self, timeout): return []
    
    import json
    import sys

import math

# ============================================================================
# Configuración de hardware
# ============================================================================
ADC_PIN = 34               # GPIO34 (ADC1_CH6, input-only)
ADC_SAMPLES = 50           # Promedio de lecturas ADC
SAMPLE_RATE_MS = 100       # Periodo de muestreo en modos continuos (100ms → 10 Hz)

# Parámetros del sensor MPX5500DP
V_SUPPLY = 3.3             # Voltaje de alimentación del sensor (V)
P_MIN = 20.0               # Presión mínima del sensor (kPa)
P_MAX = 520.0              # Presión máxima del sensor (kPa)
VOUT_MIN_IDEAL = V_SUPPLY * 0.2  # Salida a 0 kPa (ideal): 0.66V @ 3.3V
VOUT_MAX_IDEAL = V_SUPPLY * 1.0  # Salida a 500 kPa (ideal): 3.3V @ 3.3V

# Transfer function inversa: P = (Vout/VS - 0.2) / 0.2 * (escala) + offset
# Simplificado: P(kPa) = (Vout - VOUT_MIN_IDEAL) / SENSITIVITY + P_MIN
SENSITIVITY = (VOUT_MAX_IDEAL - VOUT_MIN_IDEAL) / (P_MAX - P_MIN)  # V/kPa

# Calibración ADC (opcional, deshabilitado por defecto)
AUTO_USE_CALIBRATION = False
CALIBRATION_FILE = "calibration.json"

# ============================================================================
# Inicialización de hardware
# ============================================================================
if MICROPYTHON:
    adc = ADC(Pin(ADC_PIN))
    adc.atten(ADC.ATTN_11DB)   # 0–3.3V (aprox. 0–4095)
    adc.width(ADC.WIDTH_12BIT) # 12 bits
    print(f"ADC inicializado en GPIO{ADC_PIN} (ATTN_11DB, 12bit)")

# ============================================================================
# Utilidades de calibración (opcional)
# ============================================================================
def load_calibration():
    """Carga parámetros de calibración desde JSON."""
    try:
        with open(CALIBRATION_FILE, "r") as f:
            data = json.load(f)
        print(f"[Calibración] Datos cargados: {data}")
        return data
    except:
        print("[Calibración] Archivo no encontrado o inválido, usando valores por defecto.")
        return None

def save_calibration(data):
    """Guarda parámetros de calibración a JSON."""
    try:
        with open(CALIBRATION_FILE, "w") as f:
            json.dump(data, f)
        print(f"[Calibración] Guardado en '{CALIBRATION_FILE}': {data}")
    except Exception as e:
        print(f"[Error] No se pudo guardar calibración: {e}")

def adc_to_voltage(raw, calib=None):
    """
    Convierte lectura ADC cruda a voltaje (V).
    Si calib es un dict con 'adc_low', 'adc_high', aplica mapeo lineal.
    """
    if calib and 'adc_low' in calib and 'adc_high' in calib:
        adc_low = calib['adc_low']
        adc_high = calib['adc_high']
        # Mapeo: 0V → adc_low, 3.3V → adc_high
        if adc_high == adc_low:
            print("[Advertencia] Calibración inválida (mismo valor low/high), usando fórmula estándar.")
            return (raw / 4095.0) * 3.3
        voltage = ((raw - adc_low) / (adc_high - adc_low)) * 3.3
        return max(0.0, min(3.3, voltage))  # clamp
    else:
        # Sin calibración: lineal estándar
        return (raw / 4095.0) * 3.3

# ============================================================================
# Lectura de ADC
# ============================================================================
def read_adc_avg(n=ADC_SAMPLES):
    """Lee n muestras del ADC y devuelve el promedio."""
    if not MICROPYTHON:
        return 2048
    total = 0
    for _ in range(n):
        total += adc.read()
        time.sleep_ms(1)
    return total // n

# ============================================================================
# Conversión de voltaje a presión
# ============================================================================
def voltage_to_pressure_kpa(voltage):
    """
    Convierte voltaje del sensor a presión (kPa) usando transfer function.
    P(kPa) = (Vout - Vmin) / sensitivity + Pmin
    """
    if voltage < VOUT_MIN_IDEAL:
        # Fuera de rango bajo
        return P_MIN
    if voltage > VOUT_MAX_IDEAL:
        # Fuera de rango alto (saturado)
        return P_MAX
    
    pressure = ((voltage - VOUT_MIN_IDEAL) / SENSITIVITY) + P_MIN
    return pressure

# ============================================================================
# Menú interactivo con timeout
# ============================================================================
def menu_select(timeout_s=6):
    """
    Muestra menú de modos y espera selección del usuario con timeout.
    Retorna opción (str) o None si timeout.
    """
    print("\n" + "="*50)
    print("MENÚ PRINCIPAL — Práctica 4: MPX5500DP")
    print("="*50)
    print("1) Lectura ADC cruda")
    print("2) Voltaje del sensor (V)")
    print("3) Presión (kPa)")
    print("4) Monitor CSV continuo (para visualización)")
    print("5) Asistente de calibración ADC (opcional)")
    print("q) Salir")
    print("="*50)
    print(f"Selecciona opción (timeout: {timeout_s}s): ", end="")
    
    if not MICROPYTHON:
        return "1"  # Default en modo PC
    
    poll = uselect.poll()
    poll.register(sys.stdin, uselect.POLLIN)
    start = time.ticks_ms()
    
    while True:
        elapsed = time.ticks_diff(time.ticks_ms(), start) / 1000.0
        if elapsed >= timeout_s:
            print("\n[Timeout] Reintentando menú...")
            return None
        
        events = poll.poll(100)
        if events:
            line = sys.stdin.readline().strip()
            if line:
                return line
        time.sleep_ms(50)

def check_menu_break():
    """
    Verifica si el usuario escribió 'm' para regresar al menú.
    Retorna True si detecta 'm', False en caso contrario.
    """
    if not MICROPYTHON:
        return False
    
    poll = uselect.poll()
    poll.register(sys.stdin, uselect.POLLIN)
    events = poll.poll(0)  # No bloqueante
    
    if events:
        line = sys.stdin.readline().strip().lower()
        if line == 'm':
            print("\n[Menú] Regresando al menú principal...")
            return True
    return False

# ============================================================================
# Modos de operación
# ============================================================================
def mode_raw_adc():
    """Modo 1: Lectura ADC cruda continua."""
    print("\n--- MODO 1: Lectura ADC cruda ---")
    print("Presiona 'm' + ENTER para regresar al menú.\n")
    
    while True:
        raw = read_adc_avg()
        print(f"ADC: {raw:4d}")
        
        if check_menu_break():
            break
        time.sleep_ms(SAMPLE_RATE_MS)

def mode_voltage():
    """Modo 2: Voltaje del sensor (V)."""
    print("\n--- MODO 2: Voltaje del sensor ---")
    print("Presiona 'm' + ENTER para regresar al menú.\n")
    
    calib = None
    if AUTO_USE_CALIBRATION:
        calib = load_calibration()
    
    while True:
        raw = read_adc_avg()
        voltage = adc_to_voltage(raw, calib)
        print(f"Voltaje: {voltage:.3f} V  (ADC: {raw})")
        
        if check_menu_break():
            break
        time.sleep_ms(SAMPLE_RATE_MS)

def mode_pressure():
    """Modo 3: Presión en kPa."""
    print("\n--- MODO 3: Presión (kPa) ---")
    print("Presiona 'm' + ENTER para regresar al menú.\n")
    
    calib = None
    if AUTO_USE_CALIBRATION:
        calib = load_calibration()
    
    while True:
        raw = read_adc_avg()
        voltage = adc_to_voltage(raw, calib)
        pressure = voltage_to_pressure_kpa(voltage)
        print(f"Presión: {pressure:.2f} kPa  (V: {voltage:.3f}, ADC: {raw})")
        
        if check_menu_break():
            break
        time.sleep_ms(SAMPLE_RATE_MS)

def mode_csv_monitor():
    """Modo 4: Monitor CSV continuo para visualización externa."""
    print("\n--- MODO 4: Monitor CSV continuo ---")
    print("Formato: timestamp_ms,adc_raw,voltage_V,pressure_kPa")
    print("Presiona 'm' + ENTER para detener.\n")
    
    calib = None
    if AUTO_USE_CALIBRATION:
        calib = load_calibration()
    
    # Header CSV
    print("timestamp_ms,adc_raw,voltage_V,pressure_kPa")
    
    start_t = time.ticks_ms()
    while True:
        t = time.ticks_diff(time.ticks_ms(), start_t)
        raw = read_adc_avg()
        voltage = adc_to_voltage(raw, calib)
        pressure = voltage_to_pressure_kpa(voltage)
        
        print(f"{t},{raw},{voltage:.3f},{pressure:.2f}")
        
        if check_menu_break():
            break
        time.sleep_ms(SAMPLE_RATE_MS)

def mode_calibration_wizard():
    """
    Modo 5: Asistente de calibración ADC (opcional).
    Guía al usuario para medir GND y 3.3V, guarda parámetros.
    """
    print("\n" + "="*60)
    print("ASISTENTE DE CALIBRACIÓN ADC")
    print("="*60)
    print("Este asistente corrige offsets lineales del ADC mediante")
    print("dos puntos de referencia: GND (0V) y 3.3V.")
    print("NOTA: La calibración mejora offset/ganancia pero NO corrige")
    print("la no linealidad completa del ADC ESP32.")
    print("="*60)
    
    input("\n1) Conecta GPIO34 a GND, presiona ENTER...")
    time.sleep_ms(500)
    adc_low = read_adc_avg(100)
    print(f"   ADC @ GND: {adc_low}")
    
    input("\n2) Conecta GPIO34 a 3V3, presiona ENTER...")
    time.sleep_ms(500)
    adc_high = read_adc_avg(100)
    print(f"   ADC @ 3V3: {adc_high}")
    
    if adc_high <= adc_low:
        print("\n[Error] ADC high <= ADC low. Verifica conexiones.")
        return
    
    calib_data = {
        "adc_low": adc_low,
        "adc_high": adc_high,
        "v_low": 0.0,
        "v_high": 3.3,
        "timestamp": time.ticks_ms()
    }
    
    save_calibration(calib_data)
    print("\n[Calibración completa] Datos guardados.")
    print("Para usar automáticamente, cambia AUTO_USE_CALIBRATION = True en main.py")
    input("\nPresiona ENTER para regresar al menú...")

# ============================================================================
# Main loop
# ============================================================================
def main():
    """Bucle principal con menú interactivo."""
    print("\n" + "="*60)
    print("Práctica 4 — MPX5500DP Pressure Sensor")
    print("ESP32 + MicroPython")
    print("="*60)
    print(f"ADC: GPIO{ADC_PIN}, 12bit, ATTN_11DB (0-3.3V)")
    print(f"Sensor: MPX5500DP (20-520 kPa, VS={V_SUPPLY}V)")
    print(f"Calibración ADC: {'ACTIVA' if AUTO_USE_CALIBRATION else 'DESACTIVADA'}")
    print("="*60)
    
    while True:
        choice = menu_select(timeout_s=6)
        
        if choice is None:
            continue
        
        if choice == '1':
            mode_raw_adc()
        elif choice == '2':
            mode_voltage()
        elif choice == '3':
            mode_pressure()
        elif choice == '4':
            mode_csv_monitor()
        elif choice == '5':
            mode_calibration_wizard()
        elif choice.lower() == 'q':
            print("\n[Salida] Programa terminado.")
            break
        else:
            print(f"\n[Opción inválida] '{choice}' no reconocida. Intenta de nuevo.")

if __name__ == "__main__":
    main()
