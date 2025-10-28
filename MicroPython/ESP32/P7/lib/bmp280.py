# Reutilización: driver BMP280 mínimo (copiado de P6)
try:
    from machine import I2C
except ImportError:
    pass

BMP280_REG_CHIP_ID = 0xD0
BMP280_CHIP_ID = 0x58
BMP280_REG_CALIB_START = 0x88
BMP280_REG_CTRL_MEAS = 0xF4
BMP280_REG_CONFIG = 0xF5
BMP280_REG_PRESS_MSB = 0xF7

BMP280_MODE_NORMAL = 0x03
BMP280_OSRS_2 = 0x02


class BMP280:
    def __init__(self, i2c, addr=0x76):
        self.i2c = i2c
        self.addr = addr
        chip = self.i2c.readfrom_mem(self.addr, BMP280_REG_CHIP_ID, 1)[0]
        if chip != BMP280_CHIP_ID:
            raise RuntimeError("BMP280 chip id mismatch: 0x%02X" % chip)
        self._load_calib()
        self._configure()

    def _read(self, reg, n):
        return self.i2c.readfrom_mem(self.addr, reg, n)

    def _write(self, reg, val):
        if isinstance(val, int):
            val = bytes([val])
        self.i2c.writeto_mem(self.addr, reg, val)

    def _load_calib(self):
        calib = self._read(BMP280_REG_CALIB_START, 24)
        self.dig_T1 = int.from_bytes(calib[0:2], 'little')
        self.dig_T2 = int.from_bytes(calib[2:4], 'little', signed=True)
        self.dig_T3 = int.from_bytes(calib[4:6], 'little', signed=True)
        self.dig_P1 = int.from_bytes(calib[6:8], 'little')
        self.dig_P2 = int.from_bytes(calib[8:10], 'little', signed=True)
        self.dig_P3 = int.from_bytes(calib[10:12], 'little', signed=True)
        self.dig_P4 = int.from_bytes(calib[12:14], 'little', signed=True)
        self.dig_P5 = int.from_bytes(calib[14:16], 'little', signed=True)
        self.dig_P6 = int.from_bytes(calib[16:18], 'little', signed=True)
        self.dig_P7 = int.from_bytes(calib[18:20], 'little', signed=True)
        self.dig_P8 = int.from_bytes(calib[20:22], 'little', signed=True)
        self.dig_P9 = int.from_bytes(calib[22:24], 'little', signed=True)

    def _configure(self):
        ctrl_meas = (BMP280_OSRS_2 << 5) | (BMP280_OSRS_2 << 2) | BMP280_MODE_NORMAL
        self._write(BMP280_REG_CTRL_MEAS, ctrl_meas)
        config = (0x04 << 5) | (0x00 << 2) | 0x00  # standby 500ms, filter off
        self._write(BMP280_REG_CONFIG, config)

    def read_raw(self):
        data = self._read(BMP280_REG_PRESS_MSB, 6)
        adc_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        adc_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        return adc_t, adc_p

    def _comp_temp(self, adc_t):
        var1 = ((adc_t >> 3) - (self.dig_T1 << 1)) * self.dig_T2 >> 11
        var2 = (((adc_t >> 4) - self.dig_T1) * ((adc_t >> 4) - self.dig_T1) >> 12) * self.dig_T3 >> 14
        t_fine = var1 + var2
        temp = (t_fine * 5 + 128) >> 8
        return temp / 100.0, t_fine

    def _comp_press(self, adc_p, t_fine):
        var1 = t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12)
        var1 = ((1 << 47) + var1) * self.dig_P1 >> 33
        if var1 == 0:
            return 0.0
        p = 1048576 - adc_p
        p = (((p << 31) - var2) * 3125) // var1
        var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
        var2 = (self.dig_P8 * p) >> 19
        p = ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)
        return p / 256.0

    def read(self):
        adc_t, adc_p = self.read_raw()
        temp, t_fine = self._comp_temp(adc_t)
        press = self._comp_press(adc_p, t_fine)
        return temp, press
