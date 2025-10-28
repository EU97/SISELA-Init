# boot.py - P2 ESP32 MicroPython
# Mantiene la estructura/metodología de P1.
# Este archivo se ejecuta al arrancar.

# (Opcional) Aquí puedes configurar periféricos globales, desactivar WiFi
# para reducir ruido en mediciones, etc. Mantener mínimo por simplicidad.

try:
    import esp
    esp.osdebug(None)  # Silencia logs de debug del sistema
except Exception:
    pass

print("[BOOT] ESP32 listo para P2 (ADC)")
