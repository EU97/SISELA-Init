# landing_gear.py — Control de tren de aterrizaje con motor a pasos (RP2040)
# Práctica 8: Sistema Integrado

from machine import Pin

# Drivers esperados en lib/: stepper_a4988.py y/o stepper_uln2003.py
try:
    from stepper_a4988 import StepperA4988
    HAS_A4988 = True
except ImportError:
    HAS_A4988 = False

try:
    from stepper_uln2003 import StepperULN2003
    HAS_ULN2003 = True
except ImportError:
    HAS_ULN2003 = False


class LandingGear:
    """Gestión del tren de aterrizaje con soporte para A4988 o ULN2003"""

    STATE_RETRACTED = "RETRACTED"
    STATE_EXTENDED = "EXTENDED"
    STATE_MOVING = "MOVING"
    STATE_UNKNOWN = "UNKNOWN"

    def __init__(self, driver_type="A4988", pins=None, endstop_pin=4):
        self.driver_type = driver_type
        self.driver = None
        self.state = self.STATE_UNKNOWN
        self.position_steps = 0

        # Endstop con pull-up interno; activo a nivel bajo
        self.endstop = Pin(endstop_pin, Pin.IN, Pin.PULL_UP)

        if driver_type == "A4988" and HAS_A4988:
            self.driver = StepperA4988(
                step_pin=pins['step'],
                dir_pin=pins['dir'],
                enable_pin=pins.get('en', None)
            )
            # Viaje completo estimado (ajustable según mecánica)
            self.steps_full_travel = 800
        elif driver_type == "ULN2003" and HAS_ULN2003:
            self.driver = StepperULN2003(pins=pins['pins'])
            self.steps_full_travel = 2048
        else:
            raise RuntimeError("Driver '%s' no disponible o no soportado" % driver_type)

        # RPM por defecto (para A4988), ULN2003 usa delay interno
        self.rpm_default = 30

    # Utilidades compatibles con distintos drivers
    def _set_direction(self, cw=True):
        if hasattr(self.driver, 'set_dir'):
            self.driver.set_dir(cw)
        elif hasattr(self.driver, 'set_direction'):
            self.driver.set_direction(1 if cw else 0)
        # ULN2003 usa signo de steps; no es necesario aquí

    def _step_once(self, cw=True, interval_us=None):
        if hasattr(self.driver, 'step_once'):
            # A4988 RP2040 P7
            self._set_direction(cw)
            self.driver.step_once(interval_us)
        elif hasattr(self.driver, 'step'):
            # Fallback genérico: usar +1/-1 pasos
            steps = 1 if cw else -1
            self.driver.step(steps, interval_us)
        else:
            raise RuntimeError('Driver de stepper no expone método de paso')

    def _rpm_to_interval(self, rpm, steps_per_rev=200):
        if rpm <= 0:
            return 10000
        sps = (rpm * steps_per_rev) / 60.0
        return int((1.0 / sps) * 1_000_000)

    def is_endstop_triggered(self):
        return self.endstop.value() == 0

    def extend(self):
        if self.state == self.STATE_EXTENDED:
            print("Tren ya extendido")
            return True

        print("Extendiendo tren de aterrizaje...")
        self.state = self.STATE_MOVING
        interval_us = self._rpm_to_interval(self.rpm_default)

        # Dirección hacia adelante
        steps_moved = 0
        max_steps = self.steps_full_travel + 200
        while steps_moved < max_steps:
            if self.is_endstop_triggered():
                print("Endstop alcanzado - Tren extendido")
                self.state = self.STATE_EXTENDED
                self.position_steps = 0
                return True
            self._step_once(True, interval_us)
            steps_moved += 1
            self.position_steps += 1
        print("ADVERTENCIA: Endstop no alcanzado en extensión")
        self.state = self.STATE_UNKNOWN
        return False

    def retract(self, steps=None):
        if self.state == self.STATE_RETRACTED:
            print("Tren ya retraído")
            return
        if steps is None:
            steps = self.steps_full_travel
        print("Retrayendo tren de aterrizaje (%d pasos)..." % steps)
        self.state = self.STATE_MOVING
        interval_us = self._rpm_to_interval(self.rpm_default)
        for _ in range(steps):
            self._step_once(False, interval_us)
            self.position_steps -= 1
        self.state = self.STATE_RETRACTED
        print("Tren retraído")

    def homing(self):
        print("Ejecutando homing del tren de aterrizaje...")
        if not self.extend():
            print("ERROR: homing falló - endstop no alcanzado")
            return False
        # Retraer un poco para liberar endstop
        interval_us = self._rpm_to_interval(self.rpm_default)
        for _ in range(50):
            self._step_once(False, interval_us)
        self.position_steps = 50
        self.state = self.STATE_EXTENDED
        print("Homing completado")
        return True

    def get_state(self):
        return self.state

    def get_status(self):
        state_display = {
            self.STATE_EXTENDED: "EXTENDIDO ✓",
            self.STATE_RETRACTED: "RETRAÍDO ✗",
            self.STATE_MOVING: "EN MOVIMIENTO...",
            self.STATE_UNKNOWN: "DESCONOCIDO ?"
        }
        endstop_state = "ACTIVADO" if self.is_endstop_triggered() else "LIBRE"
        lines = []
        lines.append("╔════════════════════════════════════════╗")
        lines.append("║   TREN DE ATERRIZAJE - ESTADO         ║")
        lines.append("╠════════════════════════════════════════╣")
        lines.append(f"║ Estado:    {state_display[self.state].ljust(26)} ║")
        lines.append(f"║ Endstop:   {endstop_state.ljust(26)} ║")
        lines.append(f"║ Posición:  {self.position_steps:5d} pasos{' '*16}║")
        lines.append(f"║ Driver:    {self.driver_type.ljust(26)} ║")
        lines.append("╚════════════════════════════════════════╝")
        return "\n".join(lines)

    def deinit(self):
        if hasattr(self.driver, 'disable'):
            self.driver.disable()
        if hasattr(self.driver, 'release'):
            self.driver.release()
