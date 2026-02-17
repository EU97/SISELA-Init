# Práctica P1 — MicroPython en RP2040 (Raspberry Pi Pico)

Este proyecto prepara el entorno de la Práctica 1 (Fundamentos de MCUs y Entorno de Desarrollo) en una placa RP2040 usando MicroPython con Thonny o Pymakr en VS Code.

## Objetivo

- Flashear (si es necesario) MicroPython en una placa RP2040 (Raspberry Pi Pico/Pico W).
- Configurar el entorno de desarrollo y sincronizar un proyecto base.
- Ejecutar un ejemplo mínimo que parpadee el LED integrado (GP25) y muestre mensajes por el REPL.

## Requisitos previos

- Hardware: Raspberry Pi Pico, Pico W o compatible RP2040, cable micro-USB.
- Windows 10/11 (también funciona en Linux/macOS).
- Thonny IDE (recomendado) o VS Code + extensión Pymakr.
- Firmware MicroPython para RP2040 (v1.22 o superior recomendado).

## Estructura del proyecto

```
P1/
  ├─ boot.py        # Se ejecuta al arranque
  ├─ main.py        # Programa principal (múltiples modos + menú)
  ├─ PINES.md       # Documento amigable con el pinout por defecto
  ├─ lib/           # Módulos adicionales (vacío por ahora)
  │   └─ .gitkeep
  ├─ pymakr.conf    # Configuración del proyecto Pymakr (opcional)
  └─ README.md      # Este archivo
```

## Instalación de herramientas

### Opción 1: Thonny (recomendado para principiantes)
1. Descarga e instala Thonny desde https://thonny.org
2. Conecta el Pico manteniendo presionado el botón BOOTSEL
3. Aparecerá como unidad de almacenamiento masivo (RPI-RP2)
4. En Thonny, ve a Tools > Options > Interpreter
5. Selecciona "MicroPython (Raspberry Pi Pico)"
6. Haz clic en "Install or update MicroPython" si es necesario
7. Selecciona el firmware y presiona "Install"

### Opción 2: Pymakr en VS Code
1. Instala VS Code y la extensión "Pymakr" desde el Marketplace
2. Flashea MicroPython manualmente (ver siguiente sección)
3. Abre esta carpeta en VS Code
4. Conecta y sincroniza con Pymakr

### Flashear MicroPython manualmente (si es necesario)
1. Descarga el firmware desde https://micropython.org/download/RPI_PICO/
2. Mantén presionado BOOTSEL y conecta el Pico por USB
3. Aparecerá como unidad RPI-RP2
4. Copia el archivo `.uf2` a la unidad
5. El Pico se reiniciará automáticamente con MicroPython

## Configuración y uso

### Con Thonny:
1. Abre `main.py` en Thonny
2. Selecciona el intérprete "MicroPython (Raspberry Pi Pico)" en la esquina inferior derecha
3. Guarda el archivo en el Pico (Ctrl+Shift+S o "File > Save as..." > "Raspberry Pi Pico")
4. Haz lo mismo con `boot.py`
5. Presiona F5 o el botón "Run" para ejecutar

### Con Pymakr:
1. Abre esta carpeta `MicroPython/RP2040/P1` en VS Code
2. Conecta el Pico por USB
3. En Pymakr (barra inferior), presiona "Connect"
4. Presiona "Sync project" para subir archivos
5. Observa la salida en el terminal REPL

## Qué hace el ejemplo

- `main.py` ofrece 4 modos seleccionables por el monitor serial (REPL):
  1) Blink LED1 (GP25, LED integrado)
  2) Secuencia (chaser) en 3 LEDs (LED1, LED2, LED3)
  3) Monitor de entradas: lee BTN1/BTN2 (pull-up) y refleja en LED2/LED3
  4) Integrado: BTN1 alterna patrón (chaser/blink-all) y BTN2 cambia velocidad

- Al iniciar, aparece un menú. Escribe 1/2/3/4 + ENTER. Si no respondes, arranca el modo 4 por defecto.
- Durante la ejecución, escribe `m` + ENTER para volver al menú.
- Pines por defecto:
  - LEDs: `LED1_PIN=25` (onboard), `LED2_PIN=16`, `LED3_PIN=17`
  - Botones: `BTN1_PIN=14`, `BTN2_PIN=15` (pull-up, activo LOW)
- Ver esquema detallado en `PINES.md` y `assets/wiring.mmd`

## Verificación (criterios de aceptación)

- El REPL muestra al arranque: `[boot] Sistema iniciando… (RP2040 + MicroPython) P1`
- Luego aparece el menú con las 4 opciones
- En modo 1, mensajes `LED1 ON` / `LED1 OFF` cada segundo
- El LED integrado (GP25) parpadea con el mismo ritmo

## Diferencias con ESP32

| Aspecto | ESP32 | RP2040 |
|---------|-------|--------|
| LED integrado | GPIO 2 | GP25 |
| Pines digitales | GPIO 0-39 (no todos disponibles) | GP0-GP28 (29 pines) |
| ADC | 18 canales, 12 bits | 3 canales + 1 temp interno, 16 bits |
| Pull-up interno | Disponible | Disponible |
| Voltaje lógico | 3.3V | 3.3V |
| Tolerancia 5V | NO (algunos pines) | NO |

## Solución de problemas

- **No ves el puerto COM**: Prueba mantener BOOTSEL presionado al conectar, o reinstala drivers USB.
- **Puerto ocupado**: Cierra otros programas que usen el mismo puerto.
- **El LED no parpadea**: Verifica que `LED1_PIN=25` sea el LED onboard de tu placa.
- **Error de memoria**: El RP2040 tiene menos RAM que ESP32; limita el uso de buffers grandes.
- **Imports no encontrados**: Asegúrate de que MicroPython esté correctamente instalado en el Pico.

## Archivos clave

- `boot.py`: Mensaje de arranque, mantenerlo ligero para evitar bloqueos.
- `main.py`: Lógica principal con menú de 4 modos.
- `pymakr.conf`: Configuración opcional para Pymakr.
- `PINES.md`: Referencia detallada de pines.
- `lib/`: Carpeta para módulos propios/terceros (vacía por ahora).

## Preguntas de reflexión

1. ¿Qué diferencia hay entre `boot.py` y `main.py` en el ciclo de arranque?
2. ¿Cómo se compara el RP2040 con el ESP32 en términos de pines GPIO y ADC?
3. ¿Qué ventajas tiene Thonny sobre Pymakr para desarrollo con RP2040?

## Recursos

- MicroPython (RP2040): https://docs.micropython.org/en/latest/rp2/quickref.html
- Firmware oficial: https://micropython.org/download/RPI_PICO/
- Raspberry Pi Pico Datasheet: https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf
- Thonny IDE: https://thonny.org
