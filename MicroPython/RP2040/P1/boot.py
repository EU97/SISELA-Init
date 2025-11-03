"""
boot.py — se ejecuta al arranque de la placa (antes de main.py)

Mantenerlo ligero: ideal para configuración básica. Aquí solo
mostramos un mensaje para verificar el inicio.
"""

try:
	print("[boot] Sistema iniciando… (RP2040 + MicroPython) P1")
except Exception as e:
	# Evita que un fallo aquí bloquee el arranque
	pass
