"""
Práctica 5 — BMP280 Digital Sensor (ESP32 + MicroPython)
main.py: Lectura I2C de sensor barométrico/temperatura BMP280

BMP280: Sensor digital de presión y temperatura de Bosch Sensortec
- Interfaz: I2C (dirección 0x76 o 0x77) / SPI
- Presión: 300–1100 hPa (≈30–110 kPa)
- Temperatura: -40 a +85°C
- Compensación interna: Calibración de fábrica en registros
- Aplicaciones: Altimetría, meteorología, navegación

Este driver implementa lectura I2C básica con compensación de temperatura/presión.
"""

# ============================================================================
# Imports & Polyfills
# ============================================================================
try:
    from machine import I2C, Pin
    import utime as time
    import uselect
    import ujson as json
    import sys
    import ustruct as struct
    MICROPYTHON = True
except ImportError:
    # Polyfills para análisis fuera de la placa
    print("[PC Mode] Usando polyfills para análisis estático.")
    MICROPYTHON = False
    
    class I2C:
        def __init__(self, scl, sda, freq): pass
        def scan(self): return [0x76]
        def readfrom_mem(self, addr, reg, n): return bytes([0]*n)
        def writeto_mem(self, addr, reg, data): pass
    
    class Pin:
        IN = 1
        OUT = 2
        def __init__(self, pin, mode=None): pass
    
    class time:
        @staticmethod
        def sleep_ms(ms): pass
        @staticmethod
        def ticks_ms(): return 0
        @staticmethod
        def ticks_diff(a, b): return 0
    
    class uselect:
        POLLIN = 1
        @staticmethod
        def poll(): return _FakePoll()
    
    class _FakePoll:
        def register(self, stream, mode): pass
        def poll(self, timeout): return []
    
    class struct:
        @staticmethod
        def unpack(fmt, data): return (0,) * len(fmt.replace('<', '').replace('>', ''))
    
    import json
    import sys

import math

# ============================================================================
# Configuración de hardware I2C
# ============================================================================
I2C_SCL_PIN = 22           # GPIO22 (SCL por defecto ESP32)
I2C_SDA_PIN = 21           # GPIO21 (SDA por defecto ESP32)
I2C_FREQ = 400000          # 400 kHz (Fast Mode I2C)

BMP280_I2C_ADDR = 0x76     # Dirección I2C por defecto (0x76 o 0x77)
SAMPLE_RATE_MS = 500       # Periodo de muestreo (500ms → 2 Hz)

# Altitud de referencia para cálculo barométrico (ajustar según ubicación)
ALTITUDE_REF_M = 0.0       # Nivel del mar (0m), ajustar según altitud local

# ============================================================================
# Registros BMP280
# ============================================================================
BMP280_REG_CHIP_ID = 0xD0
BMP280_REG_RESET = 0xE0
BMP280_REG_STATUS = 0xF3
BMP280_REG_CTRL_MEAS = 0xF4
BMP280_REG_CONFIG = 0xF5
BMP280_REG_PRESS_MSB = 0xF7
BMP280_REG_TEMP_MSB = 0xFA

# Calibración (0x88–0xA1)
BMP280_REG_CALIB_START = 0x88

# Chip ID esperado
BMP280_CHIP_ID = 0x58

# Modos de operación
BMP280_MODE_SLEEP = 0x00
BMP280_MODE_FORCED = 0x01
BMP280_MODE_NORMAL = 0x03

# Oversampling
BMP280_OSRS_SKIP = 0x00
BMP280_OSRS_1 = 0x01
BMP280_OSRS_2 = 0x02
BMP280_OSRS_4 = 0x03
BMP280_OSRS_8 = 0x04
BMP280_OSRS_16 = 0x05

