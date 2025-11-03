# flight_controls.py — Control de superficies de vuelo con servomotores
# Práctica 8: Sistema Integrado

from machine import Pin, PWM
import utime

class FlightControls:
    """
    Clase para gestionar servomotores de superficies de control
    (alerones, elevadores, timón, etc.)
    """
    
    def __init__(self, servos):
        """
        Inicializa servos para superficies de control
        
        Args:
            servos: dict con nombre de superficie y pin GPIO
                    ej: {'aileron': 25, 'elevator': 26}
        """
        self.servos = {}
        self.angles = {}
        
        for name, pin_num in servos.items():
            pwm = PWM(Pin(pin_num), freq=50)  # 50 Hz para servos
            self.servos[name] = pwm
            self.angles[name] = 90  # Posición neutral
            self._set_angle(name, 90)
    
    def _angle_to_duty(self, angle):
        """
        Convierte ángulo (0-180°) a duty cycle (0-1023 en ESP32)
        
        Mapeo:
        0° → ~1000 µs → duty ~51
        90° → ~1500 µs → duty ~77
        180° → ~2000 µs → duty ~102
        """
        # Rango de pulso: 1000-2000 µs
        # Periodo: 20000 µs (50 Hz)
        # duty_u16 = (pulse_us / 20000) * 65535
        pulse_us = 1000 + (angle / 180.0) * 1000
        duty_u16 = int((pulse_us / 20000.0) * 65535)
        return duty_u16
    
    def _set_angle(self, name, angle):
        """Establece ángulo de un servo (uso interno)"""
        angle = max(0, min(180, angle))  # Limitar 0-180
        duty = self._angle_to_duty(angle)
        self.servos[name].duty_u16(duty)
        self.angles[name] = angle
    
    def set_surface(self, name, angle):
        """
        Establece ángulo de una superficie de control
        
        Args:
            name: Nombre de la superficie ('aileron', 'elevator', etc.)
            angle: Ángulo deseado (0-180°), 90° = neutral
        """
        if name not in self.servos:
            raise ValueError(f"Superficie '{name}' no existe")
        
        self._set_angle(name, angle)
    
    def get_angle(self, name):
        """Obtiene el ángulo actual de una superficie"""
        return self.angles.get(name, 90)
    
    def center_all(self):
        """Centra todas las superficies a posición neutral (90°)"""
        for name in self.servos.keys():
            self._set_angle(name, 90)
    
    def increment(self, name, delta=5):
        """
        Incrementa ángulo de superficie
        
        Args:
            name: Nombre de superficie
            delta: Incremento en grados (puede ser negativo)
        """
        if name in self.angles:
            new_angle = self.angles[name] + delta
            self._set_angle(name, new_angle)
    
    def sweep(self, name, duration_ms=2000):
        """
        Barre una superficie de 0 a 180° y regresa
        
        Args:
            name: Nombre de superficie
            duration_ms: Duración total del barrido (ms)
        """
        if name not in self.servos:
            return
        
        steps = 36  # 5° por paso
        delay_ms = duration_ms // (steps * 2)
        
        # 0 → 180
        for angle in range(0, 181, 5):
            self._set_angle(name, angle)
            utime.sleep_ms(delay_ms)
        
        # 180 → 0
        for angle in range(180, -1, -5):
            self._set_angle(name, angle)
            utime.sleep_ms(delay_ms)
        
        # Volver a neutral
        self._set_angle(name, 90)
    
    def get_status(self):
        """
        Genera resumen del estado de superficies
        
        Returns:
            str: Texto formateado con ángulos de todas las superficies
        """
        lines = []
        lines.append("╔════════════════════════════════════════╗")
        lines.append("║   SUPERFICIES DE CONTROL - ESTADO     ║")
        lines.append("╠════════════════════════════════════════╣")
        
        for name, angle in self.angles.items():
            # Crear barra visual del ángulo
            bar_width = 10
            filled = int((angle / 180.0) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            
            label = name.capitalize().ljust(12)
            angle_str = f"{angle:3d}°"
            lines.append(f"║ {label} {angle_str} [{bar}]     ║")
        
        lines.append("╚════════════════════════════════════════╝")
        return "\n".join(lines)
    
    def deinit(self):
        """Libera recursos de PWM y centra servos"""
        self.center_all()
        utime.sleep_ms(500)
        for pwm in self.servos.values():
            pwm.deinit()
