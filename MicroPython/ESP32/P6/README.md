# Práctica P6 — MicroPython · ESP32 · OLED SSD1306 (I2C)

Visualización local en pantalla OLED 128x64 utilizando el bus I2C del ESP32. Opcionalmente integra un sensor BMP280 en el mismo bus para mostrar temperatura, presión y altitud.

## Objetivo

- Configurar I2C en el ESP32 y manejar una pantalla OLED SSD1306 (0x3C)
- Presentar datos en la pantalla (texto y mini-gráficas)
- Integrar un sensor digital (BMP280) en el mismo bus I2C para visualizar T/P/Alt

## Requisitos previos

- ESP32 con MicroPython cargado
- Extensión Pymakr en VS Code (o alternativa Thonny / rshell)
- Conocimiento básico de I2C (P5) y del flujo de trabajo de prácticas previas

## Material y conexiones

- Módulo OLED SSD1306 128x64 (I2C, dirección típica 0x3C)
- (Opcional) Módulo BMP280 (0x76/0x77)
- Cables Dupont

Conexiones (ESP32 DevKit):

- SDA → GPIO21
- SCL → GPIO22
- VCC → 3.3 V
- GND → GND

Ambos (OLED + BMP280) pueden ir en paralelo al mismo bus I2C (SDA/SCL compartidos).

Consulta `PINES.md` y `assets/wiring.svg` para el esquema.

## Pasos

1) En Pymakr, sube `boot.py`, `main.py` y la carpeta `lib/` (ssd1306.py, bmp280.py)
2) Conecta la OLED (y opcionalmente el BMP280)
3) Resetea el ESP32. Verás un mensaje de arranque; `main.py` ofrece menú por consola.

## Modos de operación

1. Dashboard (texto): Muestra T/Presión/Alt si hay BMP280; si no, mensajes de “sin sensor”.
2. Mini-gráfica: Traza desplazante de altitud (o presión) a lo largo del tiempo.
3. Scan I2C: Lista de direcciones detectadas (útil para diagnóstico de cableado).
4. Demo OLED: Texto rebotando para probar la pantalla.

Para volver al menú: escribe `m` + ENTER en la consola.

## Verificación

- Se detecta la OLED y se actualiza la pantalla sin errores
- Si hay BMP280:
	- Se muestran temperatura (°C), presión (hPa) y altitud (m) en el Dashboard
	- La mini-gráfica reacciona a cambios (moviendo el sensor o variando la presión)
- Scan I2C muestra 0x3C (OLED) y 0x76/0x77 (BMP280) cuando estén conectados

## Archivos

- `boot.py`: Mensaje de arranque
- `main.py`: Lógica de menú y modos, integración con OLED/BMP280
- `lib/ssd1306.py`: Driver mínimo de la pantalla OLED
- `lib/bmp280.py`: Driver del sensor BMP280 (opcional)
- `PINES.md`: Tabla de pines y notas
- `assets/wiring.mmd` / `assets/wiring.svg`: Diagrama de cableado
- `docs/SSD1306.md`: Ficha técnica breve

## Recursos

- Datasheet SSD1306 (comandos y modo de memoria)
- MicroPython `framebuf` (renderizado en blanco/negro)
- Prácticas anteriores (P5) para BMP280
