# P2: Adquisición de Datos Analógicos (ADC) - Sensor de Posición
# Plataforma: RP2040 (Raspberry Pi Pico) + MicroPython
#
# Funcionalidad:
# - Lee un sensor analógico (ej. potenciómetro) en GP26 (ADC0) usando ADC a 12 bits.
# - Convierte a voltaje (0-3.3V) y genera salida CSV por consola.
# - Incluye un filtro de media móvil simple para reducir ruido.
# - Mapea el voltaje a un ángulo (opcional) para sensores de posición tipo potenciómetro (0-300° aprox).
#
# DIFERENCIAS vs ESP32:
# - RP2040 usa read_u16() que devuelve 0-65535 (16 bits con padding, solo 12 bits significativos)
# - ESP32 usa read() que devuelve 0-4095 (12 bits directos)
# - RP2040 tiene solo 3 canales ADC: GP26 (ADC0), GP27 (ADC1), GP28 (ADC2)
# - No requiere atten() ni width(), ADC simple inicializado con pin number
#
# Salida (CSV):
# t_ms,raw,avg,voltage_v,angle_deg
# 0,32768,32768,1.650,150.0
# 10,32900,32850,1.656,150.5
# ...
#
# Uso:
# - Conecta el sensor como en assets/wiring.mmd.
# - Sube y ejecuta con Thonny o Pymakr. Observa la consola.
# - Para graficar, copia la salida CSV a un archivo y usa tu herramienta favorita.

from machine import ADC
from time import ticks_ms, ticks_diff, sleep_ms

# ------------ Parámetros de adquisición ------------
ADC_PIN = 26              # GP26 (ADC0) - Pin físico 31 en Pico
FS_HZ = 100               # Frecuencia de muestreo en Hz
MA_WINDOW = 8             # Ventana de media móvil (N muestras)
VREF = 3.3                # Voltaje de referencia (3.3V en RP2040)
ADC_MAX = 65535           # read_u16() -> 0..65535 (16 bits)
ANGLE_MAX_DEG = 300       # Rango angular del sensor de posición (ajustable)
PRINT_HEADER_EVERY = 0    # 0 = solo al inicio; >0 = reimprime cada N líneas

# ------------ Configuración de ADC ------------
# RP2040: ADC(pin_number) donde pin_number es 26, 27 o 28
# No necesita atten() ni width(), ya configurado para 0-3.3V
adc = ADC(ADC_PIN)

# ------------ Utilidades ------------

def raw_to_voltage(raw: int) -> float:
    """Convierte lectura ADC de 16 bits a voltaje (0-3.3V)"""
    return (raw / ADC_MAX) * VREF


def voltage_to_angle(voltage: float) -> float:
    """Mapeo lineal 0..VREF -> 0..ANGLE_MAX_DEG"""
    if voltage <= 0:
        return 0.0
    if voltage >= VREF:
        return float(ANGLE_MAX_DEG)
    return (voltage / VREF) * ANGLE_MAX_DEG


class MovingAverage:
    """Filtro de media móvil simple"""
    def __init__(self, size: int):
        self.size = max(1, int(size))
        self.buf = [0] * self.size
        self.sum = 0
        self.idx = 0
        self.count = 0

    def add(self, x: int) -> int:
        # Quita el viejo y añade el nuevo
        old = self.buf[self.idx]
        self.sum -= old
        self.buf[self.idx] = x
        self.sum += x
        self.idx = (self.idx + 1) % self.size
        if self.count < self.size:
            self.count += 1
        # Retorna promedio entero para coherencia con raw
        return self.sum // self.count


# ------------ Loop principal ------------

def main():
    period_ms = max(1, int(1000 / FS_HZ))
    ma = MovingAverage(MA_WINDOW)

    # Cabecera CSV
    print("t_ms,raw,avg,voltage_v,angle_deg")
    print("# RP2040 ADC: GP{} (ADC{}), read_u16() 0-65535".format(ADC_PIN, ADC_PIN-26))

    t0 = ticks_ms()
    line = 0
    try:
        while True:
            t = ticks_diff(ticks_ms(), t0)
            
            # DIFERENCIA CLAVE: read_u16() en lugar de read()
            raw = adc.read_u16()  # 0-65535 (16 bits)
            
            avg = ma.add(raw)
            v = raw_to_voltage(avg)
            ang = voltage_to_angle(v)

            # Imprime CSV
            print("{},{},{},{:.3f},{:.1f}".format(t, raw, avg, v, ang))

            line += 1
            if PRINT_HEADER_EVERY and (line % PRINT_HEADER_EVERY == 0):
                print("t_ms,raw,avg,voltage_v,angle_deg")

            sleep_ms(period_ms)
    except KeyboardInterrupt:
        print("\n[INFO] Adquisición detenida por el usuario.")


if __name__ == "__main__":
    main()
