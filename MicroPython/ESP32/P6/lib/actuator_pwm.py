"""
ActuatorPWM — Pequeño envoltorio para manejar PWM por porcentaje (0–100%).
Compatible con firmwares que exponen duty_u16 o duty (0–1023).
"""
from machine import Pin, PWM

class ActuatorPWM:
    def __init__(self, pin: int, freq: int = 1000):
        self.pwm = PWM(Pin(pin), freq=freq)
        self.percent = 0
        self.set_percent(0)

    def set_percent(self, percent: float):
        if percent < 0:
            percent = 0
        if percent > 100:
            percent = 100
        self.percent = percent
        if hasattr(self.pwm, "duty_u16"):
            self.pwm.duty_u16(int(65535 * (percent / 100.0)))
        elif hasattr(self.pwm, "duty"):
            self.pwm.duty(int(1023 * (percent / 100.0)))
        else:
            raise RuntimeError("PWM sin duty_u16/duty")

    def off(self):
        self.set_percent(0)

    def deinit(self):
        self.off()
        self.pwm.deinit()
