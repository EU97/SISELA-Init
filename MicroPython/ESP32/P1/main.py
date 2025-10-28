"""
Programa principal (main.py) — ESP32 + MicroPython

Función: parpadeo del LED integrado (GPIO 2 en la mayoría de DevKit)
         e impresión periódica en el REPL para ver actividad.

Si tu placa no tiene LED en GPIO 2, ajusta LED_PIN abajo.
"""

from machine import Pin
import time

# Cambia este valor si tu placa usa otro pin para el LED integrado
LED_PIN = 2

led = Pin(LED_PIN, Pin.OUT)

print("[main] Iniciando bucle de parpadeo en GPIO {}".format(LED_PIN))

while True:
    led.value(1)
    print("LED ON")
    time.sleep(1)
    led.value(0)
    print("LED OFF")
    time.sleep(1)
