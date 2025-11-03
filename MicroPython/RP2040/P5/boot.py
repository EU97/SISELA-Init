"""
Práctica 5 — Control PWM para Servomotores (RP2040 + MicroPython)

Archivo de arranque mínimo. Mantiene el REPL disponible y no
interfiere con la ejecución del script principal.
"""

try:
    import machine  # noqa: F401 (asegura inicialización básica)
except ImportError:
    pass

print("\n=== Práctica 5: Control PWM para Servomotores (RP2040) ===\n")
