# propulsion.py — Control de sistema de propulsión (motor/hélice)
# Práctica 8: Sistema Integrado

from machine import Pin, PWM
import utime

class PropulsionSystem:
    """
    Clase para gestionar sistema de propulsión (motor DC o similar)
    usando PWM + transistor MOSFET
    """
    
    def __init__(self, pin, freq=1000):
        """
        Inicializa sistema de propulsión
        
        Args:
            pin: GPIO para señal PWM
            freq: Frecuencia PWM en Hz (default 1kHz)
        """
        self.pwm = PWM(Pin(pin), freq=freq)
        self.throttle_percent = 0
        self.set_throttle(0)  # Iniciar apagado
    
    def set_throttle(self, percent):
        """
        Establece potencia del motor (throttle)
        
        Args:
            percent: Potencia 0-100%
        """
        percent = max(0, min(100, percent))  # Limitar 0-100
        self.throttle_percent = percent
        
        # Convertir a duty_u16 (0-65535)
        duty = int((percent / 100.0) * 65535)
        self.pwm.duty_u16(duty)
    
    def get_throttle(self):
        """Obtiene potencia actual (0-100%)"""
        return self.throttle_percent
    
    def increment(self, delta=5):
        """
        Incrementa o decrementa potencia
        
        Args:
            delta: Cambio en % (puede ser negativo)
        """
        new_throttle = self.throttle_percent + delta
        self.set_throttle(new_throttle)
    
    def emergency_stop(self):
        """Corte de emergencia (apaga motor)"""
        self.set_throttle(0)
    
    def ramp_up(self, target_percent, duration_ms=2000):
        """
        Rampa de aceleración suave
        
        Args:
            target_percent: Potencia objetivo (0-100%)
            duration_ms: Duración de la rampa
        """
        start = self.throttle_percent
        target_percent = max(0, min(100, target_percent))
        steps = 20
        step_delay = duration_ms // steps
        delta = (target_percent - start) / steps
        
        for i in range(steps):
            self.set_throttle(start + delta * (i + 1))
            utime.sleep_ms(step_delay)
    
    def ramp_down(self, duration_ms=2000):
        """Rampa de desaceleración hasta 0%"""
        self.ramp_up(0, duration_ms)
    
    def get_status(self):
        """
        Genera resumen del estado del motor
        
        Returns:
            str: Texto formateado con estado del motor
        """
        throttle = self.throttle_percent
        
        # Barra de progreso
        bar_width = 20
        filled = int((throttle / 100.0) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        
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
        """Libera recursos y apaga motor"""
        self.set_throttle(0)
        utime.sleep_ms(100)
        self.pwm.deinit()
