# Pines por defecto — Práctica P1 (ESP32 + MicroPython)

Este archivo documenta, de forma amigable, los pines usados por el código de `main.py`.

> Nota: Los pines están "hardcode" en el código. Si necesitas cambiarlos, edítalos en la sección "Configuración de pines" de `main.py`.

## Resumen de señales

- LED1 (salida): GPIO 2 — LED integrado común en muchas placas ESP32
- LED2 (salida): GPIO 4 — LED externo opcional
- LED3 (salida): GPIO 5 — LED externo opcional
- BTN1 (entrada): GPIO 13 — Botón con pull-up interno (activo LOW)
- BTN2 (entrada): GPIO 14 — Botón con pull-up interno (activo LOW)
- Nivel activo de LEDs: alto (LED_ON_LEVEL = 1)

## Mapa visual (lógico)

```
LED1  <-- GPIO2  (parpadeo y parte de las secuencias)
LED2  <-- GPIO4  (usa chaser y refleja BTN1 en modo monitor)
LED3  <-- GPIO5  (usa chaser y refleja BTN2 en modo monitor)
BTN1  --> GPIO13 (pulsado = 0; pull-up interno)
BTN2  --> GPIO14 (pulsado = 0; pull-up interno)
```

## Diagrama de cableado (Mermaid)

Puedes ver/editar el archivo fuente en `assets/wiring.mmd`. GitHub y algunas extensiones de VS Code renderizan Mermaid automáticamente.

```mermaid
%% Diagrama lógico de conexiones
graph LR
	subgraph ESP32
		GPIO2[(GPIO 2)]
		GPIO4[(GPIO 4)]
		GPIO5[(GPIO 5)]
		GPIO13[(GPIO 13)]
		GPIO14[(GPIO 14)]
		GND((GND))
	end

	GPIO2 --> R1[R 220Ω] --> D1[LED1]; D1 --> GND
	GPIO4 --> R2[R 220Ω] --> D2[LED2]; D2 --> GND
	GPIO5 --> R3[R 220Ω] --> D3[LED3]; D3 --> GND

	GPIO13 --- SW1((BTN1)) --- GND
	GPIO14 --- SW2((BTN2)) --- GND

	note1["Resistencia 220–330Ω típicamente"]
	R1 -.-> note1
	R2 -.-> note1
	R3 -.-> note1

	### SVG ya incluido

	Se incluye una versión SVG en `assets/wiring.svg` para visualizar sin soporte Mermaid.

	### ¿Cómo generar el SVG/PNG desde Mermaid en Windows (PowerShell)?

	1. Instala Node.js (https://nodejs.org/)
	2. Instala la CLI de Mermaid:

	```powershell
	npm install -g @mermaid-js/mermaid-cli
	```

	3. Genera el SVG (y opcionalmente PNG):

	```powershell
	# SVG transparente
	mmdc -i assets/wiring.mmd -o assets/wiring.svg -b transparent

	# PNG con fondo blanco (opcional)
```
	```

	Notas:
	- Si usas VS Code, también puedes instalar una extensión de Mermaid (p. ej., "Markdown Preview Mermaid Support") para previsualizar.
	- Como alternativa, usa el editor web https://mermaid.live para pegar el contenido y exportar SVG/PNG.

## Dónde modificar en el código

En `main.py`, busca la sección "Configuración de pines":

```python
# LEDs (salidas)
LED1_PIN = 2   # LED integrado habitual
LED2_PIN = 4   # Cambia si tu placa usa otros pines disponibles
LED3_PIN = 5

# Botones (entradas con pull-up)
BTN1_PIN = 13
BTN2_PIN = 14

LED_ON_LEVEL = 1  # 1 si el LED enciende con nivel alto; 0 para activo-bajo
```

- Para LEDs activos en bajo, cambia `LED_ON_LEVEL = 0`.
- Si tu placa tiene el LED integrado en otro pin (p. ej., GPIO 5 o 13), actualiza `LED1_PIN`.
- Si usas otros pines para botones, asegúrate de cablear el botón a GND (pull-up interno mantiene el pin en 1 cuando no se pulsa).

## Consejos de conexión

- LEDs externos: conecta la resistencia en serie (220–330 Ω típico) al pin de la GPIO y el LED a GND (o al Vcc si es activo-bajo; ajusta `LED_ON_LEVEL`).
- Botones: un extremo a la GPIO y el otro a GND; el `Pin.PULL_UP` interno mantiene el nivel alto cuando está suelto.

## Relación con los modos del programa

- Modo 1 (Blink): usa LED1.
- Modo 2 (Chaser): usa LED1, LED2, LED3 en secuencia.
- Modo 3 (Monitor): lee BTN1/BTN2 y refleja su estado en LED2/LED3.
- Modo 4 (Integrado): BTN1 cambia patrón (chaser ↔ blink-all) y BTN2 cambia velocidad.

## Oscilogramas

Consulta `docs/oscilograma.md` para ver diagramas ASCII de las señales esperadas en los modos Blink y Chaser, y notas para medir con osciloscopio.
