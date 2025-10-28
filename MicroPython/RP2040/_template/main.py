# main.py — plantilla base para prácticas RP2040 + MicroPython
# Estructura: parámetros, configuración HW, utilidades, clases, loop principal.

from time import ticks_ms, ticks_diff, sleep_ms

# -------- Parámetros (ajusta para tu práctica) --------
LOOP_HZ = 10        # Frecuencia de iteración del loop principal
PRINT_EVERY = 1     # Imprime cada N iteraciones (para no saturar)

# Ejemplos de pines (RP2040):
# from machine import Pin, ADC, PWM, I2C, UART
# PIN_LED = 25  # Onboard LED en Raspberry Pi Pico
# ADC_PIN = 26  # ADC0 = GP26, ADC1 = GP27, ADC2 = GP28

# Nota ADC en RP2040 MicroPython:
# - Se usa read_u16() (0..65535), resolver con Vref ~3.3 V.
# - Ej.: adc = ADC(26); val = adc.read_u16()

# -------- Configuración HW (inicializa periféricos aquí) --------
# led = Pin(PIN_LED, Pin.OUT)
# adc = ADC(ADC_PIN)  # usar canal 26/27/28 según corresponda

# -------- Utilidades --------

def now_ms() -> int:
    return ticks_ms()

# -------- Clases auxiliares (opcional) --------

class MovingAverage:
    def __init__(self, size: int):
        self.size = max(1, int(size))
        self.buf = [0] * self.size
        self.sum = 0
        self.idx = 0
        self.count = 0

    def add(self, x: int) -> int:
        old = self.buf[self.idx]
        self.sum -= old
        self.buf[self.idx] = x
        self.sum += x
        self.idx = (self.idx + 1) % self.size
        if self.count < self.size:
            self.count += 1
        return self.sum // self.count

# -------- Loop principal --------

def main():
    period_ms = max(1, int(1000 / LOOP_HZ))
    t0 = now_ms()
    it = 0

    # Ejemplo de cabecera CSV (ajusta campos para tu práctica)
    # print("t_ms,field1,field2")

    try:
        while True:
            t = ticks_diff(now_ms(), t0)

            # LEE SENSORES / ACTUALIZA ESTADO AQUÍ (p.ej., val = adc.read_u16())

            if it % PRINT_EVERY == 0:
                # print("{},{}".format(t, val))
                pass

            it += 1
            sleep_ms(period_ms)
    except KeyboardInterrupt:
        print("\n[INFO] Ejecución detenida por el usuario.")


if __name__ == "__main__":
    main()
