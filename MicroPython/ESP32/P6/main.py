"""
Practica 6 — Conmutación de potencia por PWM (transistor)

Modos:
  1) Encendido/Apagado (100%/0%)
  2) PWM manual (0–100%)
  3) Barrido 0→100→0
  4) Potenciómetro (ADC)
  5) Registro CSV (barrido con muestreo) — para tools/sisela_signal

Presiona 'm' + ENTER en cualquier modo para regresar al menú.

El Modo 5 alimenta la toolkit PC `tools/sisela_signal/`:
  python -m sisela_signal capture --port COM5 --menu 5 --out cap.csv
  python -m sisela_signal characterize --file cap.csv --col adc_raw --mode adc
  python -m sisela_signal live --port COM5 --menu 5 --cols duty_pct,adc_raw
"""

try:
    import sys
    import uselect
    import utime as time
    from machine import Pin, PWM, ADC
    MICROPYTHON = True
except ImportError:
    print("[PC Mode] Usando polyfills para análisis estático.")
    MICROPYTHON = False
    import sys

    class Pin:
        IN = 1; OUT = 2; PULL_UP = 3
        def __init__(self, *a, **kw): pass
        def value(self, v=None): return 0

    class PWM:
        def __init__(self, *a, **kw): pass
        def duty_u16(self, v=None): pass
        def duty(self, v=None): pass
        def deinit(self): pass

    class ADC:
        ATTN_11DB = 3
        WIDTH_12BIT = 3
        def __init__(self, *a, **kw): pass
        def atten(self, v=None): pass
        def width(self, v=None): pass
        def read(self): return 0

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

try:
    from siglab import stream_csv
    HAVE_SIGLAB = True
except ImportError:
    HAVE_SIGLAB = False


# Configuración de pines/frecuencia
ACT_PIN = 18  # GPIO para la compuerta/base (PWM)
PWM_FREQ = 1000  # Hz
ADC_PIN = 34  # Potenciómetro opcional


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


def _set_duty_percent(pwm: PWM, percent: float):
    """Ajusta duty (0–100%) usando duty_u16 o duty, según firmware."""
    if percent < 0:
        percent = 0
    if percent > 100:
        percent = 100

    if hasattr(pwm, "duty_u16"):
        pwm.duty_u16(int(65535 * (percent / 100.0)))
    elif hasattr(pwm, "duty"):
        pwm.duty(int(1023 * (percent / 100.0)))
    else:
        raise RuntimeError("PWM sin duty_u16/duty")


def _build_pwm():
    pwm = PWM(Pin(ACT_PIN), freq=PWM_FREQ)
    _set_duty_percent(pwm, 0)
    return pwm


def _build_adc():
    adc = ADC(Pin(ADC_PIN))
    if hasattr(adc, "atten"):
        adc.atten(ADC.ATTN_11DB)
    if hasattr(adc, "width"):
        adc.width(ADC.WIDTH_12BIT)
    return adc


def mode_on_off(pwm: PWM):
    print("\n[Modo 1] Encendido/Apagado. 'm'+ENTER para menú.")
    duty_list = [0, 100]
    idx = 0
    while True:
        _set_duty_percent(pwm, duty_list[idx])
        print("Duty = {}%".format(duty_list[idx]))
        idx = 1 - idx
        for _ in range(10):  # 1 s total
            if _readline_nonblocking().lower() == "m":
                _set_duty_percent(pwm, 0)
                return
            time.sleep_ms(100)


def mode_manual_pwm(pwm: PWM):
    print("\n[Modo 2] PWM manual. Ingresa 0–100 y ENTER. 'm' para menú.")
    while True:
        print("Ingresa duty %: ", end="")
        line = sys.stdin.readline().strip()
        if not line:
            continue
        if line.lower() == "m":
            _set_duty_percent(pwm, 0)
            return
        try:
            val = float(line)
            _set_duty_percent(pwm, val)
            print("Aplicado duty = {:.1f}%".format(val))
        except ValueError:
            print("Entrada inválida. Usa números 0–100 o 'm'.")


