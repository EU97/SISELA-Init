# boot.py — inicialización mínima de práctica
# Ajusta según necesidades (desactivar WiFi/BT, logs, etc.)

try:
    import esp
    esp.osdebug(None)
except Exception:
    pass

print("[BOOT] Plantilla lista. Ejecutando main.py…")