# ============================================================================
# Driver BMP280
# ============================================================================
class BMP280:
    """Driver básico para sensor BMP280 por I2C."""
    
    def __init__(self, i2c, addr=BMP280_I2C_ADDR):
        """
        Inicializa el sensor BMP280.
        
        Args:
            i2c: Objeto machine.I2C configurado.
            addr: Dirección I2C del sensor (0x76 o 0x77).
        """
        self.i2c = i2c
        self.addr = addr
        
        # Verificar chip ID
        chip_id = self._read_reg(BMP280_REG_CHIP_ID, 1)[0]
        if chip_id != BMP280_CHIP_ID:
            raise RuntimeError(f"BMP280 no detectado (Chip ID: 0x{chip_id:02X}, esperado: 0x{BMP280_CHIP_ID:02X})")
        
        print(f"[BMP280] Detectado en dirección 0x{addr:02X} (Chip ID: 0x{chip_id:02X})")
        
        # Leer calibración de fábrica
        self._load_calibration()
        
        # Configurar sensor: oversampling x2 temp/press, modo normal
        self._configure(
            mode=BMP280_MODE_NORMAL,
            osrs_t=BMP280_OSRS_2,
            osrs_p=BMP280_OSRS_2
        )
    
    def _read_reg(self, reg, n):
        """Lee n bytes desde registro reg."""
        if not MICROPYTHON:
            return bytes([0] * n)
        return self.i2c.readfrom_mem(self.addr, reg, n)
    
    def _write_reg(self, reg, data):
        """Escribe data en registro reg."""
        if not MICROPYTHON:
            return
        if isinstance(data, int):
            data = bytes([data])
        self.i2c.writeto_mem(self.addr, reg, data)
    
    def _load_calibration(self):
        """Carga parámetros de calibración de fábrica (0x88–0xA1)."""
        calib = self._read_reg(BMP280_REG_CALIB_START, 24)
        
        # Desempaquetar coeficientes (ver datasheet BMP280, sección 3.11.2)
        self.dig_T1 = struct.unpack('<H', calib[0:2])[0]
        self.dig_T2 = struct.unpack('<h', calib[2:4])[0]
        self.dig_T3 = struct.unpack('<h', calib[4:6])[0]
        
        self.dig_P1 = struct.unpack('<H', calib[6:8])[0]
        self.dig_P2 = struct.unpack('<h', calib[8:10])[0]
        self.dig_P3 = struct.unpack('<h', calib[10:12])[0]
        self.dig_P4 = struct.unpack('<h', calib[12:14])[0]
        self.dig_P5 = struct.unpack('<h', calib[14:16])[0]
        self.dig_P6 = struct.unpack('<h', calib[16:18])[0]
        self.dig_P7 = struct.unpack('<h', calib[18:20])[0]
        self.dig_P8 = struct.unpack('<h', calib[20:22])[0]
        self.dig_P9 = struct.unpack('<h', calib[22:24])[0]
        
        print(f"[BMP280] Calibración cargada (dig_T1={self.dig_T1}, dig_P1={self.dig_P1})")
    
    def _configure(self, mode=BMP280_MODE_NORMAL, osrs_t=BMP280_OSRS_2, osrs_p=BMP280_OSRS_2):
        """
        Configura el sensor.
        
        Args:
            mode: Modo de operación (SLEEP/FORCED/NORMAL).
            osrs_t: Oversampling de temperatura.
            osrs_p: Oversampling de presión.
        """
        ctrl_meas = (osrs_t << 5) | (osrs_p << 2) | mode
        self._write_reg(BMP280_REG_CTRL_MEAS, ctrl_meas)
        
        # Config: standby 500ms, filter off, SPI off
        config = (0x04 << 5) | (0x00 << 2) | 0x00
        self._write_reg(BMP280_REG_CONFIG, config)
        
        print(f"[BMP280] Configurado (modo={mode}, osrs_t={osrs_t}, osrs_p={osrs_p})")
    
    def read_raw(self):
        """
        Lee valores ADC crudos de temperatura y presión.
        
        Returns:
            tuple: (adc_temp, adc_press)
        """
        # Leer 6 bytes: press_msb, press_lsb, press_xlsb, temp_msb, temp_lsb, temp_xlsb
        data = self._read_reg(BMP280_REG_PRESS_MSB, 6)
        
        adc_press = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        adc_temp = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        
        return adc_temp, adc_press
    
    def compensate_temperature(self, adc_t):
        """
        Compensa temperatura usando calibración (algoritmo de Bosch).
        
        Args:
            adc_t: Valor ADC de temperatura.
        
        Returns:
            tuple: (temp_celsius, t_fine) — t_fine se usa para compensar presión.
        """
        var1 = ((adc_t >> 3) - (self.dig_T1 << 1)) * self.dig_T2 >> 11
        var2 = (((adc_t >> 4) - self.dig_T1) * ((adc_t >> 4) - self.dig_T1) >> 12) * self.dig_T3 >> 14
        t_fine = var1 + var2
        temp = (t_fine * 5 + 128) >> 8
        return temp / 100.0, t_fine
    
    def compensate_pressure(self, adc_p, t_fine):
        """
        Compensa presión usando calibración (algoritmo de Bosch).
        
        Args:
            adc_p: Valor ADC de presión.
            t_fine: Parámetro t_fine calculado en compensate_temperature.
        
        Returns:
            float: Presión en Pa (Pascal).
        """
        var1 = t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12)
        var1 = ((1 << 47) + var1) * self.dig_P1 >> 33
        
        if var1 == 0:
            return 0.0  # Evitar división por cero
        
        p = 1048576 - adc_p
        p = (((p << 31) - var2) * 3125) // var1
        var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
        var2 = (self.dig_P8 * p) >> 19
        p = ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)
        
        return p / 256.0  # Presión en Pa
    
    def read(self):
        """
        Lee temperatura y presión compensadas.
        
        Returns:
            tuple: (temp_celsius, press_Pa)
        """
        adc_t, adc_p = self.read_raw()
        temp, t_fine = self.compensate_temperature(adc_t)
        press = self.compensate_pressure(adc_p, t_fine)
        return temp, press

