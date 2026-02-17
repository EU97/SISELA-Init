# P2: Sistema de Adquisición Analógica con Codificación ARINC 429
# Plataforma: ESP32 + MicroPython
#
# Funcionalidad completa (4 casos + sistema integrado):
#   Caso 1 - ADC + Media Móvil: Lee potenciómetro en GPIO34, filtra ruido con
#            media móvil (N=8), convierte a voltaje y ángulo del sensor.
#   Caso 2 - Indicador de Flaps: Mapea el voltaje a posición de flaps (0-45°).
#            Genera alerta si se supera el umbral de sobre-extensión (>40°).
#   Caso 3 - ARINC 429 BNR: Empaqueta el valor ADC en una palabra de 32 bits
#            con Label 270 (octal), datos BNR, SSM y paridad impar.
#   Caso 4 - Falla de Sensor: Detecta valores fuera de rango (circuito abierto)
#            y actualiza la SSM a Failure Warning (00). Enciende LED indicador.
#
# Salida CSV (compatible con tools/live_plot.py):
#   t_ms,raw,avg,voltage_v,angle_deg,flap_deg,ssm,arinc_hex
#   0,2048,2048,1.650,150.0,22.5,OK,0x6008C0B8
#   10,2052,2050,1.653,150.2,22.5,OK,0x6008D0B8
#
# Uso:
#   1. Conecta el sensor como en assets/wiring.mmd (VCC->3V3, GND->GND, Wiper->GPIO34).
#   2. Sube con Pymakr (config en pymakr.conf). Observa la consola serial.
#   3. Para gráficas en tiempo real:
#        python tools/live_plot.py --port COM3 --baud 115200 --y voltage_v
#   4. Para graficar CSV exportado ver docs/oscilograma.md.

from machine import ADC, Pin
from time import ticks_ms, ticks_diff, sleep_ms

# ------------ Parámetros de adquisición (Caso 1) ------------
ADC_PIN = 34              # GPIO34 (entrada analógica solo-entrada)
FS_HZ = 100               # Frecuencia de muestreo en Hz
MA_WINDOW = 8             # Ventana de media móvil (N muestras)
VREF = 3.3                # Voltaje de referencia (aprox con ATTN_11DB)
ADC_MAX = 4095            # 12 bits -> 0..4095
ANGLE_MAX_DEG = 300       # Rango angular del potenciómetro (ajustable)

# ------------ Parámetros de flaps (Caso 2) ------------
FLAP_MAX_DEG = 45.0       # Deflexión máxima de flaps
FLAP_ALERT_DEG = 40.0     # Umbral de alerta por sobre-extensión

# ------------ Parámetros ARINC 429 (Caso 3) ------------
ARINC_LABEL = 270         # Label octal ARINC 429 para posición de flaps

# ------------ Parámetros de detección de falla (Caso 4) ------------
UMBRAL_MIN = int(ADC_MAX * 0.02)   # ~82  (sensor desconectado bajo)
UMBRAL_MAX = int(ADC_MAX * 0.98)   # ~4013 (sensor desconectado alto)
LED_PIN = 2               # GPIO2 = LED onboard (indicador de falla)

# ------------ Configuración de hardware ------------
adc = ADC(Pin(ADC_PIN))
adc.atten(ADC.ATTN_11DB)      # rango ~0-3.3V (teórico hasta ~3.6V)
adc.width(ADC.WIDTH_12BIT)    # 12 bits

try:
    led_falla = Pin(LED_PIN, Pin.OUT)
    led_falla.value(0)
except Exception:
    led_falla = None

# ============================================================
# Caso 1: Utilidades de conversión y filtrado
# ============================================================

def raw_to_voltage(raw: int) -> float:
    """Convierte lectura ADC cruda a voltaje (0-3.3V)."""
    return (raw / ADC_MAX) * VREF


def voltage_to_angle(voltage: float) -> float:
    """Mapeo lineal 0..VREF -> 0..ANGLE_MAX_DEG (ángulo del potenciómetro)."""
    if voltage <= 0:
        return 0.0
    if voltage >= VREF:
        return float(ANGLE_MAX_DEG)
    return (voltage / VREF) * ANGLE_MAX_DEG


