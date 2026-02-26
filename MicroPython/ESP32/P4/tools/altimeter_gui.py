#!/usr/bin/env python3
"""
altimeter_gui.py — Altímetro barométrico estilo aeronáutico para BMP180

Visualización tipo instrumento de avión con:
  • Carátula circular con aguja giratoria (0–1000 m por revolución)
  • Ventana de Kollsman (QNH en hPa)
  • Lecturas digitales: altitud, temperatura, presión
  • Gráfica de altitud vs tiempo (strip chart)
  • Grabación de datos a CSV

Lee datos CSV del puerto serie (Modo 4 de Práctica 4).
Formato esperado: timestamp_ms,temp_C,pressure_hPa,altitude_m

Uso:
    python altimeter_gui.py --port COM5
    python altimeter_gui.py --port /dev/ttyUSB0 --save flight.csv
    python altimeter_gui.py --port COM5 --unit ft

Dependencias:
    pip install pyserial

Autor: SISELA-Init
Licencia: MIT
"""

import argparse
import math
import sys
import time
import threading
from collections import deque

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
except ImportError:
    print("[Error] tkinter no disponible. Instala Python con soporte Tk.")
    sys.exit(1)

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("[Error] pyserial no instalado. Ejecuta: pip install pyserial")
    sys.exit(1)


# ============================================================================
# Constantes
# ============================================================================
GAUGE_SIZE    = 340      # Tamaño del canvas del altímetro
CHART_HEIGHT  = 160      # Altura del strip chart
UPDATE_MS     = 80       # Intervalo de redibujado (ms)
MAX_POINTS    = 600      # ~2 min a 5 Hz
M_PER_REV     = 1000     # Metros por revolución de aguja