def mode_sweep(pwm: PWM):
    print("\n[Modo 3] Barrido 0→100→0. 'm' para menú.")
    duty = 0
    step = 1
    while True:
        _set_duty_percent(pwm, duty)
        if duty % 10 == 0:
            print("Duty = {}%".format(duty))
        duty += step
        if duty >= 100:
            duty = 100
            step = -1
        elif duty <= 0:
            duty = 0
            step = 1
        if _readline_nonblocking().lower() == "m":
            _set_duty_percent(pwm, 0)
            return
        time.sleep_ms(15)


def mode_potentiometer(pwm: PWM, adc: ADC | None):
    print("\n[Modo 4] Potenciómetro ADC GPIO{}. 'm' para menú.".format(ADC_PIN))
    if adc is None:
        print("[WARN] ADC no disponible en este firmware/pin.")
        return
    last_print = time.ticks_ms()
    while True:
        raw = adc.read()
        duty = int((raw / 4095.0) * 100)
        _set_duty_percent(pwm, duty)
        now = time.ticks_ms()
        if time.ticks_diff(now, last_print) > 500:
            print("ADC={} → Duty={}% .".format(raw, duty))
            last_print = now
        if _readline_nonblocking().lower() == "m":
            _set_duty_percent(pwm, 0)
            return
        time.sleep_ms(10)


def mode_csv_log(pwm: PWM, adc: ADC | None):
    """Modo 5: barrido automático 0->100->0 registrando CSV `t_us,duty_pct,adc_raw`
    a Fs fija, para `tools/sisela_signal` (captura, análisis o vista en vivo)."""
    print("\n[Modo 5] Registro CSV (barrido con muestreo). 'm'+ENTER aborta.")
    if not HAVE_SIGLAB:
        print("[WARN] Falta lib/siglab.py. No se puede registrar CSV.")
        return
    fs = 50.0  # Hz
    duration_s = 4.0  # un barrido completo 0->100->0 aprox.
    n = int(fs * duration_s)
    step = 100.0 / (n / 2.0)
    state = {"duty": 0.0, "dir": 1.0}

    def _read():
        d = state["duty"]
        _set_duty_percent(pwm, d)
        raw = adc.read() if adc is not None else 0
        state["duty"] += state["dir"] * step
        if state["duty"] >= 100.0:
            state["duty"], state["dir"] = 100.0, -1.0
        elif state["duty"] <= 0.0:
            state["duty"], state["dir"] = 0.0, 1.0
        return (round(d, 1), raw)

    stream_csv(_read, fs, cols=("duty_pct", "adc_raw"), max_samples=n)
    _set_duty_percent(pwm, 0)


MENU = (
    """
==============================
 Practica 6 — Conmutación PWM
 GPIO{} @ {} Hz
------------------------------
 1) Encendido/Apagado
 2) PWM manual (0–100%)
 3) Barrido (0→100→0)
 4) Potenciómetro (ADC GPIO{})
 5) Registro CSV (barrido con muestreo)
==============================
""".format(ACT_PIN, PWM_FREQ, ADC_PIN)
)


def main():
    pwm = _build_pwm()
    adc = _build_adc()
    try:
        while True:
            print(MENU)
            sel = input("Selecciona opción: ")
            if not sel:
                continue
            if sel == "1":
                mode_on_off(pwm)
            elif sel == "2":
                mode_manual_pwm(pwm)
            elif sel == "3":
                mode_sweep(pwm)
            elif sel == "4":
                mode_potentiometer(pwm, adc)
            elif sel == "5":
                mode_csv_log(pwm, adc)
            else:
                print("Opción no válida.")
    finally:
        _set_duty_percent(pwm, 0)
        pwm.deinit()


if __name__ == "__main__":
    main()
