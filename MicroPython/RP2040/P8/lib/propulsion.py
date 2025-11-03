# propulsion.py — Control de sistema de propulsión (RP2040)
# Práctica 8: Sistema Integrado

from machine import Pin, PWM
import utime

class PropulsionSystem:
    """
    Control de potencia para motor (PWM + MOSFET)
    """
    def __init__(self, pin, freq=1000):
        self.pwm = PWM(Pin(pin))
        self.pwm.freq(freq)
        self.throttle_percent = 0
        self.set_throttle(0)

    def set_throttle(self, percent):
        percent = max(0, min(100, int(percent)))
        self.throttle_percent = percent
        duty = int((percent / 100.0) * 65535)
        self.pwm.duty_u16(duty)

    def get_throttle(self):
        return self.throttle_percent

    def increment(self, delta=5):
        self.set_throttle(self.throttle_percent + delta)

    def emergency_stop(self):
        self.set_throttle(0)

    def ramp_up(self, target_percent, duration_ms=2000):
        start = self.throttle_percent
        target_percent = max(0, min(100, int(target_percent)))
        steps = max(1, duration_ms // 50)
        delta = (target_percent - start) / steps
        for i in range(steps):
            self.set_throttle(start + delta * (i + 1))
            utime.sleep_ms(50)

    def ramp_down(self, duration_ms=2000):
        self.ramp_up(0, duration_ms)

    def get_status(self):
        throttle = self.throttle_percent
        bar_w = 20
        filled = int((throttle / 100.0) * bar_w)
        bar = "█" * filled + "░" * (bar_w - filled)
        status = "APAGADO" if throttle == 0 else "ACTIVO"
        lines = []
        lines.append("╔════════════════════════════════════════╗")
        lines.append("║     SISTEMA DE PROPULSIÓN - ESTADO    ║")
        lines.append("╠════════════════════════════════════════╣")
        lines.append(f"║ Potencia:  {throttle:3d}% [{bar}] ║")
        lines.append(f"║ Estado:    {status.ljust(26)} ║")
        lines.append("╚════════════════════════════════════════╝")
        return "\n".join(lines)

    def deinit(self):
        self.set_throttle(0)
        utime.sleep_ms(100)
        self.pwm.deinit()
