# landing_gear.py — Control de tren de aterrizaje con motor a pasos
# Práctica 8: Sistema Integrado

from machine import Pin
import utime
import sys

# Intentar importar drivers de stepper (deben estar en lib/)
try:
    from stepper_a4988 import StepperA4988
    HAS_A4988 = True
except ImportError:
    HAS_A4988 = False

try:
    from stepper_uln2003 import StepperULN2003
    HAS_ULN2003 = False
except ImportError:
    HAS_ULN2003 = False


class LandingGear:
    """
    Clase para gestionar tren de aterrizaje con motor a pasos
    Estados: RETRACTED, EXTENDED, MOVING, UNKNOWN
    """
    
    # Estados del tren
    STATE_RETRACTED = "RETRACTED"
    STATE_EXTENDED = "EXTENDED"
    STATE_MOVING = "MOVING"
    STATE_UNKNOWN = "UNKNOWN"
    
    def __init__(self, driver_type="A4988", pins=None, endstop_pin=4):
        """
        Inicializa sistema de tren de aterrizaje
        
        Args:
            driver_type: "A4988" o "ULN2003"
            pins: dict con pines según driver
                  A4988: {'step': 19, 'dir': 21, 'en': 5}
                  ULN2003: {'pins': [19, 21, 22, 23]}
            endstop_pin: GPIO para fin de carrera (límite extendido)
        """
        self.driver_type = driver_type
        self.driver = None
        self.state = self.STATE_UNKNOWN
        self.position_steps = 0  # Posición relativa en pasos
        
        # Configurar endstop
        self.endstop = Pin(endstop_pin, Pin.IN, Pin.PULL_UP)
        
        # Configurar driver de stepper
        if driver_type == "A4988" and HAS_A4988:
            self.driver = StepperA4988(
                step_pin=pins['step'],
                dir_pin=pins['dir'],
                en_pin=pins['en']
            )
            self.steps_full_travel = 800  # Aprox. 4 revoluciones
        elif driver_type == "ULN2003" and HAS_ULN2003:
            self.driver = StepperULN2003(pins=pins['pins'])
            self.steps_full_travel = 2048  # Media revolución aprox.
        else:
            raise RuntimeError(f"Driver '{driver_type}' no disponible o no soportado")
        
        self.rpm_default = 30  # RPM moderado para tren
    
    def is_endstop_triggered(self):
        """Verifica si el endstop está activado (tren completamente extendido)"""
        return self.endstop.value() == 0  # Pull-up, LOW cuando activado
    
    def extend(self, blocking=True):
        """
        Extiende el tren de aterrizaje hasta el endstop
        
        Args:
            blocking: Si True, espera hasta que termine
        
        Returns:
            bool: True si alcanzó endstop, False si no
        """
        if self.state == self.STATE_EXTENDED:
            print("Tren ya extendido")
            return True
        
        print("Extendiendo tren de aterrizaje...")
        self.state = self.STATE_MOVING
        
        # Mover hacia adelante (dirección positiva)
        self.driver.set_direction(1)
        
        steps_moved = 0
        max_steps = self.steps_full_travel + 200  # Margen de seguridad
        
        while steps_moved < max_steps:
            if self.is_endstop_triggered():
                print("Endstop alcanzado - Tren extendido")
                self.state = self.STATE_EXTENDED
                self.position_steps = 0  # Resetear posición en endstop
                return True
            
            self.driver.step()
            steps_moved += 1
            self.position_steps += 1
            
            # Delay según RPM
            interval_us = self._rpm_to_interval(self.rpm_default)
            utime.sleep_us(interval_us)
        
        print("ADVERTENCIA: Endstop no alcanzado después de máximo de pasos")
        self.state = self.STATE_UNKNOWN
        return False
    
    def retract(self, steps=None):
        """
        Retrae el tren de aterrizaje
        
        Args:
            steps: Número de pasos a retroceder. Si None, usa steps_full_travel
        """
        if self.state == self.STATE_RETRACTED:
            print("Tren ya retraído")
            return
        
        if steps is None:
            steps = self.steps_full_travel
        
        print(f"Retrayendo tren de aterrizaje ({steps} pasos)...")
        self.state = self.STATE_MOVING
        
        # Mover hacia atrás (dirección negativa)
        self.driver.set_direction(0)
        
        for _ in range(steps):
            self.driver.step()
            self.position_steps -= 1
            
            interval_us = self._rpm_to_interval(self.rpm_default)
            utime.sleep_us(interval_us)
        
        self.state = self.STATE_RETRACTED
        print("Tren retraído")
    
    def homing(self):
        """
        Ejecuta secuencia de homing: extiende hasta endstop y retrae un poco
        para establecer posición de referencia
        """
        print("Ejecutando homing del tren de aterrizaje...")
        
        # Extender hasta endstop
        if not self.extend():
            print("ERROR: Homing falló - endstop no alcanzado")
            return False
        
        # Retroceder un poco para liberar endstop
        print("Retrocediendo para liberar endstop...")
        self.driver.set_direction(0)
        for _ in range(50):
            self.driver.step()
            interval_us = self._rpm_to_interval(self.rpm_default)
            utime.sleep_us(interval_us)
        
        self.position_steps = 50
        self.state = self.STATE_EXTENDED
        print("Homing completado")
        return True
    
    def _rpm_to_interval(self, rpm, steps_per_rev=200):
        """Convierte RPM a intervalo entre pasos en microsegundos"""
        if rpm <= 0:
            return 10000  # Muy lento
        steps_per_second = (rpm * steps_per_rev) / 60.0
        interval_seconds = 1.0 / steps_per_second
        return int(interval_seconds * 1_000_000)
    
    def get_state(self):
        """Retorna el estado actual del tren"""
        return self.state
    
    def get_status(self):
        """
        Genera resumen del estado del tren
        
        Returns:
            str: Texto formateado con estado del tren
        """
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
        """Libera recursos del driver"""
        if self.driver:
            if hasattr(self.driver, 'disable'):
                self.driver.disable()
            if hasattr(self.driver, 'release'):
                self.driver.release()
