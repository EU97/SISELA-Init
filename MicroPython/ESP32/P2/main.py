# P2: Adquisición de Datos Analógicos (ADC) - Sensor de Posición
# Plataforma: ESP32 + MicroPython
# Metodología replicada de P1: estructura de carpetas, documentación y ejecución con Pymakr.
#
# Funcionalidad:
# - Lee un sensor analógico (ej. potenciómetro) en GPIO34 usando ADC a 12 bits.
# - Convierte a voltaje con atenuación 11dB (0-3.3V aprox) y genera salida CSV por consola.
# - Incluye un filtro de media móvil simple para reducir ruido.
# - Mapea el voltaje a un ángulo (opcional) para sensores de posición tipo potenciómetro (0-300° aprox).
#
# Salida (CSV):
# t_ms,raw,avg,voltage_v,angle_deg
# 0,2048,2048,1.650,150.0
# 10,2052,2050,1.653,150.2
# ...
#
# Uso:
# - Conecta el sensor como en assets/wiring.mmd.
# - Sube y ejecuta con Pymakr (config en pymakr.conf). Observa la consola.
# - Para graficar, copia la salida CSV a un archivo y usa tu herramienta favorita.

from machine import ADC, Pin
from time import ticks_ms, ticks_diff, sleep_ms

# ------------ Parámetros de adquisición ------------
ADC_PIN = 34              # GPIO34 (entrada analógica solo-entrada)
FS_HZ = 100               # Frecuencia de muestreo en Hz
MA_WINDOW = 8             # Ventana de media móvil (N muestras)
VREF = 3.3                # Voltaje de referencia (aprox con ATTN_11DB)
ADC_MAX = 4095            # 12 bits -> 0..4095
ANGLE_MAX_DEG = 300       # Rango angular del sensor de posición (ajustable)
PRINT_HEADER_EVERY = 0    # 0 = solo al inicio; >0 = reimprime cada N líneas

# ------------ Configuración de ADC ------------
adc = ADC(Pin(ADC_PIN))
adc.atten(ADC.ATTN_11DB)      # rango ~0-3.3V (teórico hasta ~3.6V)
adc.width(ADC.WIDTH_12BIT)    # 12 bits

# ------------ Utilidades ------------

def raw_to_voltage(raw: int) -> float:
    return (raw / ADC_MAX) * VREF


def voltage_to_angle(voltage: float) -> float:
    # Mapeo lineal 0..VREF -> 0..ANGLE_MAX_DEG
    if voltage <= 0:
        return 0.0
    if voltage >= VREF:
        return float(ANGLE_MAX_DEG)
    return (voltage / VREF) * ANGLE_MAX_DEG


class MovingAverage:
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
        # Retorna promedio entero para coherencia con raw (pero puedes usar float si prefieres)
        return self.sum // self.count


# ------------ Loop principal ------------

def main():
    period_ms = max(1, int(1000 / FS_HZ))
    ma = MovingAverage(MA_WINDOW)

    # Cabecera CSV
    print("t_ms,raw,avg,voltage_v,angle_deg")

    t0 = ticks_ms()
    line = 0
    try:
        while True:
            t = ticks_diff(ticks_ms(), t0)
            raw = adc.read()
            avg = ma.add(raw)
            v = raw_to_voltage(avg)
            ang = voltage_to_angle(v)

            # Imprime CSV
            # Formateo conservador para MicroPython (f-strings básicos)
            print("{},{},{},{:.3f},{:.1f}".format(t, raw, avg, v, ang))

            line += 1
            if PRINT_HEADER_EVERY and (line % PRINT_HEADER_EVERY == 0):
                print("t_ms,raw,avg,voltage_v,angle_deg")

            sleep_ms(period_ms)
    except KeyboardInterrupt:
        print("\n[INFO] Adquisición detenida por el usuario.")


if __name__ == "__main__":
    main()
