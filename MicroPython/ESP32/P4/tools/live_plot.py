#!/usr/bin/env python3
"""
live_plot.py — Visualización en tiempo real de datos del MPX5500DP

Lee datos CSV del puerto serie (Modo 4 de Práctica 4) y grafica presión vs tiempo.

Uso:
    python live_plot.py --port COM5 --baud 115200 --window 30
    python live_plot.py --port /dev/ttyUSB0 --save data.csv

Dependencias:
    pip install pyserial matplotlib numpy

Autor: SISELA-Init
Licencia: MIT
"""

import argparse
import sys
import time
from collections import deque

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("[Error] pyserial no instalado. Ejecuta: pip install pyserial")
    sys.exit(1)

try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
except ImportError:
    print("[Error] matplotlib no instalado. Ejecuta: pip install matplotlib")
    sys.exit(1)

import numpy as np


class PressurePlotter:
    """Graficador en tiempo real de datos de presión."""
    
    def __init__(self, port, baudrate=115200, window_size=30, save_file=None):
        """
        Inicializa el graficador.
        
        Args:
            port (str): Puerto serie (ej: 'COM5', '/dev/ttyUSB0').
            baudrate (int): Velocidad de comunicación.
            window_size (int): Ventana de tiempo en segundos.
            save_file (str|None): Archivo CSV para guardar datos (opcional).
        """
        self.port = port
        self.baudrate = baudrate
        self.window_size = window_size
        self.save_file = save_file
        
        # Buffers de datos (deque con tamaño fijo)
        self.max_points = window_size * 10  # Asume 10 Hz
        self.times = deque(maxlen=self.max_points)
        self.pressures = deque(maxlen=self.max_points)
        self.voltages = deque(maxlen=self.max_points)
        
        # Puerto serie
        self.ser = None
        self.csv_file = None
        self.start_time = None
        self.header_received = False
        
    def open_serial(self):
        """Abre el puerto serie."""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"[OK] Conectado a {self.port} @ {self.baudrate} baud")
            time.sleep(2)  # Espera estabilización
            return True
        except serial.SerialException as e:
            print(f"[Error] No se pudo abrir {self.port}: {e}")
            return False
    
    def open_csv_file(self):
        """Abre archivo CSV para guardar datos (si save_file está definido)."""
        if self.save_file:
            try:
                self.csv_file = open(self.save_file, 'w', encoding='utf-8')
                print(f"[OK] Guardando datos en {self.save_file}")
            except IOError as e:
                print(f"[Advertencia] No se pudo crear {self.save_file}: {e}")
                self.csv_file = None
    
    def read_line(self):
        """
        Lee una línea del puerto serie y parsea CSV.
        
        Returns:
            tuple|None: (timestamp_ms, adc_raw, voltage_V, pressure_kPa) o None si error.
        """
        try:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                
                # Ignorar líneas vacías o mensajes de debug
                if not line or line.startswith('[') or line.startswith('='):
                    return None
                
                # Primera línea es header CSV
                if not self.header_received:
                    if 'timestamp' in line.lower() and 'pressure' in line.lower():
                        print(f"[Header] {line}")
                        self.header_received = True
                        if self.csv_file:
                            self.csv_file.write(line + '\n')
                    return None
                
                # Parsear CSV: timestamp_ms,adc_raw,voltage_V,pressure_kPa
                parts = line.split(',')
                if len(parts) == 4:
                    timestamp_ms = int(parts[0])
                    adc_raw = int(parts[1])
                    voltage = float(parts[2])
                    pressure = float(parts[3])
                    
                    # Guardar a archivo CSV si está habilitado
                    if self.csv_file:
                        self.csv_file.write(line + '\n')
                        self.csv_file.flush()
                    
                    return (timestamp_ms, adc_raw, voltage, pressure)
        except (ValueError, UnicodeDecodeError, IndexError) as e:
            print(f"[Parse Error] {e}: {line}")
        
        return None
    
    def update_plot(self, frame):
        """
        Callback de animación de matplotlib.
        
        Args:
            frame: Número de frame (no usado).
        """
        # Leer datos del puerto serie
        data = self.read_line()
        
        if data:
            timestamp_ms, adc_raw, voltage, pressure = data
            
            # Primera lectura: guardar tiempo de inicio
            if self.start_time is None:
                self.start_time = timestamp_ms
            
            # Convertir a tiempo relativo en segundos
            time_s = (timestamp_ms - self.start_time) / 1000.0
            
            # Agregar a buffers
            self.times.append(time_s)
            self.pressures.append(pressure)
            self.voltages.append(voltage)
            
            # Actualizar gráfica
            if len(self.times) > 1:
                self.ax1.clear()
                self.ax2.clear()
                
                # Gráfica 1: Presión (kPa)
                self.ax1.plot(list(self.times), list(self.pressures), 'b-', linewidth=1.5, label='Presión (kPa)')
                self.ax1.set_ylabel('Presión (kPa)', fontsize=12, color='b')
                self.ax1.tick_params(axis='y', labelcolor='b')
                self.ax1.grid(True, alpha=0.3)
                self.ax1.legend(loc='upper left')
                
                # Gráfica 2: Voltaje (V)
                self.ax2.plot(list(self.times), list(self.voltages), 'r-', linewidth=1.5, label='Voltaje (V)')
                self.ax2.set_xlabel('Tiempo (s)', fontsize=12)
                self.ax2.set_ylabel('Voltaje (V)', fontsize=12, color='r')
                self.ax2.tick_params(axis='y', labelcolor='r')
                self.ax2.grid(True, alpha=0.3)
                self.ax2.legend(loc='upper left')
                
                # Ajustar límites de tiempo (ventana deslizante)
                if time_s > self.window_size:
                    self.ax1.set_xlim(time_s - self.window_size, time_s)
                    self.ax2.set_xlim(time_s - self.window_size, time_s)
                else:
                    self.ax1.set_xlim(0, self.window_size)
                    self.ax2.set_xlim(0, self.window_size)
                
                # Título con último valor
                self.fig.suptitle(
                    f"MPX5500DP — Live Plot | Presión: {pressure:.2f} kPa | Voltaje: {voltage:.3f} V",
                    fontsize=14,
                    fontweight='bold'
                )
    
    def run(self):
        """Ejecuta el graficador en tiempo real."""
        if not self.open_serial():
            return
        
        self.open_csv_file()
        
        # Configurar figura de matplotlib
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        self.fig.suptitle("MPX5500DP — Live Plot", fontsize=14, fontweight='bold')
        
        # Animación
        ani = animation.FuncAnimation(
            self.fig,
            self.update_plot,
            interval=50,  # 50 ms → 20 FPS
            blit=False,
            cache_frame_data=False
        )
        
        print("\n[Graficando] Presiona Ctrl+C o cierra ventana para detener.\n")
        
        try:
            plt.tight_layout()
            plt.show()
        except KeyboardInterrupt:
            print("\n[Interrumpido] Cerrando...")
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()
            if self.csv_file:
                self.csv_file.close()
                print(f"[OK] Datos guardados en {self.save_file}")


