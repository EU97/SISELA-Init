# main.py — plantilla base para prácticas ESP32 + MicroPython
# Estructura: parámetros, configuración HW, utilidades, clases, loop principal.

from time import ticks_ms, ticks_diff, sleep_ms

# -------- Parámetros (ajusta para tu práctica) --------
LOOP_HZ = 10        # Frecuencia de iteración del loop principal
PRINT_EVERY = 1     # Imprime cada N iteraciones (para no saturar)

# (Opcional) Calibración ADC — patrón sugerido
# AUTO_USE_CALIBRATION = False  # Si True, usa low/high de calibration.json para mapear adc→voltaje
# CAL_FILE = "calibration.json"
# Nota: Implementa un modo 5 (wizard) que mida low (GND) y high (3V3) y guarde el archivo.

# Ejemplos de pines (cámbialos en cada práctica)
# from machine import Pin, ADC, PWM, I2C, UART
# PIN_LED = 2
# ADC_PIN = 34

# -------- Configuración HW (inicializa periféricos aquí) --------
# led = Pin(PIN_LED, Pin.OUT)
# adc = ADC(Pin(ADC_PIN)); adc.atten(ADC.ATTN_11DB); adc.width(ADC.WIDTH_12BIT)

# -------- Utilidades --------

def now_ms() -> int:
    return ticks_ms()

# (Opcional) Funciones de calibración ADC
# Descomenta y ajusta si habilitas AUTO_USE_CALIBRATION

# try:
#     import ujson as json
# except ImportError:
#     try:
#         import json
#     except Exception:
#         json = None
# try:
#     import os
# except Exception:
#     os = None
#
# _cal = {"low": 0, "high": (1 << 12) - 1, "enabled": False}
#
# def load_calibration():
#     global _cal
#     if json is None:
#         return
#     try:
#         if os and hasattr(os, "stat"):
#             _ = os.stat(CAL_FILE)
#         with open(CAL_FILE, "r") as f:
#             data = json.load(f)
#             if isinstance(data, dict) and "low" in data and "high" in data:
#                 _cal.update({
#                     "low": int(data.get("low", 0)),
#                     "high": int(data.get("high", (1 << 12) - 1)),
#                     "enabled": bool(data.get("enabled", False)),
#                 })
#                 print("[CAL] Cargado: low={}, high={}, enabled={}".format(
#                     _cal["low"], _cal["high"], _cal["enabled"]))
#     except Exception as e:
#         print("[CAL] No se pudo cargar: {}".format(e))
#
# def save_calibration():
#     if json is None:
#         print("[CAL] JSON no disponible.")
#         return False
#     try:
#         with open(CAL_FILE, "w") as f:
#             json.dump(_cal, f)
#         print("[CAL] Guardado en {}".format(CAL_FILE))
#         return True
#     except Exception as e:
#         print("[CAL] Error guardando: {}".format(e))
#         return False
#
# def adc_to_voltage(adc_val, width_bits=12, v_full=3.3):
#     # Si AUTO_USE_CALIBRATION y calibración válida, mapea [low..high] → [0..v_full]
#     if AUTO_USE_CALIBRATION and _cal and (_cal.get("high", 0) > _cal.get("low", 0)):
#         span = float(_cal["high"] - _cal["low"]) or 1.0
#         ratio = (adc_val - _cal["low"]) / span
#         ratio = 0.0 if ratio < 0 else (1.0 if ratio > 1 else ratio)
#         return ratio * v_full
#     # Mapeo estándar sin calibración
#     maxcount = (1 << width_bits) - 1
#     return (adc_val / maxcount) * v_full

# -------- Clases auxiliares (opcional) --------

class MovingAverage:
    def __init__(self, size: int):
        self.size = max(1, int(size))
        self.buf = [0] * self.size
        self.sum = 0
        self.idx = 0
        self.count = 0

    def add(self, x: int) -> int:
        old = self.buf[self.idx]
        self.sum -= old
        self.buf[self.idx] = x
        self.sum += x
        self.idx = (self.idx + 1) % self.size
        if self.count < self.size:
            self.count += 1
        return self.sum // self.count

# -------- Loop principal --------

def main():
    period_ms = max(1, int(1000 / LOOP_HZ))
    t0 = now_ms()
    it = 0

    # Ejemplo de cabecera CSV (ajusta campos para tu práctica)
    # print("t_ms,field1,field2")

    try:
        while True:
            t = ticks_diff(now_ms(), t0)

            # LEE SENSORES / ACTUALIZA ESTADO AQUÍ
            # val = adc.read()

            # FORMATEA SALIDA (CSV o logs), p.ej. cada PRINT_EVERY iteraciones
            if it % PRINT_EVERY == 0:
                # print("{},{}".format(t, val))
                pass

            it += 1
            sleep_ms(period_ms)
    except KeyboardInterrupt:
        print("\n[INFO] Ejecución detenida por el usuario.")


if __name__ == "__main__":
    main()
