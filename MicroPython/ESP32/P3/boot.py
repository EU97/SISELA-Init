# boot.py — Práctica 3 NTC (ESP32 + MicroPython)
# Inicialización mínima: suprime logs de debug y anuncia arranque.

try:
    import esp
    esp.osdebug(None)
except Exception:
    pass

print("[BOOT][P3] Medición de temperatura con NTC — iniciando main.py…")
