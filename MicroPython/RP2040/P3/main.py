"""
Práctica 3 — Medición de Temperatura con NTC (RP2040 + MicroPython)

Funciones clave:
  - Lectura ADC en GP26 (ADC0) de un divisor resistivo: 3V3 -> R_SERIE -> nodo -> NTC -> GND.
  - Cálculo de V(nodo), R_NTC y T(°C) mediante la ecuación Beta.
  - Modos elegibles por REPL: 1) ADC crudo, 2) Resistencia, 3) Temperatura, 4) Monitor integrado (CSV).
  - Tecla 'm' + ENTER para volver al menú.

Diferencias RP2040 vs ESP32:
  - ADC: GP26-GP28 (3 canales) vs GPIO32-39 (18 canales)
  - Función: adc.read_u16() (0-65535) vs adc.read() (0-4095)
  - Sin atenuación/width: RP2040 siempre 12-bit con padding a 16-bit
  - Voltaje máximo: 3.3V estricto (sin protección como en ESP32)

Advertencias:
  - RP2040 ADC solo acepta 0-3.3V (sin protección de sobrevoltaje).
  - GP26-GP28 son los únicos pines ADC disponibles.
"""

import sys

try:
    from machine import Pin, ADC
except ImportError:  # análisis fuera de la placa
    Pin = object  # type: ignore
    ADC = object  # type: ignore

try:
    import utime as time
except ImportError:
    import time

try:
    import uselect
except ImportError:
    uselect = None  # type: ignore
try:
    import ujson as json
except ImportError:
    try:
        import json  # type: ignore
    except Exception:
        json = None  # type: ignore
try:
    import os
except Exception:
    os = None  # type: ignore

# Polyfills mínimos para análisis fuera de la placa
if not hasattr(time, "sleep_ms"):
    def _sleep_ms(ms):
        time.sleep(ms/1000.0)
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
# Configuración — parámetros
# ==========================

# Pines
ADC_PIN = 26  # GP26 (ADC0) — RP2040 usa número directo, no Pin()

# ADC (RP2040: siempre 12-bit con padding a 16-bit)
ADC_MAX = 65535  # read_u16() devuelve 0-65535
SAMPLES = 16     # promedio simple por lectura

# Divisor y NTC
V_SUPPLY = 3.3     # V de alimentación del divisor
R_SERIES = 10000.0 # ohmios (10k)
NTC_R0 = 10000.0   # ohmios @ T0
NTC_BETA = 3950.0  # beta típica
T0_K = 273.15 + 25.0

# Loop
LOOP_HZ = 10
PRINT_EVERY = 1

# Calibración (opcional): deshabilitada por defecto
CAL_FILE = "calibration.json"
AUTO_USE_CALIBRATION = False  # deja False por defecto
_cal = {"low": 0, "high": ADC_MAX, "enabled": False}

# ==========================
# Inicialización de HW
# ==========================

def _init_adc(pin_no=ADC_PIN):
    """Inicializa ADC en RP2040.
    
    Diferencia clave: RP2040 usa ADC(pin_number) directamente,
    sin necesidad de Pin() wrapper ni configuración de atenuación/width.
    """
    adc_obj = ADC(pin_no)  # GP26 = ADC(26), GP27 = ADC(27), GP28 = ADC(28)
    return adc_obj

adc = None
try:
    adc = _init_adc()
except Exception as e:
    print("[WARN] ADC no inicializado en escritorio: {}".format(e))


# ==========================
# Calibración ADC (opcional)
# ==========================

def load_calibration():
    global _cal
    if json is None:
        return
    try:
        if os and hasattr(os, "stat"):
            _ = os.stat(CAL_FILE)
        with open(CAL_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, dict) and "low" in data and "high" in data:
                _cal.update({
                    "low": int(data.get("low", 0)),
                    "high": int(data.get("high", ADC_MAX)),
                    "enabled": bool(data.get("enabled", False)),
                })
                print("[CAL] Archivo de calibración cargado: low={}, high={}, enabled={}".format(
                    _cal["low"], _cal["high"], _cal["enabled"]))
    except Exception as e:
        print("[CAL] No se pudo cargar calibración: {}".format(e))


def save_calibration():
    if json is None:
        print("[CAL] JSON no disponible; no se puede guardar.")
        return False
    try:
        with open(CAL_FILE, "w") as f:
            json.dump(_cal, f)
        print("[CAL] Guardado en {}".format(CAL_FILE))
        return True
    except Exception as e:
        print("[CAL] Error guardando calibración: {}".format(e))
        return False

