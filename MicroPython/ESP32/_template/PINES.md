# [Pn] · Mapa de pines (ESP32)

Rellena con el mapeo concreto de la práctica.

Tabla rápida:

| Señal | Pin ESP32 | Descripción |
|------:|-----------|-------------|
| VCC   | 3V3       | Alimentación |
| GND   | GND       | Tierra |
| SIG   | GPIOXX    | Señal principal |

Notas:
- Agrega advertencias de voltaje/atenuación si usas ADC.
- Evita pines reservados o especiales si no los necesitas.

## Calibración rápida (opcional)

- Si vas a medir un nodo analógico con ADC, puedes incluir un modo de calibración (wizard) como en P3.
- Pasos típicos desde el REPL:
	1) Une el nodo a GND y confirma con `ok` + ENTER → se registra `low`.
	2) Une el nodo a 3V3 y confirma con `ok` + ENTER → se registra `high`.
	3) Se guarda `calibration.json` en la placa.
- Para usar la calibración en el código, expón una bandera en `main.py`:
	- `AUTO_USE_CALIBRATION = False` (por defecto). Si `True`, mapear `[low..high] → [0..Vref]`.
