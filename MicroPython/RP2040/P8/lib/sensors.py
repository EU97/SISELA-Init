# sensors.py — Gestión de sensores ADC para telemetría de vuelo (RP2040)
# Práctica 8: Sistema Integrado

from machine import ADC, Pin

class FlightSensors:
    """
    Clase para gestionar múltiples sensores analógicos en RP2040.
    Nota: RP2040 ofrece 3 entradas ADC externas (GP26, GP27, GP28) +
    1 canal interno (ADC4: temperatura). Por ello, esta práctica usa
    TEMP interna como cuarto canal por defecto, salvo que se especifique otro.
    """
    
    def __init__(self, pins):
        """
        Inicializa sensores ADC
        
        Args:
            pins: dict con claves 'altitude', 'speed', 'attitude', 'light'
                  y valores GP o cadenas especiales ('TEMP')
        """
        self.channels = {}
        self.raw_values = {}
        self.scaled_values = {}

        # Configuración de escalas (ajustables)
        self.scales = {
            'altitude': {'min': 0, 'max': 3000, 'unit': 'm'},     # 0-3000 m
            'speed':    {'min': 0, 'max': 300,  'unit': 'kt'},    # 0-300 kt
            'attitude': {'min': -90,'max': 90,  'unit': '°'},     # -90..+90°
            'light':    {'min': 0, 'max': 1000, 'unit': 'lux'}    # 0-1000 lux (sim)
        }

        for name, pin_id in pins.items():
            if pin_id == 'TEMP':
                # ADC interno de temperatura (canal 4)
                self.channels[name] = ADC(4)
            else:
                self.channels[name] = ADC(Pin(pin_id))
            self.raw_values[name] = 0
            self.scaled_values[name] = 0.0

    def _read_u16(self, name):
        return self.channels[name].read_u16()  # 0..65535

    def _scale_value(self, name, raw):
        # Escala 16-bit a rango físico
        scale = self.scales[name]
        scaled = scale['min'] + (raw / 65535.0) * (scale['max'] - scale['min'])
        return round(scaled, 1)

    def read_all(self):
        for name in self.channels.keys():
            raw = self._read_u16(name)
            self.raw_values[name] = raw
            self.scaled_values[name] = self._scale_value(name, raw)
        return self.scaled_values.copy()

    def get_sensor(self, name):
        if name not in self.channels:
            raise ValueError("Sensor '%s' no existe" % name)
        raw = self._read_u16(name)
        self.raw_values[name] = raw
        self.scaled_values[name] = self._scale_value(name, raw)
        return self.scaled_values[name]

    def get_raw(self, name):
        return self.raw_values.get(name, 0)

    def get_percentage(self, name):
        raw = self.raw_values.get(name, 0)
        return round((raw / 65535.0) * 100, 1)

    def calibrate(self, name, min_val, max_val):
        if name in self.scales:
            self.scales[name]['min'] = min_val
            self.scales[name]['max'] = max_val

    def get_summary(self):
        self.read_all()
        lines = []
        lines.append("╔════════════════════════════════════════╗")
        lines.append("║      SENSORES DE VUELO - ESTADO       ║")
        lines.append("╠════════════════════════════════════════╣")
        label_map = {
            'altitude': 'Altitud',
            'speed': 'Velocidad',
            'attitude': 'Actitud',
            'light': 'Luz/Temp'
        }
        for name, value in self.scaled_values.items():
            unit = self.scales[name]['unit']
            pct = self.get_percentage(name)
            bar_width = 10
            filled = int((pct / 100.0) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            label = label_map.get(name, name).ljust(12)
            value_str = f"{value:7.1f} {unit:4s}".rjust(12)
            lines.append(f"║ {label} {value_str} [{bar}] {pct:5.1f}% ║")
        lines.append("╚════════════════════════════════════════╝")
        return "\n".join(lines)

    def deinit(self):
        # No deinit para ADC en RP2040
        pass