# ============================================================================
# Inicialización de hardware
# ============================================================================
if MICROPYTHON:
    i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
    print(f"[I2C] Bus configurado (SCL=GPIO{I2C_SCL_PIN}, SDA=GPIO{I2C_SDA_PIN}, {I2C_FREQ}Hz)")
    
    # Escanear dispositivos I2C
    devices = i2c.scan()
    print(f"[I2C] Dispositivos detectados: {[hex(d) for d in devices]}")
    
    # Inicializar BMP280
    try:
        bmp = BMP280(i2c, addr=BMP280_I2C_ADDR)
    except RuntimeError as e:
        print(f"[Error] {e}")
        print("[Sugerencia] Verifica conexiones I2C y dirección (0x76 o 0x77)")
        bmp = None

# ============================================================================
# Utilidades
# ============================================================================
def pressure_to_altitude(press_Pa, press_sea_level_Pa=101325.0):
    """
    Calcula altitud usando fórmula barométrica internacional.
    
    Args:
        press_Pa: Presión medida (Pa).
        press_sea_level_Pa: Presión a nivel del mar (Pa, default 101325).
    
    Returns:
        float: Altitud estimada (metros).
    """
    return 44330.0 * (1.0 - (press_Pa / press_sea_level_Pa) ** 0.1903)