# ==========================
# Utilidades
# ==========================

def _poll():
    if uselect is None:
        return None
    try:
        p = uselect.poll()
        p.register(sys.stdin, uselect.POLLIN)
        return p
    except Exception:
        return None


def _readline_timeout(ms=0, p=None):
    if uselect is None:
        return None
    p = p or _poll()
    if p is None:
        return None
    res = p.poll(ms)
    if res:
        try:
            s = sys.stdin.readline()
            return s.strip() if s else None
        except Exception:
            return None
    return None


def adc_read_avg(adc_obj, nsamples=SAMPLES):
    """Lee ADC múltiples veces y promedia.
    
    RP2040: usa read_u16() en lugar de read().
    """
    if adc_obj is None:
        return 0
    s = 0
    for _ in range(max(1, int(nsamples))):
        s += adc_obj.read_u16()  # RP2040: read_u16() devuelve 0-65535
    return s // max(1, int(nsamples))


def adc_to_voltage(adc_val, adc_max=ADC_MAX, v_full=V_SUPPLY):
    """Convierte valor ADC a voltaje.
    
    RP2040: adc_max = 65535 (16-bit)
    ESP32:  adc_max = 4095 (12-bit)
    """
    # Si hay calibración y está activa, usar mapa [low..high] → [0..v_full]
    if AUTO_USE_CALIBRATION and _cal and (_cal.get("high", 0) > _cal.get("low", 0)):
        span = float(_cal["high"] - _cal["low"]) or 1.0
        ratio = (adc_val - _cal["low"]) / span
        if ratio < 0:
            ratio = 0.0
        if ratio > 1:
            ratio = 1.0
        return ratio * v_full
    # Aproximación estándar: 0..adc_max → 0..v_full
    return (adc_val / adc_max) * v_full


def voltage_to_ntc_res(v_node, vcc=V_SUPPLY, r_series=R_SERIES):
    """Calcula resistencia de NTC desde voltaje de nodo.
    
    Divisor: Vnode = Vcc * Rntc / (Rseries + Rntc)
    Despeje: Rntc = Rseries * Vnode / (Vcc - Vnode)
    """
    eps = 1e-9
    denom = max(eps, (vcc - v_node))
    return r_series * (v_node / denom)


def ntc_res_to_temp_c(r_ntc, r0=NTC_R0, beta=NTC_BETA, t0=T0_K):
    """Convierte resistencia de NTC a temperatura en °C usando ecuación Beta.
    
    Ecuación: 1/T = 1/T0 + (1/Beta)*ln(R/R0)
    """
    import math
    r = max(1e-3, r_ntc)
    invT = (1.0 / t0) + (1.0 / beta) * math.log(r / r0)
    T = 1.0 / invT
    return T - 273.15


# ==========================
# Modos
# ==========================

def mode_adc_raw(period_s=0.2):
    """Modo 1: Muestra valor ADC crudo y voltaje de nodo."""
    print("[Modo 1] ADC crudo + V(nodo)")
    p = _poll()
    while True:
        if _readline_timeout(0, p) in ("m", "menu", "q", "exit"):
            print("Volviendo al menú…")
            return
        val = adc_read_avg(adc)
        v = adc_to_voltage(val)
        print("adc={}, V={:.3f}".format(val, v))
        time.sleep_ms(int(period_s*1000))


def mode_resistance(period_s=0.2):
    """Modo 2: Muestra resistencia estimada de la NTC."""
    print("[Modo 2] Resistencia NTC estimada")
    p = _poll()
    while True:
        if _readline_timeout(0, p) in ("m", "menu", "q", "exit"):
            print("Volviendo al menú…")
            return
        val = adc_read_avg(adc)
        v = adc_to_voltage(val)
        r = voltage_to_ntc_res(v)
        print("adc={}, V={:.3f}, Rntc={:.1f}Ω".format(val, v, r))
        time.sleep_ms(int(period_s*1000))


def mode_temperature(period_s=0.5):
    """Modo 3: Muestra temperatura calculada en °C."""
    print("[Modo 3] Temperatura (°C) — Beta={:.0f}, R0={:.0f}Ω".format(NTC_BETA, NTC_R0))
    p = _poll()
    while True:
        if _readline_timeout(0, p) in ("m", "menu", "q", "exit"):
            print("Volviendo al menú…")
            return
        val = adc_read_avg(adc)
        v = adc_to_voltage(val)
        r = voltage_to_ntc_res(v)
        t = ntc_res_to_temp_c(r)
        print("V={:.3f}V, Rntc={:.0f}Ω, T={:.2f}°C".format(v, r, t))
        time.sleep_ms(int(period_s*1000))


