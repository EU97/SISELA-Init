# sensors.py — Gestión de sensores ADC para telemetría de vuelo
# Práctica 8: Sistema Integrado

from machine import ADC, Pin
import utime

class FlightSensors:
    """
    Clase para gestionar múltiples sensores analógicos (ADC)
    Simula instrumentos de vuelo: altitud, velocidad, actitud, luminosidad
    """
    
    def __init__(self, pins):
        """
        Inicializa sensores ADC
        
        Args:
            pins: dict con claves 'altitude', 'speed', 'attitude', 'light'
                  y valores como números de GPIO
        """
        self.adcs = {}
        self.raw_values = {}
        self.scaled_values = {}
        
        # Configurar ADCs
        for name, pin_num in pins.items():
            adc = ADC(Pin(pin_num))
            adc.atten(ADC.ATTN_11DB)  # Rango completo 0-3.3V
            adc.width(ADC.WIDTH_12BIT)  # Resolución 12 bits (0-4095)
            self.adcs[name] = adc
            self.raw_values[name] = 0
            self.scaled_values[name] = 0
        
        # Parámetros de escalado (ajustar según aplicación)
        self.scales = {
            'altitude': {'min': 0, 'max': 3000, 'unit': 'm'},      # 0-3000 metros
            'speed': {'min': 0, 'max': 300, 'unit': 'kt'},        # 0-300 nudos
            'attitude': {'min': -90, 'max': 90, 'unit': '°'},     # -90 a +90 grados
            'light': {'min': 0, 'max': 1000, 'unit': 'lux'}       # 0-1000 lux
        }
    
    def read_all(self):
        """
        Lee todos los sensores y actualiza valores crudos y escalados
        
        Returns:
            dict: Valores escalados de todos los sensores
        """
        for name, adc in self.adcs.items():
            raw = adc.read()
            self.raw_values[name] = raw
            
            # Escalar según rango definido
            scale = self.scales[name]
            scaled = scale['min'] + (raw / 4095.0) * (scale['max'] - scale['min'])
            self.scaled_values[name] = round(scaled, 1)
        
        return self.scaled_values.copy()
    
    def get_sensor(self, name):
        """
        Obtiene el valor escalado de un sensor específico
        
        Args:
            name: Nombre del sensor ('altitude', 'speed', etc.)
        
        Returns:
            float: Valor escalado del sensor
        """
        if name not in self.adcs:
            raise ValueError(f"Sensor '{name}' no existe")
        
        raw = self.adcs[name].read()
        self.raw_values[name] = raw
        
        scale = self.scales[name]
        scaled = scale['min'] + (raw / 4095.0) * (scale['max'] - scale['min'])
        self.scaled_values[name] = round(scaled, 1)
        
        return self.scaled_values[name]
    
    def get_raw(self, name):
        """Obtiene el valor crudo ADC (0-4095)"""
        return self.raw_values.get(name, 0)
    
    def get_percentage(self, name):
        """Obtiene el porcentaje del rango (0-100%)"""
        raw = self.raw_values.get(name, 0)
        return round((raw / 4095.0) * 100, 1)
    
    def calibrate(self, name, min_val, max_val):
        """
        Calibra el rango de un sensor
        
        Args:
            name: Nombre del sensor
            min_val: Valor mínimo de la escala física
            max_val: Valor máximo de la escala física
        """
        if name in self.scales:
            self.scales[name]['min'] = min_val
            self.scales[name]['max'] = max_val
    
    def get_summary(self):
        """
        Genera resumen formateado de todos los sensores
        
        Returns:
            str: Texto con estado de todos los sensores
        """
        self.read_all()
        lines = []
        lines.append("╔════════════════════════════════════════╗")
        lines.append("║      SENSORES DE VUELO - ESTADO       ║")
        lines.append("╠════════════════════════════════════════╣")
        
        for name, value in self.scaled_values.items():
            unit = self.scales[name]['unit']
            pct = self.get_percentage(name)
            raw = self.raw_values[name]
            
            # Crear barra de progreso
            bar_width = 10
            filled = int((pct / 100.0) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            
            label = name.capitalize().ljust(12)
            value_str = f"{value:7.1f} {unit:4s}".rjust(12)
            lines.append(f"║ {label} {value_str} [{bar}] {pct:5.1f}% ║")
        
        lines.append("╚════════════════════════════════════════╝")
        return "\n".join(lines)
    
    def deinit(self):
        """Libera recursos de los ADCs"""
        for adc in self.adcs.values():
            # ADC no tiene método deinit explícito en MicroPython ESP32
            pass
