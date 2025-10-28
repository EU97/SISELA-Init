# PINES — P6 OLED SSD1306 (I2C)

Conexiones principales en ESP32 (DevKit):

- SDA → GPIO21
- SCL → GPIO22
- VCC → 3.3 V
- GND → GND

Direcciones I2C típicas:

- OLED SSD1306: 0x3C
- BMP280 (opcional): 0x76 o 0x77

Notas:

- La mayoría de módulos OLED incluyen resistencias de pull‑up en SDA/SCL. Si no, añade ~4.7 kΩ a 3.3 V.
- OLED y BMP280 pueden compartir el bus I2C (conectar en paralelo SDA/SCL). Asegura GND común.
- Mantén cables cortos para fiabilidad a 400 kHz.