def mode_monitor_csv(period_s=0.2):
    """Modo 4: Monitor CSV para graficar datos."""
    print("t_ms,adc,v_node_v,r_ntc_ohm,t_c")
    t0 = time.ticks_ms()
    p = _poll()
    while True:
        if _readline_timeout(0, p) in ("m", "menu", "q", "exit"):
            print("\nVolviendo al menú…")
            return
        t = time.ticks_diff(time.ticks_ms(), t0)
        val = adc_read_avg(adc)
        v = adc_to_voltage(val)
        r = voltage_to_ntc_res(v)
        tc = ntc_res_to_temp_c(r)
        print("{},{},{:.4f},{:.1f},{:.2f}".format(t, val, v, r, tc))
        time.sleep_ms(int(period_s*1000))


def mode_calibration_wizard():
    """Modo 5: Guía interactiva para calibrar el ADC (offset/ganancia).

    Procedimiento:
      1) Conecta el nodo (GP26) a GND. Escribe 'ok' + ENTER.
      2) Conecta el nodo (GP26) a 3V3. Escribe 'ok' + ENTER.
    Se guardarán los valores como low/high en calibration.json.
    
    Nota: La calibración NO se aplica automáticamente a menos que
    pongas AUTO_USE_CALIBRATION=True.
    """
    print("\n=== Calibración ADC — guía ===")
    print("Este asistente mide extremos para mapear 0V y 3.3V.")
    print("Paso 1) Une el nodo (GP26) a GND. Luego escribe 'ok' + ENTER.")
    p = _poll()
    # Espera confirmación 'ok'
    while True:
        s = _readline_timeout(200, p)
        if s and s.strip().lower() in ("ok", "ok."):
            break
    # Mide LOW
    low = 0
    NS = 64
    for _ in range(NS):
        low += adc_read_avg(adc)
        time.sleep_ms(5)
    low //= NS
    print("Leído LOW (GND): {}".format(low))

    print("Paso 2) Une el nodo (GP26) a 3V3. Luego escribe 'ok' + ENTER.")
    while True:
        s = _readline_timeout(200, p)
        if s and s.strip().lower() in ("ok", "ok."):
            break
    # Mide HIGH
    high = 0
    for _ in range(NS):
        high += adc_read_avg(adc)
        time.sleep_ms(5)
    high //= NS
    print("Leído HIGH (3V3): {}".format(high))

    if high <= low:
        print("[CAL] Valores inválidos (high<=low). Repite el proceso.")
        return

    _cal.update({"low": int(low), "high": int(high), "enabled": True})
    if save_calibration():
        print("[CAL] Guardado. Para usarla, edita AUTO_USE_CALIBRATION=True en main.py.")
    else:
        print("[CAL] No se pudo guardar. Puedes copiar estos valores manualmente:")
        print("low={}, high={}".format(low, high))


# ==========================
# Menú
# ==========================

def menu_select(timeout_s=6):
    print("\n=== P3 · NTC (RP2040) — elige modo y ENTER ===")
    print("1) ADC crudo")
    print("2) Resistencia NTC")
    print("3) Temperatura (°C)")
    print("4) Monitor CSV (t,adc,V,R,T)")
    print("5) Calibración ADC (guía)")
    print("(Por defecto en {}s: 3)".format(timeout_s))
    p = _poll()
    # Limpieza de buffer inicial
    _ = _readline_timeout(10, p)
    for _ in range(timeout_s):
        s = _readline_timeout(1000, p)
        if s and s in ("1","2","3","4","5"):
            return int(s)
    return 3


def main():
    print("[main][P3] Listo. Escribe 'm' + ENTER para volver al menú desde cualquier modo.")
    while True:
        sel = menu_select()
        if sel == 1:
            mode_adc_raw()
        elif sel == 2:
            mode_resistance()
        elif sel == 3:
            mode_temperature()
        elif sel == 4:
            mode_monitor_csv()
        else:
            mode_calibration_wizard()


if __name__ == "__main__":
    # Intenta cargar calibración (se aplicará SOLO si AUTO_USE_CALIBRATION=True)
    load_calibration()
    main()