# ============================================================================
# Menú interactivo con timeout
# ============================================================================
def menu_select(timeout_s=6):
    """Muestra menú de modos y espera selección del usuario con timeout."""
    print("\n" + "="*50)
    print("MENÚ PRINCIPAL — Práctica 5: BMP280 (I2C)")
    print("="*50)
    print("1) Lectura ADC cruda (raw)")
    print("2) Temperatura compensada (°C)")
    print("3) Presión compensada (hPa / kPa)")
    print("4) Altitud estimada (m)")
    print("5) Monitor CSV continuo (T, P, Alt)")
    print("6) Información del sensor")
    print("q) Salir")
    print("="*50)
    print(f"Selecciona opción (timeout: {timeout_s}s): ", end="")
    
    if not MICROPYTHON:
        return "1"
    
    poll = uselect.poll()
    poll.register(sys.stdin, uselect.POLLIN)
    start = time.ticks_ms()
    
    while True:
        elapsed = time.ticks_diff(time.ticks_ms(), start) / 1000.0
        if elapsed >= timeout_s:
            print("\n[Timeout] Reintentando menú...")
            return None
        
        events = poll.poll(100)
        if events:
            line = sys.stdin.readline().strip()
            if line:
                return line
        time.sleep_ms(50)

def check_menu_break():
    """Verifica si el usuario escribió 'm' para regresar al menú."""
    if not MICROPYTHON:
        return False
    
    poll = uselect.poll()
    poll.register(sys.stdin, uselect.POLLIN)
    events = poll.poll(0)
    
    if events:
        line = sys.stdin.readline().strip().lower()
        if line == 'm':
            print("\n[Menú] Regresando al menú principal...")
            return True
    return False

# ============================================================================
# Modos de operación
# ============================================================================
def mode_raw_adc():
    """Modo 1: Lectura ADC cruda continua."""
    print("\n--- MODO 1: Lectura ADC cruda ---")
    print("Presiona 'm' + ENTER para regresar al menú.\n")
    
    if not bmp:
        print("[Error] Sensor no inicializado.")
        input("Presiona ENTER para regresar...")
        return
    
    while True:
        adc_t, adc_p = bmp.read_raw()
        print(f"ADC_TEMP: {adc_t:6d}  ADC_PRESS: {adc_p:6d}")
        
        if check_menu_break():
            break
        time.sleep_ms(SAMPLE_RATE_MS)

def mode_temperature():
    """Modo 2: Temperatura compensada (°C)."""
    print("\n--- MODO 2: Temperatura compensada ---")
    print("Presiona 'm' + ENTER para regresar al menú.\n")
    
    if not bmp:
        print("[Error] Sensor no inicializado.")
        input("Presiona ENTER para regresar...")
        return
    
    while True:
        temp, _ = bmp.read()
        print(f"Temperatura: {temp:.2f} °C")
        
        if check_menu_break():
            break
        time.sleep_ms(SAMPLE_RATE_MS)

def mode_pressure():
    """Modo 3: Presión compensada (hPa / kPa)."""
    print("\n--- MODO 3: Presión compensada ---")
    print("Presiona 'm' + ENTER para regresar al menú.\n")
    
    if not bmp:
        print("[Error] Sensor no inicializado.")
        input("Presiona ENTER para regresar...")
        return
    
    while True:
        _, press_Pa = bmp.read()
        press_hPa = press_Pa / 100.0
        press_kPa = press_Pa / 1000.0
        
        print(f"Presión: {press_hPa:.2f} hPa  ({press_kPa:.2f} kPa)")
        
        if check_menu_break():
            break
        time.sleep_ms(SAMPLE_RATE_MS)

def mode_altitude():
    """Modo 4: Altitud estimada (m)."""
    print("\n--- MODO 4: Altitud estimada ---")
    print(f"Referencia: nivel del mar ({ALTITUDE_REF_M:.1f} m)")
    print("Presiona 'm' + ENTER para regresar al menú.\n")
    
    if not bmp:
        print("[Error] Sensor no inicializado.")
        input("Presiona ENTER para regresar...")
        return
    
    while True:
        temp, press_Pa = bmp.read()
        altitude = pressure_to_altitude(press_Pa)
        
        print(f"Altitud: {altitude:.1f} m  (T: {temp:.2f}°C, P: {press_Pa/100:.2f} hPa)")
        
        if check_menu_break():
            break
        time.sleep_ms(SAMPLE_RATE_MS)

