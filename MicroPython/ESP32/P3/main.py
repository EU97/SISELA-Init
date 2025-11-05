"""
Práctica 3 — Medición de Temperatura (ESP32 + MicroPython)

Menú para elegir sensor: NTC (termistor) o LM35, con modos normales y CSV.

Funciones clave:
    - NTC: divisor resistivo 3V3 -> R_SERIE -> nodo -> NTC -> GND, ecuación Beta para °C
    - LM35: sensor lineal 10mV/°C, conversión directa V*100 → °C
    - Menús por REPL: selección de sensor y modos por sensor
    - Tecla 'm' + ENTER: volver al menú de modos del sensor actual; CTRL+C reinicia / rerun para cambiar de sensor

Advertencias:
    - Usa pines ADC apropiados (32–39). GPIO34 es entrada‑solo.
    - La atenuación 11dB apunta a ~3.3V full scale; considera no linealidades del ADC de ESP32.
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
ADC_PIN = 34  # GPIO34 (ADC1), entrada‑solo

# ADC
ADC_ATTEN = 3  # ADC.ATTN_11DB
ADC_WIDTH = 3  # ADC.WIDTH_12BIT
SAMPLES = 16   # promedio simple por lectura

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
AUTO_USE_CALIBRATION = False  # deja False por defecto como solicitaste
_cal = {"low": 0, "high": (1 << 12) - 1, "enabled": False}

# LM35: 10mV/°C (0.01 V/°C) → Temp(°C) = Volt(V) * 100
def lm35_voltage_to_temp_c(v):
    try:
        return float(v) * 100.0
    except Exception:
        return 0.0

# ==========================
# Inicialización de HW
# ==========================

def _init_adc(pin_no=ADC_PIN):
    adc_obj = ADC(Pin(pin_no))
    try:
        adc_obj.atten(ADC.ATTN_11DB)
    except Exception:
        # Algunos ports usan entero 3
        adc_obj.atten(ADC_ATTEN)
    try:
        adc_obj.width(ADC.WIDTH_12BIT)
    except Exception:
        adc_obj.width(ADC_WIDTH)
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
            # Verifica existencia simple
            # Si no existe, os.stat lanzará excepción
            _ = os.stat(CAL_FILE)
        with open(CAL_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, dict) and "low" in data and "high" in data:
                _cal.update({
                    "low": int(data.get("low", 0)),
                    "high": int(data.get("high", (1 << 12) - 1)),
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
    if adc_obj is None:
        return 0
    s = 0
    for _ in range(max(1, int(nsamples))):
        s += adc_obj.read()
    return s // max(1, int(nsamples))


def adc_to_voltage(adc_val, width_bits=12, v_full=V_SUPPLY):
    # Si hay calibración y está activa, usar mapa [low..high] → [0..v_full]
    if AUTO_USE_CALIBRATION and _cal and (_cal.get("high", 0) > _cal.get("low", 0)):
        span = float(_cal["high"] - _cal["low"]) or 1.0
        ratio = (adc_val - _cal["low"]) / span
        if ratio < 0:
            ratio = 0.0
        if ratio > 1:
            ratio = 1.0
        return ratio * v_full
    # Aproximación estándar: 0..(2^width-1) → 0..v_full
    maxcount = (1 << width_bits) - 1
    return (adc_val / maxcount) * v_full


def voltage_to_ntc_res(v_node, vcc=V_SUPPLY, r_series=R_SERIES):
    # Vnode = Vcc * Rntc / (Rseries + Rntc)  =>  Rntc = Rseries * Vnode / (Vcc - Vnode)
    eps = 1e-9
    denom = max(eps, (vcc - v_node))
    return r_series * (v_node / denom)


def ntc_res_to_temp_c(r_ntc, r0=NTC_R0, beta=NTC_BETA, t0=T0_K):
    # 1/T = 1/T0 + (1/B)*ln(R/R0)
    import math
    r = max(1e-3, r_ntc)
    invT = (1.0 / t0) + (1.0 / beta) * math.log(r / r0)
    T = 1.0 / invT
    return T - 273.15


# ==========================
# Modos
# ==========================

def mode_adc_raw(period_s=0.2):
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


# ==========================
# Modos LM35
# ==========================

def mode_lm35_temperature(period_s=0.5):
    print("[LM35] Temperatura (°C) — 10mV/°C (V*100)")
    p = _poll()
    while True:
        if _readline_timeout(0, p) in ("m", "menu", "q", "exit"):
            print("Volviendo al menú…")
            return
        val = adc_read_avg(adc)
        v = adc_to_voltage(val)
        t = lm35_voltage_to_temp_c(v)
        print("V={:.3f}V, T={:.2f}°C".format(v, t))
        time.sleep_ms(int(period_s*1000))


def mode_calibration_wizard():
    """Guía interactiva para calibrar el ADC (offset/ganancia).

    Procedimiento:
      1) Conecta el nodo (GPIO34) a GND. Escribe 'ok' + ENTER.
      2) Conecta el nodo (GPIO34) a 3V3. Escribe 'ok' + ENTER.
    Se guardarán los valores como low/high en calibration.json.
    Nota: La calibración NO se aplica automáticamente a menos que
    pongas AUTO_USE_CALIBRATION=True.
    """
    print("\n=== Calibración ADC — guía ===")
    print("Este asistente mide extremos para mapear 0V y 3.3V.")
    print("Paso 1) Une el nodo (GPIO34) a GND. Luego escribe 'ok' + ENTER.")
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

    print("Paso 2) Une el nodo (GPIO34) a 3V3. Luego escribe 'ok' + ENTER.")
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

def menu_select_ntc(timeout_s=6):
    print("\n=== P3 · NTC — elige modo y ENTER ===")
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


def menu_select_lm35(timeout_s=6):
    print("\n=== P3 · LM35 — elige modo y ENTER ===")
    print("1) ADC crudo")
    print("2) Temperatura (°C)")
    print("3) Monitor CSV (t,adc,V,T)")
    print("(Por defecto en {}s: 2)".format(timeout_s))
    p = _poll()
    _ = _readline_timeout(10, p)
    for _ in range(timeout_s):
        s = _readline_timeout(1000, p)
        if s and s in ("1","2","3"):
            return int(s)
    return 2


def menu_select_sensor(timeout_s=5):
    print("\n=== P3 · Selecciona sensor ===")
    print("1) NTC (termistor)")
    print("2) LM35 (10mV/°C)")
    print("(Por defecto en {}s: 1)".format(timeout_s))
    p = _poll()
    _ = _readline_timeout(10, p)
    for _ in range(timeout_s):
        s = _readline_timeout(1000, p)
        if s and s in ("1","2"):
            return int(s)
    return 1


def main():
    print("[main][P3] Listo. Selecciona sensor y modo. 'm' vuelve al menú actual.")
    while True:
        sensor = menu_select_sensor()
        if sensor == 1:  # NTC
            while True:
                sel = menu_select_ntc()
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
                # Al salir de un modo con 'm', regresa a menú NTC
        else:  # LM35
            while True:
                sel = menu_select_lm35()
                if sel == 1:
                    mode_adc_raw()
                elif sel == 2:
                    mode_lm35_temperature()
                else:
                    # sel == 3: CSV
                    t0 = time.ticks_ms()
                    print("t_ms,adc,v_node_v,t_c")
                    p = _poll()
                    while True:
                        if _readline_timeout(0, p) in ("m", "menu", "q", "exit"):
                            print("\nVolviendo al menú…")
                            break
                        t = time.ticks_diff(time.ticks_ms(), t0)
                        val = adc_read_avg(adc)
                        v = adc_to_voltage(val)
                        tc = lm35_voltage_to_temp_c(v)
                        print("{},{},{:.4f},{:.2f}".format(t, val, v, tc))
                        time.sleep_ms(int(0.2*1000))
                # Al salir de un modo con 'm', regresa a menú LM35


if __name__ == "__main__":
    # Intenta cargar calibración (se aplicará SOLO si AUTO_USE_CALIBRATION=True)
    load_calibration()
    main()