# ============================================================================
# Altimeter Gauge Widget
# ============================================================================
class AltimeterGauge(tk.Canvas):
    """Carátula de altímetro estilo aeronáutico."""

    def __init__(self, parent, size=GAUGE_SIZE, **kw):
        super().__init__(parent, width=size, height=size, bg='#0d0d1a',
                         highlightthickness=0, **kw)
        self.size = size
        self.cx = size // 2
        self.cy = size // 2
        self.r = int(size * 0.44)       # Radio principal
        self.altitude_m = 0.0
        self.qnh_hpa = 1013.25
        self._draw_face()

    def _angle_for_value(self, value, max_val=10):
        """Convierte valor (0–max_val) a ángulo en radianes (0=top, CW)."""
        frac = (value % max_val) / max_val
        return math.radians(90 - frac * 360)

    def _draw_face(self):
        """Dibuja fondo estático del altímetro."""
        cx, cy, r = self.cx, self.cy, self.r

        # Fondo circular
        self.create_oval(cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10,
                         fill='#1a1a2e', outline='#444', width=2)
        self.create_oval(cx - r, cy - r, cx + r, cy + r,
                         fill='#111122', outline='#666', width=1)

        # Marcas mayores (0–9) y menores
        for i in range(100):
            angle = self._angle_for_value(i, 100)
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)

            if i % 10 == 0:
                # Marca mayor
                r1, r2 = r - 25, r - 5
                self.create_line(cx + r1 * cos_a, cy - r1 * sin_a,
                                 cx + r2 * cos_a, cy - r2 * sin_a,
                                 fill='white', width=2)
                # Número
                rn = r - 38
                num = (i // 10) % 10
                self.create_text(cx + rn * cos_a, cy - rn * sin_a,
                                 text=str(num), fill='white',
                                 font=('Consolas', 16, 'bold'))
            elif i % 5 == 0:
                # Marca intermedia
                r1, r2 = r - 18, r - 5
                self.create_line(cx + r1 * cos_a, cy - r1 * sin_a,
                                 cx + r2 * cos_a, cy - r2 * sin_a,
                                 fill='#aaa', width=1)
            else:
                # Marca menor
                r1, r2 = r - 12, r - 5
                self.create_line(cx + r1 * cos_a, cy - r1 * sin_a,
                                 cx + r2 * cos_a, cy - r2 * sin_a,
                                 fill='#666', width=1)

        # Etiquetas "×100 m"
        self.create_text(cx, cy + r * 0.55, text="×100 m",
                         fill='#888', font=('Calibri', 9))

        # Ventana de Kollsman (QNH)
        kw, kh = 70, 22
        kx = cx + r * 0.42
        ky = cy
        self.create_rectangle(kx - kw // 2, ky - kh // 2,
                              kx + kw // 2, ky + kh // 2,
                              fill='#0a0a15', outline='#888', width=1)
        self._qnh_text = self.create_text(kx, ky, text="1013.3",
                                          fill='#00ff88', font=('Consolas', 10))

        # Huella central
        self.create_oval(cx - 8, cy - 8, cx + 8, cy + 8,
                         fill='#333', outline='#888')

        # ID de la aguja (se crea vacía, se actualiza en update)
        self._needle = None

        # Texto digital de altitud
        self._alt_text = self.create_text(cx, cy - r * 0.2,
                                          text="---", fill='#00ff88',
                                          font=('Consolas', 22, 'bold'))

    def update_altitude(self, alt_m, qnh=None):
        """Actualiza aguja y displays."""
        self.altitude_m = alt_m
        if qnh is not None:
            self.qnh_hpa = qnh

        cx, cy, r = self.cx, self.cy, self.r

        # Aguja
        angle = self._angle_for_value(alt_m / (M_PER_REV / 10), 10)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        needle_len = r - 48
        tail_len = 18
        nx = cx + needle_len * cos_a
        ny = cy - needle_len * sin_a
        tx = cx - tail_len * cos_a
        ty = cy + tail_len * sin_a

        if self._needle:
            self.delete(self._needle)
        self._needle = self.create_line(tx, ty, nx, ny,
                                        fill='#ff3333', width=3,
                                        arrow=tk.LAST, arrowshape=(12, 15, 5))

        # Hub
        self.create_oval(cx - 6, cy - 6, cx + 6, cy + 6,
                         fill='#ff3333', outline='#ff3333')

        # Digital
        self.itemconfigure(self._alt_text, text=f"{alt_m:.0f} m")

        # Kollsman
        self.itemconfigure(self._qnh_text, text=f"{self.qnh_hpa:.1f}")


# ============================================================================
# Strip Chart Widget
# ============================================================================
class StripChart(tk.Canvas):
    """Gráfica de altitud vs tiempo."""

    def __init__(self, parent, width=600, height=CHART_HEIGHT, **kw):
        super().__init__(parent, width=width, height=height,
                         bg='#0d0d1a', highlightthickness=0, **kw)
        self.w = width
        self.h = height
        self.margin = {'l': 55, 'r': 10, 't': 10, 'b': 25}
        self.data = deque(maxlen=MAX_POINTS)

    def add_point(self, t_sec, alt_m):
        self.data.append((t_sec, alt_m))

    def redraw(self):
        self.delete('all')
        if len(self.data) < 2:
            self.create_text(self.w // 2, self.h // 2,
                             text="Esperando datos...",
                             fill='#444', font=('Calibri', 11))
            return

        ml, mr, mt, mb = self.margin['l'], self.margin['r'], self.margin['t'], self.margin['b']
        pw = self.w - ml - mr
        ph = self.h - mt - mb

        times = [d[0] for d in self.data]
        alts  = [d[1] for d in self.data]
        t_min, t_max = times[0], times[-1]
        if t_max == t_min:
            t_max = t_min + 1

        a_min = min(alts) - 2
        a_max = max(alts) + 2
        if a_max == a_min:
            a_max = a_min + 10

        # Grid
        for i in range(5):
            y = mt + ph * i / 4
            self.create_line(ml, y, ml + pw, y, fill='#222', dash=(2, 4))
            val = a_max - (a_max - a_min) * i / 4
            self.create_text(ml - 5, y, text=f"{val:.0f}",
                             fill='#666', font=('Consolas', 8), anchor='e')

        # Axes
        self.create_line(ml, mt, ml, mt + ph, fill='#555')
        self.create_line(ml, mt + ph, ml + pw, mt + ph, fill='#555')

        # Time labels
        for i in range(5):
            x = ml + pw * i / 4
            val = t_min + (t_max - t_min) * i / 4
            self.create_text(x, mt + ph + 12, text=f"{val:.0f}s",
                             fill='#666', font=('Consolas', 8))

        # Data line
        points = []
        for t, a in self.data:
            x = ml + (t - t_min) / (t_max - t_min) * pw
            y = mt + (a_max - a) / (a_max - a_min) * ph
            points.append(x)
            points.append(y)

        if len(points) >= 4:
            self.create_line(points, fill='#00cc66', width=2, smooth=True)

        # Y-axis label
        self.create_text(12, self.h // 2, text="Alt (m)",
                         fill='#888', font=('Calibri', 9), angle=90)


# ============================================================================
# Main Application
# ============================================================================
class AltimeterApp(tk.Tk):
    """Aplicación principal del altímetro."""

    def __init__(self, port, baud=115200, save_file=None, unit='m',
                 auto_start=True, menu_choice='4', no_reset=False):
        super().__init__()
        self.title("BMP180 — Altímetro Barométrico Aeronáutico")
        self.configure(bg='#0d0d1a')
        self.resizable(False, False)

        self.port = port
        self.baud = baud
        self.save_file = save_file
        self.unit = unit
        self.auto_start = auto_start
        self.menu_choice = str(menu_choice)
        self.no_reset = no_reset

        self.ser = None
        self.csv_file = None
        self.running = False
        self.header_received = False
        self.start_time = None

        # Data
        self.temp_c = 0.0
        self.pressure_hpa = 1013.25
        self.altitude_m = 0.0
        self.data_count = 0

        self._build_ui()
        self._start_serial()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(UPDATE_MS, self._update_loop)

    def _build_ui(self):
        """Construye toda la interfaz."""
        main = tk.Frame(self, bg='#0d0d1a')
        main.pack(padx=10, pady=10)

        # --- Fila superior: gauge + panel derecho ---
        top = tk.Frame(main, bg='#0d0d1a')
        top.pack(fill='x')

        # Altimeter gauge
        self.gauge = AltimeterGauge(top, size=GAUGE_SIZE)
        self.gauge.pack(side='left', padx=(0, 15))

        # Panel derecho
        right = tk.Frame(top, bg='#0d0d1a', width=260)
        right.pack(side='left', fill='y')

        # Digital displays
        style = {'bg': '#0d0d1a', 'fg': '#00ff88', 'font': ('Consolas', 14),
                 'anchor': 'w'}
        lbl_style = {'bg': '#0d0d1a', 'fg': '#888', 'font': ('Calibri', 10),
                     'anchor': 'w'}

        tk.Label(right, text="ALTITUD", **lbl_style).pack(anchor='w', pady=(10, 0))
        self.lbl_alt = tk.Label(right, text="--- m", **style)
        self.lbl_alt.pack(anchor='w')
        self.lbl_alt_ft = tk.Label(right, text="--- ft",
                                   bg='#0d0d1a', fg='#008855',
                                   font=('Consolas', 11), anchor='w')
        self.lbl_alt_ft.pack(anchor='w')

        tk.Label(right, text="PRESIÓN", **lbl_style).pack(anchor='w', pady=(12, 0))
        self.lbl_pres = tk.Label(right, text="--- hPa", **style)
        self.lbl_pres.pack(anchor='w')

        tk.Label(right, text="TEMPERATURA", **lbl_style).pack(anchor='w', pady=(12, 0))
        self.lbl_temp = tk.Label(right, text="--- °C", **style)
        self.lbl_temp.pack(anchor='w')

        # QNH slider
        tk.Label(right, text="QNH (hPa)", **lbl_style).pack(anchor='w', pady=(15, 0))
        self.qnh_var = tk.DoubleVar(value=1013.25)
        self.qnh_scale = tk.Scale(right, from_=980, to=1050, resolution=0.1,
                                  orient='horizontal', variable=self.qnh_var,
                                  bg='#1a1a2e', fg='#00ff88',
                                  troughcolor='#333', highlightthickness=0,
                                  font=('Consolas', 9), length=230)
        self.qnh_scale.pack(anchor='w')

        # Buttons
        btn_frame = tk.Frame(right, bg='#0d0d1a')
        btn_frame.pack(anchor='w', pady=(15, 0))

        btn_style = {'bg': '#1a3a2a', 'fg': '#00ff88',
                     'font': ('Calibri', 10), 'relief': 'flat',
                     'activebackground': '#2a5a3a', 'activeforeground': '#00ff88'}

        self.btn_csv = tk.Button(btn_frame, text="💾 Guardar CSV",
                                 command=self._toggle_csv, **btn_style)
        self.btn_csv.pack(side='left', padx=(0, 8))

        tk.Button(btn_frame, text="📷 Captura",
                  command=self._save_snapshot, **btn_style).pack(side='left')

        # Status
        self.lbl_status = tk.Label(right, text="Conectando...",
                                   bg='#0d0d1a', fg='#666',
                                   font=('Calibri', 9), anchor='w')
        self.lbl_status.pack(anchor='w', pady=(10, 0))

        # --- Strip chart ---
        chart_w = GAUGE_SIZE + 260 + 15
        self.chart = StripChart(main, width=chart_w, height=CHART_HEIGHT)
        self.chart.pack(fill='x', pady=(10, 0))

        # --- Status bar ---
        status_bar = tk.Frame(main, bg='#111122')
        status_bar.pack(fill='x', pady=(8, 0))
        self.lbl_port = tk.Label(status_bar,
                                 text=f"Puerto: {self.port} @ {self.baud}",
                                 bg='#111122', fg='#666',
                                 font=('Consolas', 9))
        self.lbl_port.pack(side='left', padx=8)
        self.lbl_count = tk.Label(status_bar, text="Datos: 0",
                                  bg='#111122', fg='#666',
                                  font=('Consolas', 9))
        self.lbl_count.pack(side='right', padx=8)

    # ----------------------------------------------------------------
    # Serial
    # ----------------------------------------------------------------
    def _start_serial(self):
        """Abre puerto serie y lanza thread de lectura."""
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.5)
            if self.no_reset:
                try:
                    self.ser.dtr = False
                    self.ser.rts = False
                except Exception:
                    pass

            time.sleep(2)
            try:
                self.ser.reset_input_buffer()
            except Exception:
                pass

            if self.auto_start:
                self._enter_csv_mode()

            self.running = True
            self.lbl_status.config(text="Conectado", fg='#00ff88')

            thread = threading.Thread(target=self._serial_reader, daemon=True)
            thread.start()

        except serial.SerialException as e:
            self.lbl_status.config(text=f"Error: {e}", fg='#ff4444')

    def _enter_csv_mode(self):
        """Envía selección de menú para entrar al modo CSV."""
        try:
            for _ in range(2):
                self.ser.write(b"\r\n")
                self.ser.flush()
                time.sleep(0.1)
            cmd = (self.menu_choice + "\r\n").encode()
            for _ in range(3):
                self.ser.write(cmd)
                self.ser.flush()
                time.sleep(0.3)
        except Exception:
            pass

    def _serial_reader(self):
        """Thread de lectura serial (background)."""
        while self.running and self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if not line or line.startswith('[') or line.startswith('=') or line.startswith('-'):
                        continue
                    if not self.header_received:
                        if 'timestamp' in line.lower() and 'altitude' in line.lower():
                            self.header_received = True
                            if self.csv_file:
                                self.csv_file.write(line + '\n')
                        continue

                    parts = line.split(',')
                    if len(parts) == 4:
                        try:
                            ts_ms  = int(parts[0])
                            temp   = float(parts[1])
                            pres   = float(parts[2])
                            alt    = float(parts[3])

                            self.temp_c = temp
                            self.pressure_hpa = pres
                            self.altitude_m = alt
                            self.data_count += 1

                            if self.start_time is None:
                                self.start_time = ts_ms
                            t_sec = (ts_ms - self.start_time) / 1000.0
                            self.chart.add_point(t_sec, alt)

                            if self.csv_file:
                                self.csv_file.write(line + '\n')
                                self.csv_file.flush()
                        except (ValueError, IndexError):
                            pass
                else:
                    time.sleep(0.02)
            except Exception:
                time.sleep(0.1)

    # ----------------------------------------------------------------
    # Update loop
    # ----------------------------------------------------------------
    def _update_loop(self):
        """Redibuja GUI periódicamente."""
        alt = self.altitude_m
        alt_ft = alt * 3.28084

        self.gauge.update_altitude(alt, qnh=self.qnh_var.get())

        self.lbl_alt.config(text=f"{alt:.1f} m")
        self.lbl_alt_ft.config(text=f"{alt_ft:.0f} ft")
        self.lbl_pres.config(text=f"{self.pressure_hpa:.2f} hPa")
        self.lbl_temp.config(text=f"{self.temp_c:.1f} °C")
        self.lbl_count.config(text=f"Datos: {self.data_count}")

        self.chart.redraw()
        self.after(UPDATE_MS, self._update_loop)

    # ----------------------------------------------------------------
    # CSV
    # ----------------------------------------------------------------
    def _toggle_csv(self):
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            self.btn_csv.config(text="💾 Guardar CSV")
            self.lbl_status.config(text="CSV detenido", fg='#ffaa00')
        else:
            path = self.save_file
            if not path:
                path = filedialog.asksaveasfilename(
                    defaultextension='.csv',
                    filetypes=[('CSV', '*.csv')],
                    initialfile=f'bmp180_{int(time.time())}.csv')
            if path:
                try:
                    self.csv_file = open(path, 'w', encoding='utf-8')
                    self.csv_file.write("timestamp_ms,temp_C,pressure_hPa,altitude_m\n")
                    self.btn_csv.config(text="⏹ Detener CSV")
                    self.lbl_status.config(text=f"Grabando: {path}", fg='#00ff88')
                except IOError as e:
                    self.lbl_status.config(text=f"Error CSV: {e}", fg='#ff4444')

    def _save_snapshot(self):
        """Guarda captura instantánea en un archivo de texto."""
        ts = time.strftime('%Y-%m-%d %H:%M:%S')
        snap = (f"=== BMP180 Snapshot ===\n"
                f"Fecha/Hora: {ts}\n"
                f"Temperatura: {self.temp_c:.1f} °C\n"
                f"Presión: {self.pressure_hpa:.2f} hPa\n"
                f"Altitud: {self.altitude_m:.1f} m ({self.altitude_m * 3.28084:.0f} ft)\n"
                f"QNH: {self.qnh_var.get():.1f} hPa\n"
                f"Datos recibidos: {self.data_count}\n")
        path = filedialog.asksaveasfilename(
            defaultextension='.txt',
            filetypes=[('Text', '*.txt')],
            initialfile=f'snapshot_{int(time.time())}.txt')
        if path:
            with open(path, 'w') as f:
                f.write(snap)
            self.lbl_status.config(text=f"Snapshot: {path}", fg='#00ff88')

    # ----------------------------------------------------------------
    # Cleanup
    # ----------------------------------------------------------------
    def _on_close(self):
        self.running = False
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(b"m\r\n")
                self.ser.flush()
                time.sleep(0.1)
            except Exception:
                pass
            self.ser.close()
        if self.csv_file:
            self.csv_file.close()
        self.destroy()