def mode_csv_monitor():
    """Modo 5: Monitor CSV continuo para visualización externa."""
    print("\n--- MODO 5: Monitor CSV continuo ---")
    print("Formato: timestamp_ms,temp_C,press_hPa,press_kPa,altitude_m")
    print("Presiona 'm' + ENTER para detener.\n")
    
    if not bmp:
        print("[Error] Sensor no inicializado.")
        input("Presiona ENTER para regresar...")
        return
    
    # Header CSV
    print("timestamp_ms,temp_C,press_hPa,press_kPa,altitude_m")
    
    start_t = time.ticks_ms()
    while True:
        t = time.ticks_diff(time.ticks_ms(), start_t)
        temp, press_Pa = bmp.read()
        press_hPa = press_Pa / 100.0
        press_kPa = press_Pa / 1000.0
        altitude = pressure_to_altitude(press_Pa)
        
        print(f"{t},{temp:.2f},{press_hPa:.2f},{press_kPa:.2f},{altitude:.1f}")
        
        if check_menu_break():
            break
        time.sleep_ms(SAMPLE_RATE_MS)

def mode_sensor_info():
    """Modo 6: Información del sensor."""
    print("\n--- MODO 6: Información del sensor ---")
    
    if not bmp:
        print("[Error] Sensor no inicializado.")
        input("Presiona ENTER para regresar...")
        return
    
    print(f"\nSensor: BMP280 (Bosch Sensortec)")
    print(f"Dirección I2C: 0x{bmp.addr:02X}")
    print(f"Chip ID: 0x{BMP280_CHIP_ID:02X}")
    print(f"\nCoeficientes de calibración:")
    print(f"  dig_T1: {bmp.dig_T1}  dig_T2: {bmp.dig_T2}  dig_T3: {bmp.dig_T3}")
    print(f"  dig_P1: {bmp.dig_P1}  dig_P2: {bmp.dig_P2}  dig_P3: {bmp.dig_P3}")
    print(f"  dig_P4: {bmp.dig_P4}  dig_P5: {bmp.dig_P5}  dig_P6: {bmp.dig_P6}")
    print(f"  dig_P7: {bmp.dig_P7}  dig_P8: {bmp.dig_P8}  dig_P9: {bmp.dig_P9}")
    print(f"\nConfigu ración I2C:")
    print(f"  SCL: GPIO{I2C_SCL_PIN}  SDA: GPIO{I2C_SDA_PIN}")
    print(f"  Frecuencia: {I2C_FREQ} Hz")
    
    input("\nPresiona ENTER para regresar al menú...")

# ============================================================================
# Main loop
# ============================================================================
def main():
    """Bucle principal con menú interactivo."""
    print("\n" + "="*60)
    print("Práctica 5 — BMP280 Digital Sensor (I2C)")
    print("ESP32 + MicroPython")
    print("="*60)
    print(f"I2C: SCL=GPIO{I2C_SCL_PIN}, SDA=GPIO{I2C_SDA_PIN}, {I2C_FREQ}Hz")
    print(f"Sensor: BMP280 (0x{BMP280_I2C_ADDR:02X})")
    print("="*60)
    
    if not bmp:
        print("\n[Error crítico] BMP280 no detectado. Saliendo...")
        return
    
    while True:
        choice = menu_select(timeout_s=6)
        
        if choice is None:
            continue
        
        if choice == '1':
            mode_raw_adc()
        elif choice == '2':
            mode_temperature()
        elif choice == '3':
            mode_pressure()
        elif choice == '4':
            mode_altitude()
        elif choice == '5':
            mode_csv_monitor()
        elif choice == '6':
            mode_sensor_info()
        elif choice.lower() == 'q':
            print("\n[Salida] Programa terminado.")
            break
        else:
            print(f"\n[Opción inválida] '{choice}' no reconocida. Intenta de nuevo.")

if __name__ == "__main__":
    main()
