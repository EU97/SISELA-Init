"""
bmp180.py — Driver BMP180 para MicroPython (ESP32 / RP2040)

Sensor digital de presión barométrica y temperatura (Bosch BMP180).
Interfaz I2C, dirección por defecto 0x77.

Implementa el algoritmo de compensación completo según el datasheet:
  - 11 coeficientes de calibración leídos de EEPROM (0xAA–0xBF)
  - Compensación de temperatura (UT → °C)
  - Compensación de presión (UP → Pa) con soporte de sobremuestreo (oss 0–3)
  - Cálculo de altitud barométrica: h = 44330 × (1 − (P/P₀)^(1/5.255))

Referencia:
  Bosch BMP180 Datasheet, Rev 2.5, April 2013
  https://cdn-shop.adafruit.com/datasheets/BST-BMP180-DS000-09.pdf

Uso:
  from machine import I2C, Pin
  from bmp180 import BMP180

  i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=100000)
  sensor = BMP180(i2c)

  temp = sensor.temperature()          # °C
  pres = sensor.pressure()             # Pa
  alt  = sensor.altitude(p0=101325)    # m (ISA)
  T, P, h = sensor.read_all()          # lectura eficiente

Autor: SISELA-Init
Licencia: MIT
"""

# ============================================================================
# Sleep helper (compatible MicroPython y CPython)
# ============================================================================
try:
    import utime
    _sleep_ms = utime.sleep_ms
except (ImportError, AttributeError):
    import time as _time_mod
    def _sleep_ms(ms):
        _time_mod.sleep(ms / 1000.0)


