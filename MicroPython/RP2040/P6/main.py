"""
Practica 6 — Conmutación de potencia por PWM (transistor) (RP2040)

Modos:
  1) Encendido/Apagado (100%/0%)
  2) PWM manual (0–100%)
  3) Barrido 0→100→0
  4) Potenciómetro (ADC)

Presiona 'm' + ENTER en cualquier modo para regresar al menú.

🔄 ADAPTACIONES RP2040:
  - Pin PWM: GP18 (PWM1 A)
  - Pin ADC: GP26 (ADC0) en lugar de GPIO34
  - ADC 16-bit: adc.read_u16() → 0–65535
  - Sin atten(): No requiere configuración de atenuación
"""

import sys
import uselect
import utime as time
from machine import Pin, PWM, ADC


# Configuración de pines/frecuencia
ACT_PIN = 18  # GP18 para la compuerta/base (PWM)
PWM_FREQ = 1000  # Hz
ADC_PIN = 26  # GP26 (ADC0) — Potenciómetro opcional


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
    """
    🔄 RP2040: ADC(pin_number) directamente, sin Pin() wrapper.
    No requiere atten() ni width().
    """
    adc = ADC(ADC_PIN)
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
    """
    🔄 RP2040: ADC de 16 bits (0–65535).
    Control más suave que ESP32 (12-bit).
    """
    print("\n[Modo 4] Potenciómetro ADC GP{}. 'm' para menú.".format(ADC_PIN))
    if adc is None:
        print("[WARN] ADC no disponible en este firmware/pin.")
        return
    last_print = time.ticks_ms()
    while True:
        raw = adc.read_u16()  # 🔄 RP2040: 16-bit (0–65535)
        duty = int((raw / 65535.0) * 100)  # 🔄 Divisor 65535 en lugar de 4095
        _set_duty_percent(pwm, duty)
        now = time.ticks_ms()
        if time.ticks_diff(now, last_print) > 500:
            print("ADC={} → Duty={}% .".format(raw, duty))
            last_print = now
        if _readline_nonblocking().lower() == "m":
            _set_duty_percent(pwm, 0)
            return
        time.sleep_ms(10)


MENU = (
    """
==============================
 Practica 6 — Conmutación PWM (RP2040)
 GP{} @ {} Hz
------------------------------
 1) Encendido/Apagado
 2) PWM manual (0–100%)
 3) Barrido (0→100→0)
 4) Potenciómetro (ADC GP{})
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
            else:
                print("Opción no válida.")
    finally:
        _set_duty_percent(pwm, 0)
        pwm.deinit()


if __name__ == "__main__":
    main()