def autodetect_port():
    """Detecta automáticamente puerto ESP32."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # Buscar descripciones típicas de ESP32
        desc = port.description.lower()
        if 'cp210' in desc or 'ch340' in desc or 'uart' in desc or 'usb' in desc:
            return port.device
    
    # Si no detecta, retornar primer puerto disponible
    if ports:
        return ports[0].device
    return None


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Visualizador en tiempo real de datos MPX5500DP (Práctica 4)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python live_plot.py --port COM5 --baud 115200
  python live_plot.py --port /dev/ttyUSB0 --window 60
  python live_plot.py --port COM5 --save presion_data.csv
        """
    )
    
    parser.add_argument(
        '--port',
        type=str,
        default=None,
        help='Puerto serie (ej: COM5, /dev/ttyUSB0). Si no se especifica, autodetecta.'
    )
    
    parser.add_argument(
        '--baud',
        type=int,
        default=115200,
        help='Velocidad de comunicación en baudios (default: 115200).'
    )
    
    parser.add_argument(
        '--window',
        type=int,
        default=30,
        help='Ventana de tiempo en segundos (default: 30).'
    )
    
    parser.add_argument(
        '--save',
        type=str,
        default=None,
        help='Guardar datos en archivo CSV (opcional).'
    )
    
    args = parser.parse_args()
    
    # Autodetectar puerto si no se especificó
    port = args.port
    if port is None:
        port = autodetect_port()
        if port:
            print(f"[Autodetección] Puerto detectado: {port}")
        else:
            print("[Error] No se detectó ningún puerto serie.")
            print("Especifica manualmente con --port")
            sys.exit(1)
    
    # Crear y ejecutar graficador
    plotter = PressurePlotter(
        port=port,
        baudrate=args.baud,
        window_size=args.window,
        save_file=args.save
    )
    
    plotter.run()


if __name__ == '__main__':
    main()