class BMP180:
    """
    Driver para el sensor BMP180 (presión barométrica + temperatura).

    Especificaciones del sensor:
      - Rango de presión:    300 – 1100 hPa
      - Rango de temperatura: −40 – +85 °C
      - Interfaz:            I2C, hasta 3.4 MHz
      - Resolución máxima:   0.01 hPa (modo ultra-alta resolución)
      - Chip ID esperado:    0x55
    """

    # ---- Registros ----
    _REG_ID      = 0xD0    # Chip ID (debe ser 0x55)
    _REG_RESET   = 0xE0    # Soft reset (escribir 0xB6)
    _REG_CALIB   = 0xAA    # Inicio de calibración (22 bytes: 0xAA–0xBF)
    _REG_CTRL    = 0xF4    # Registro de control
    _REG_DATA    = 0xF6    # Data MSB (0xF6), LSB (0xF7), XLSB (0xF8)

    # ---- Comandos ----
    _CMD_TEMP    = 0x2E    # Iniciar medición de temperatura
    _CMD_PRES    = 0x34    # Iniciar medición de presión (+ oss << 6)

    # ---- Modos de sobremuestreo ----
    OSS_ULTRA_LOW  = 0     # 1 muestra,   4.5 ms, ±6.0 Pa RMS
    OSS_STANDARD   = 1     # 2 muestras,  7.5 ms, ±5.0 Pa RMS
    OSS_HIGH       = 2     # 4 muestras, 13.5 ms, ±4.0 Pa RMS
    OSS_ULTRA_HIGH = 3     # 8 muestras, 25.5 ms, ±3.0 Pa RMS

    _OSS_NAMES = ["Ultra Low Power", "Estándar", "Alta Resolución", "Ultra Alta Resolución"]
    _DELAYS_MS = [5, 8, 14, 26]     # Tiempo de espera por modo

    def __init__(self, i2c, addr=0x77, oss=OSS_STANDARD):
        """
        Inicializa el sensor BMP180.

        Args:
            i2c:  Objeto machine.I2C o machine.SoftI2C
            addr: Dirección I2C (por defecto 0x77)
            oss:  Modo de sobremuestreo (0–3, default 1 = Estándar)
        """
        self.i2c  = i2c
        self.addr = addr
        self.oss  = min(max(int(oss), 0), 3)

        # Verificar presencia en bus
        chip_id = self._read_byte(self._REG_ID)
        if chip_id != 0x55:
            raise OSError("BMP180 no detectado (ID=0x{:02X}, esperado 0x55)".format(chip_id))

        # Coeficientes de calibración (se llenan en _read_calibration)
        self.AC1 = 0; self.AC2 = 0; self.AC3 = 0
        self.AC4 = 0; self.AC5 = 0; self.AC6 = 0
        self.B1  = 0; self.B2  = 0
        self.MB  = 0; self.MC  = 0; self.MD  = 0

        # Valor intermedio compartido entre T y P
        self._B5 = 0

        self._read_calibration()

    # ================================================================
    # Helpers I2C
    # ================================================================
    def _read_byte(self, reg):
        return self.i2c.readfrom_mem(self.addr, reg, 1)[0]

    def _write_byte(self, reg, val):
        self.i2c.writeto_mem(self.addr, reg, bytes([val]))

    @staticmethod
    def _to_signed(val):
        """Convierte unsigned 16-bit a signed (complemento a 2)."""
        return val - 65536 if val >= 32768 else val

    # ================================================================
    # Calibración
    # ================================================================
    def _read_calibration(self):
        """
        Lee los 11 coeficientes de calibración del EEPROM del sensor.

        Mapa de EEPROM (22 bytes desde 0xAA):
          0xAA-0xAB: AC1 (signed)
          0xAC-0xAD: AC2 (signed)
          0xAE-0xAF: AC3 (signed)
          0xB0-0xB1: AC4 (unsigned)
          0xB2-0xB3: AC5 (unsigned)
          0xB4-0xB5: AC6 (unsigned)
          0xB6-0xB7: B1  (signed)
          0xB8-0xB9: B2  (signed)
          0xBA-0xBB: MB  (signed)
          0xBC-0xBD: MC  (signed)
          0xBE-0xBF: MD  (signed)
        """
        data = self.i2c.readfrom_mem(self.addr, self._REG_CALIB, 22)

        # Signed 16-bit
        self.AC1 = self._to_signed((data[0]  << 8) | data[1])
        self.AC2 = self._to_signed((data[2]  << 8) | data[3])
        self.AC3 = self._to_signed((data[4]  << 8) | data[5])
        # Unsigned 16-bit
        self.AC4 = (data[6]  << 8) | data[7]
        self.AC5 = (data[8]  << 8) | data[9]
        self.AC6 = (data[10] << 8) | data[11]
        # Signed 16-bit
        self.B1  = self._to_signed((data[12] << 8) | data[13])
        self.B2  = self._to_signed((data[14] << 8) | data[15])
        self.MB  = self._to_signed((data[16] << 8) | data[17])
        self.MC  = self._to_signed((data[18] << 8) | data[19])
        self.MD  = self._to_signed((data[20] << 8) | data[21])

    def get_calibration(self):
        """Retorna diccionario con los 11 coeficientes de calibración."""
        return {
            'AC1': self.AC1, 'AC2': self.AC2, 'AC3': self.AC3,
            'AC4': self.AC4, 'AC5': self.AC5, 'AC6': self.AC6,
            'B1':  self.B1,  'B2':  self.B2,
            'MB':  self.MB,  'MC':  self.MC,  'MD':  self.MD
        }

    # ================================================================
    # Lecturas crudas (sin compensar)
    # ================================================================
    def read_raw_temp(self):
        """
        Inicia medición y lee temperatura sin compensar (UT).

        Procedimiento:
          1. Escribir 0x2E en registro 0xF4
          2. Esperar 4.5 ms
          3. Leer 16 bits de registros 0xF6–0xF7

        Returns:
            int: Valor crudo UT (16-bit unsigned)
        """
        self._write_byte(self._REG_CTRL, self._CMD_TEMP)
        _sleep_ms(5)
        data = self.i2c.readfrom_mem(self.addr, self._REG_DATA, 2)
        return (data[0] << 8) | data[1]

    def read_raw_pressure(self):
        """
        Inicia medición y lee presión sin compensar (UP).

        Procedimiento:
          1. Escribir (0x34 + oss<<6) en registro 0xF4
          2. Esperar según modo (4.5–25.5 ms)
          3. Leer 19 bits de registros 0xF6–0xF8

        Returns:
            int: Valor crudo UP (hasta 19-bit)
        """
        cmd = self._CMD_PRES | (self.oss << 6)
        self._write_byte(self._REG_CTRL, cmd)
        _sleep_ms(self._DELAYS_MS[self.oss])
        data = self.i2c.readfrom_mem(self.addr, self._REG_DATA, 3)
        return ((data[0] << 16) | (data[1] << 8) | data[2]) >> (8 - self.oss)

    # ================================================================
    # Compensación de temperatura
    # ================================================================
    def _compute_B5(self, UT):
        """
        Calcula coeficiente intermedio B5 (necesario para T y P).

        Algoritmo (Bosch datasheet, Sección 3.5):
          X1 = (UT − AC6) × AC5 / 2¹⁵
          X2 = MC × 2¹¹ / (X1 + MD)
          B5 = X1 + X2

        Returns:
            int: Valor B5
        """
        X1 = ((UT - self.AC6) * self.AC5) >> 15
        X2 = (self.MC << 11) // (X1 + self.MD)
        return X1 + X2

    def temperature(self):
        """
        Lee y compensa temperatura.

        Returns:
            float: Temperatura en °C (resolución 0.1 °C)
        """
        UT = self.read_raw_temp()
        self._B5 = self._compute_B5(UT)
        T = ((self._B5 + 8) >> 4) / 10.0
        return T

    def temperature_detailed(self):
        """
        Lee temperatura con todos los pasos intermedios (para análisis educativo).

        Returns:
            dict: {'UT', 'X1', 'X2', 'B5', 'T_raw', 'T_C'}
        """
        UT = self.read_raw_temp()
        X1 = ((UT - self.AC6) * self.AC5) >> 15
        X2 = (self.MC << 11) // (X1 + self.MD)
        B5 = X1 + X2
        self._B5 = B5
        T_raw = (B5 + 8) >> 4       # En unidades de 0.1 °C
        T_celsius = T_raw / 10.0
        return {'UT': UT, 'X1': X1, 'X2': X2, 'B5': B5, 'T_raw': T_raw, 'T_C': T_celsius}

    # ================================================================
    # Compensación de presión
    # ================================================================
    def _compensate_pressure(self, UP):
        """
        Aplica algoritmo de compensación de presión completo (Bosch datasheet, Sec 3.5).

        Requiere que self._B5 esté actualizado (llamar temperature() primero).

        Pasos:
          B6 = B5 − 4000
          X1 = (B2 × (B6² / 2¹²)) / 2¹¹
          X2 = AC2 × B6 / 2¹¹
          X3 = X1 + X2
          B3 = ((AC1 × 4 + X3) << oss + 2) / 4
          X1 = AC3 × B6 / 2¹³
          X2 = (B1 × (B6² / 2¹²)) / 2¹⁶
          X3 = ((X1 + X2) + 2) / 4
          B4 = AC4 × (X3 + 32768) / 2¹⁵   (unsigned)
          B7 = (UP − B3) × (50000 >> oss)
          if B7 < 0x80000000:  p = (B7 × 2) / B4
          else:                p = (B7 / B4) × 2
          X1 = (p/256)² ; X1 = X1 × 3038 / 2¹⁶
          X2 = −7357 × p / 2¹⁶
          p = p + (X1 + X2 + 3791) / 2⁴

        Returns:
            int: Presión compensada en Pa
        """
        B5 = self._B5
        B6 = B5 - 4000

        X1 = (self.B2 * ((B6 * B6) >> 12)) >> 11
        X2 = (self.AC2 * B6) >> 11
        X3 = X1 + X2
        B3 = (((self.AC1 * 4 + X3) << self.oss) + 2) >> 2

        X1 = (self.AC3 * B6) >> 13
        X2 = (self.B1 * ((B6 * B6) >> 12)) >> 16
        X3 = ((X1 + X2) + 2) >> 2
        B4 = (self.AC4 * (X3 + 32768)) >> 15

        B7 = (UP - B3) * (50000 >> self.oss)
        if B7 < 0x80000000:
            p = (B7 * 2) // B4
        else:
            p = (B7 // B4) * 2

        X1 = (p >> 8) * (p >> 8)
        X1 = (X1 * 3038) >> 16
        X2 = (-7357 * p) >> 16
        p = p + ((X1 + X2 + 3791) >> 4)
        return p

    def pressure(self):
        """
        Lee y compensa presión.

        Realiza lectura de temperatura primero para actualizar B5.

        Returns:
            int: Presión en Pa (ej: 101325 = 1013.25 hPa)
        """
        UT = self.read_raw_temp()
        self._B5 = self._compute_B5(UT)
        UP = self.read_raw_pressure()
        return self._compensate_pressure(UP)

    def pressure_detailed(self):
        """
        Lee presión con todos los pasos intermedios (para análisis educativo).

        Returns:
            dict: {'UT', 'UP', 'B5', 'B6', 'B3', 'B4', 'B7', 'P_Pa', 'P_hPa'}
        """
        UT = self.read_raw_temp()
        UP = self.read_raw_pressure()
        B5 = self._compute_B5(UT)
        self._B5 = B5

        B6 = B5 - 4000
        X1a = (self.B2 * ((B6 * B6) >> 12)) >> 11
        X2a = (self.AC2 * B6) >> 11
        X3a = X1a + X2a
        B3  = (((self.AC1 * 4 + X3a) << self.oss) + 2) >> 2

        X1b = (self.AC3 * B6) >> 13
        X2b = (self.B1 * ((B6 * B6) >> 12)) >> 16
        X3b = ((X1b + X2b) + 2) >> 2
        B4  = (self.AC4 * (X3b + 32768)) >> 15

        B7 = (UP - B3) * (50000 >> self.oss)
        if B7 < 0x80000000:
            p = (B7 * 2) // B4
        else:
            p = (B7 // B4) * 2
        X1c = (p >> 8) * (p >> 8)
        X1c = (X1c * 3038) >> 16
        X2c = (-7357 * p) >> 16
        p   = p + ((X1c + X2c + 3791) >> 4)

        return {
            'UT': UT, 'UP': UP, 'B5': B5, 'B6': B6,
            'B3': B3, 'B4': B4, 'B7': B7,
            'P_Pa': p, 'P_hPa': p / 100.0
        }

    # ================================================================
    # Altitud barométrica
    # ================================================================
    def altitude(self, p0=101325.0):
        """
        Calcula altitud barométrica usando fórmula ISA.

        h = 44330 × (1 − (P / P₀)^(1/5.255))

        Args:
            p0: Presión de referencia a nivel del mar (Pa).
                ISA estándar = 101325 Pa.
                Ajustar al QNH local para altitud real.

        Returns:
            float: Altitud en metros sobre el nivel de referencia.
        """
        p = self.pressure()
        if p <= 0 or p0 <= 0:
            return 0.0
        return 44330.0 * (1.0 - (p / p0) ** (1.0 / 5.255))

    # ================================================================
    # Lectura combinada eficiente
    # ================================================================
    def read_all(self, p0=101325.0):
        """
        Lectura de temperatura, presión y altitud en un solo ciclo I2C.

        Más eficiente que llamar temperature(), pressure() y altitude()
        por separado porque comparte la lectura de UT y el cálculo de B5.

        Args:
            p0: Presión de referencia a nivel del mar (Pa).

        Returns:
            tuple: (temp_C, pressure_Pa, altitude_m)
        """
        UT = self.read_raw_temp()
        UP = self.read_raw_pressure()

        self._B5 = self._compute_B5(UT)
        T = ((self._B5 + 8) >> 4) / 10.0
        P = self._compensate_pressure(UP)

        if P > 0 and p0 > 0:
            h = 44330.0 * (1.0 - (P / p0) ** (1.0 / 5.255))
        else:
            h = 0.0

        return (T, P, h)

    # ================================================================
    # Utilidades
    # ================================================================
    def sea_level_pressure(self, altitude_m):
        """
        Calcula la presión a nivel del mar dado una altitud conocida.

        Útil para calibrar el QNH: si se conoce la altitud del punto
        de medición, se puede derivar P₀.

        P₀ = P / (1 − h/44330)^5.255

        Args:
            altitude_m: Altitud conocida en metros.

        Returns:
            float: Presión a nivel del mar estimada (Pa).
        """
        p = self.pressure()
        if altitude_m >= 44330:
            return p
        return p / ((1.0 - altitude_m / 44330.0) ** 5.255)

    def __repr__(self):
        return "BMP180(addr=0x{:02X}, oss={})".format(self.addr, self.oss)