# ============================================================================
# Auto-detect port
# ============================================================================
def autodetect_port():
    """Detecta automáticamente puerto serie."""
    ports = serial.tools.list_ports.comports()
    for p in ports:
        desc = p.description.lower()
        if any(k in desc for k in ('cp210', 'ch340', 'uart', 'usb')):
            return p.device
    if ports:
        return ports[0].device
    return None


# ============================================================================
# CLI
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Altímetro barométrico BMP180 — Visualización aeronáutica (Práctica 4)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python altimeter_gui.py --port COM5
  python altimeter_gui.py --port /dev/ttyUSB0 --save datos.csv
  python altimeter_gui.py --port COM5 --no-auto-start
        """)

    parser.add_argument('--port', type=str, default=None,
                        help='Puerto serie (ej: COM5, /dev/ttyUSB0). Autodetecta si omitido.')
    parser.add_argument('--baud', type=int, default=115200,
                        help='Velocidad (default: 115200)')
    parser.add_argument('--save', type=str, default=None,
                        help='Archivo CSV para guardar datos')
    parser.add_argument('--unit', type=str, default='m', choices=['m', 'ft'],
                        help='Unidad de altitud (default: m)')
    parser.add_argument('--auto-start', action='store_true', default=True,
                        help='Entrar automáticamente al modo CSV (default: True)')
    parser.add_argument('--no-auto-start', dest='auto_start', action='store_false')
    parser.add_argument('--menu-choice', type=str, default='4',
                        help='Opción de menú a enviar (default: 4)')
    parser.add_argument('--no-reset', action='store_true',
                        help='Evitar reset DTR/RTS al conectar')

    args = parser.parse_args()

    port = args.port
    if port is None:
        port = autodetect_port()
        if port:
            print(f"[Autodetección] Puerto: {port}")
        else:
            print("[Error] No se detectó puerto serie. Usa --port COM5")
            sys.exit(1)

    app = AltimeterApp(
        port=port,
        baud=args.baud,
        save_file=args.save,
        unit=args.unit,
        auto_start=args.auto_start,
        menu_choice=args.menu_choice,
        no_reset=args.no_reset
    )
    app.mainloop()


if __name__ == '__main__':
    main()