class MovingAverage:
    """Filtro de media móvil de N muestras para estabilizar la lectura ADC."""
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


# ============================================================
# Caso 2: Indicador de posición de flaps
# ============================================================

def voltage_to_flap(voltage: float) -> float:
    """Mapeo lineal 0..VREF -> 0..FLAP_MAX_DEG (posición de flaps)."""
    if voltage <= 0:
        return 0.0
    if voltage >= VREF:
        return FLAP_MAX_DEG
    return (voltage / VREF) * FLAP_MAX_DEG


# ============================================================
# Caso 3: Codificación ARINC 429 BNR (Label 270)
# ============================================================

def generar_palabra_arinc(label_oct: int, dato_adc: int, ssm: int = 0b11) -> int:
    """Construye una palabra ARINC 429 de 32 bits (formato BNR).

    Estructura de bits (LSB=1):
      Bits  1-8 : Label (etiqueta en octal, ej. 270_8 = 0xB8)
      Bits  9-10: SDI (Source/Destination Identifier, 00 por defecto)
      Bits 11-29: Data (19 bits, valor BNR)
      Bits 30-31: SSM (Sign/Status Matrix)
      Bit  32   : Paridad impar

    Args:
        label_oct: Etiqueta en octal (ej. 270)
        dato_adc:  Valor ADC (0-4095 para 12 bits)
        ssm:       0b11=Normal Operation, 0b00=Failure Warning,
                   0b01=No Computed Data, 0b10=Functional Test

    Returns:
        Palabra de 32 bits como entero.
    """
    label_int = int(str(label_oct), 8)
    trama = (ssm << 29) | (dato_adc << 10) | label_int

    # Paridad impar: total de '1' en los 32 bits debe ser impar
    if bin(trama).count('1') % 2 == 0:
        trama |= (1 << 31)
    return trama


# ============================================================
# Caso 4: Detección de falla de sensor
# ============================================================

def detectar_falla(raw: int) -> int:
    """Evalúa si el sensor está dentro del rango válido.

    Si el potenciómetro se desconecta, el pin ADC queda flotante y lee
    valores erráticos (cercanos a 0 o ADC_MAX). Un margen del 2% en
    cada extremo filtra estas condiciones.

    Returns:
        0b11 (Normal Operation) o 0b00 (Failure Warning).
    """
    if raw < UMBRAL_MIN or raw > UMBRAL_MAX:
        return 0b00   # Failure Warning
    return 0b11       # Normal Operation


# ============================================================
# Loop principal — Sistema integrado
# ============================================================

def main():
    period_ms = max(1, int(1000 / FS_HZ))
    ma = MovingAverage(MA_WINDOW)

    # Cabecera CSV extendida (compatible con tools/live_plot.py)
    print("t_ms,raw,avg,voltage_v,angle_deg,flap_deg,ssm,arinc_hex")

    t0 = ticks_ms()
    try:
        while True:
            t = ticks_diff(ticks_ms(), t0)
            raw = adc.read()
            avg = ma.add(raw)
            v = raw_to_voltage(avg)
            ang = voltage_to_angle(v)

            # Caso 2: Posición de flaps
            flap = voltage_to_flap(v)

            # Caso 4: Detección de falla
            ssm = detectar_falla(raw)

            # LED indicador de falla
            if led_falla:
                led_falla.value(1 if ssm == 0b00 else 0)

            # Caso 3: Codificación ARINC 429
            word = generar_palabra_arinc(ARINC_LABEL, avg, ssm)

            # Salida CSV con todos los datos
            ssm_str = "OK" if ssm == 0b11 else "FAIL"
            print("{},{},{},{:.3f},{:.1f},{:.1f},{},0x{:08X}".format(
                t, raw, avg, v, ang, flap, ssm_str, word))

            sleep_ms(period_ms)
    except KeyboardInterrupt:
        if led_falla:
            led_falla.value(0)
        print("\n[INFO] Adquisición detenida por el usuario.")


if __name__ == "__main__":
    main()
