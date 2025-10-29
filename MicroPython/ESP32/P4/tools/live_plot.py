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
    
    def __init__(self, port, baudrate=115200, window_size=30, save_file=None,
                 auto_start=False, menu_choice='4', stop_on_exit=False, no_reset=False):
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
        self.auto_start = auto_start
        self.menu_choice = str(menu_choice or '4')
        self.stop_on_exit = stop_on_exit
        self.no_reset = no_reset
        
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
            # Abrir puerto
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            # Opcional: intentar evitar resets por líneas de control
            try:
                if self.no_reset:
                    self.ser.dtr = False
                    self.ser.rts = False
            except Exception:
                pass
            print(f"[OK] Conectado a {self.port} @ {self.baudrate} baud")
            time.sleep(2)  # Espera estabilización
            # Limpia buffers
            try:
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()
            except Exception:
                pass

            # Intentar entrar al modo 4 (CSV) automáticamente
            if self.auto_start:
                self._try_enter_mode_csv()
            return True
        except serial.SerialException as e:
            print(f"[Error] No se pudo abrir {self.port}: {e}")
            return False

    def _try_enter_mode_csv(self):
        """Envía la selección de menú para entrar al modo CSV (opción '4')."""
        # Enviar algunos saltos de línea para sincronizar y luego la opción
        try:
            for _ in range(2):
                self.ser.write(b"\r\n")
                self.ser.flush()
                time.sleep(0.1)
            cmd = (self.menu_choice + "\r\n").encode()
            # Intento múltiple por si el programa está en timeout/reimpresión de menú
            for _ in range(3):
                self.ser.write(cmd)
                self.ser.flush()
                time.sleep(0.3)
        except Exception as e:
            print(f"[Aviso] No se pudo enviar selección de menú automáticamente: {e}")
    
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
            # Intentar salir del modo en el dispositivo
            if self.stop_on_exit and self.ser:
                try:
                    self.ser.write(b"m\r\n")
                    self.ser.flush()
                    time.sleep(0.1)
                except Exception:
                    pass
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
  python live_plot.py --no-auto-start  # Desactivar auto-inicio si ya estás en modo 4

Por defecto, el script entra automáticamente al modo 4 (CSV) del programa 
en el ESP32 y regresa al menú al salir.
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
    parser.add_argument(
        '--auto-start',
        action='store_true',
        default=True,
        help='Intentar entrar automáticamente al modo 4 (CSV) del programa principal al conectar (default: True).'
    )
    parser.add_argument(
        '--no-auto-start',
        dest='auto_start',
        action='store_false',
        help='Desactivar entrada automática al modo 4; espera que ya estés en el modo correcto.'
    )
    parser.add_argument(
        '--menu-choice',
        type=str,
        default='4',
        help='Opción de menú a enviar al conectar cuando --auto-start está activo (default: 4).'
    )
    parser.add_argument(
        '--stop-on-exit',
        action='store_true',
        default=True,
        help="Enviar 'm' al salir para regresar al menú en el dispositivo (default: True)."
    )
    parser.add_argument(
        '--no-stop-on-exit',
        dest='stop_on_exit',
        action='store_false',
        help='No enviar comando de salida al cerrar.'
    )
    parser.add_argument(
        '--no-reset',
        action='store_true',
        help='Intenta evitar reset por DTR/RTS al abrir el puerto (establece DTR/RTS en False).'
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
        save_file=args.save,
        auto_start=args.auto_start,
        menu_choice=args.menu_choice,
        stop_on_exit=args.stop_on_exit,
        no_reset=args.no_reset
    )
    
    plotter.run()


if __name__ == '__main__':
    main()
