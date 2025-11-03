# flight_controls.py — Control de superficies de vuelo con servomotores (RP2040)
# Práctica 8: Sistema Integrado

from machine import Pin, PWM
import utime

class FlightControls:
    """
    Clase para gestionar servos de superficies de control (RP2040)
    """
    
    def __init__(self, servos):
        self.servos = {}
        self.angles = {}
        for name, pin_num in servos.items():
            pwm = PWM(Pin(pin_num))
            pwm.freq(50)
            self.servos[name] = pwm
            self.angles[name] = 90
            self._set_angle(name, 90)

    def _angle_to_u16(self, angle):
        # 50 Hz = periodo 20000 µs; 1000-2000 µs útil
        pulse_us = 1000 + (angle / 180.0) * 1000
        duty_u16 = int((pulse_us / 20000.0) * 65535)
        return duty_u16

    def _set_angle(self, name, angle):
        angle = max(0, min(180, int(angle)))
        self.servos[name].duty_u16(self._angle_to_u16(angle))
        self.angles[name] = angle

    def set_surface(self, name, angle):
        if name not in self.servos:
            raise ValueError("Superficie '%s' no existe" % name)
        self._set_angle(name, angle)

    def get_angle(self, name):
        return self.angles.get(name, 90)

    def center_all(self):
        for name in self.servos.keys():
            self._set_angle(name, 90)

    def increment(self, name, delta=5):
        if name in self.angles:
            self._set_angle(name, self.angles[name] + delta)

    def sweep(self, name, duration_ms=2000):
        if name not in self.servos:
            return
        steps = 36
        delay = max(1, duration_ms // (steps * 2))
        for angle in range(0, 181, 5):
            self._set_angle(name, angle)
            utime.sleep_ms(delay)
        for angle in range(180, -1, -5):
            self._set_angle(name, angle)
            utime.sleep_ms(delay)
        self._set_angle(name, 90)

    def get_status(self):
        lines = []
        lines.append("╔════════════════════════════════════════╗")
        lines.append("║   SUPERFICIES DE CONTROL - ESTADO     ║")
        lines.append("╠════════════════════════════════════════╣")
        for name, angle in self.angles.items():
            bar_w = 10
            filled = int((angle / 180.0) * bar_w)
            bar = "█" * filled + "░" * (bar_w - filled)
            label = name.capitalize().ljust(12)
            lines.append(f"║ {label} {angle:3d}° [{bar}]     ║")
        lines.append("╚════════════════════════════════════════╝")
        return "\n".join(lines)

    def deinit(self):
        self.center_all()
        utime.sleep_ms(300)
        for pwm in self.servos.values():
            pwm.deinit()
