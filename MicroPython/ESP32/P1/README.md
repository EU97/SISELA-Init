# Práctica P1 — MicroPython en ESP32 (Pymakr)

Este proyecto prepara el entorno de la Práctica 1 (Fundamentos de MCUs y Entorno de Desarrollo) en un ESP32 usando MicroPython y la extensión Pymakr en VS Code.

## Objetivo

- Flashear (si es necesario) MicroPython en una placa ESP32.
- Configurar VS Code + Pymakr y sincronizar un proyecto base.
- Ejecutar un ejemplo mínimo que parpadee el LED integrado y muestre mensajes por el REPL.

## Requisitos previos

- Hardware: ESP32 DevKit (p. ej., DevKitC), cable USB.
- Windows 10/11, con permisos para instalar drivers.
- Drivers del puerto serie según tu placa (CP210x o CH340).
- VS Code + extensión Pymakr.
- Firmware MicroPython para ESP32 (v1.22 o superior recomendado).

## Estructura del proyecto

```
P1/
  ├─ boot.py        # Se ejecuta al arranque
  ├─ main.py        # Programa principal (parpadeo LED + prints)
  ├─ lib/           # Módulos adicionales (vacío por ahora)
  │   └─ .gitkeep
  ├─ pymakr.conf    # Configuración del proyecto Pymakr
  └─ .gitignore
```

## Instalación de herramientas

1) Instala VS Code y la extensión "Pymakr" (búsqueda: Pymakr) desde el Marketplace.
2) Instala drivers del conversor USB‑Serie de tu placa (CP210x o CH340) y conecta el ESP32.
3) Opcional (solo si necesitas flashear el firmware MicroPython):
	- Descarga el firmware estable para ESP32 desde: https://micropython.org/download/ESP32/
	- Instala Python 3.x y esptool:

```powershell
pip install --upgrade esptool
```

	- Identifica el puerto (por ejemplo COM5) en el Administrador de dispositivos.
	- Borra y flashea (ajusta COMx y el nombre del .bin):

```powershell
esptool.py --port COM5 erase_flash
esptool.py --port COM5 --baud 460800 write_flash -z 0x1000 esp32-2024xxxx-v1.22.x.bin
```

## Configuración y uso con Pymakr

1) Abre esta carpeta `MicroPython/ESP32/P1` en VS Code.
2) Conecta el ESP32 por USB. En Pymakr (barra inferior), selecciona el puerto serie (COMx) si no se detecta automáticamente.
3) Pulsa "Connect" para abrir el REPL.
4) Pulsa "Sync project" para subir `boot.py`, `main.py` y `lib/` a la placa.
5) Reinicia la placa (o pulsa "Run"/`Ctrl+D` en el REPL) y observa la salida.

## Qué hace el ejemplo

- `main.py` enciende y apaga el LED (por defecto GPIO 2) cada segundo y escribe "LED ON/OFF" en el REPL.
- Si tu placa usa otro pin para el LED integrado, edita la constante `LED_PIN` en `main.py`.

## Verificación (criterios de aceptación)

- El REPL muestra al arranque: `[boot] Sistema iniciando…`.
- Luego aparecen mensajes `LED ON` / `LED OFF` cada segundo.
- El LED integrado parpadea con el mismo ritmo.

## Solución de problemas

- No ves el puerto COM: instala/actualiza drivers USB‑Serie y cambia de cable USB.
- Puerto ocupado: cierra otros terminales/IDE que usen el mismo COM.
- El LED no parpadea: cambia `LED_PIN` (comúnmente 2, a veces 5 o 13 según la placa).
- Error `ImportError: no module named pycom`: este proyecto ya reemplaza dependencias de Pycom por MicroPython estándar; asegúrate de haber sincronizado `main.py` actualizado.

## Archivos clave

- `boot.py`: Mensaje de arranque, mantenerlo ligero para evitar bloqueos.
- `main.py`: Bucle de parpadeo y mensajes de estado por REPL.
- `pymakr.conf`: Nombre del proyecto y patrones de exclusión durante la sincronización.
- `lib/`: Carpeta para módulos propios/terceros (vacía por ahora).

## Preguntas de reflexión

1. ¿Qué diferencia hay entre `boot.py` y `main.py` en el ciclo de arranque?
2. ¿Cómo aislarías credenciales o configuración sensible en MicroPython?
3. ¿Qué latencias observas al sincronizar con Pymakr y cómo afectan al flujo de trabajo?

## Recursos

- MicroPython (ESP32): https://docs.micropython.org/en/latest/esp32/quickref.html
- Firmware oficial: https://micropython.org/download/ESP32/
- Pymakr (docs): https://docs.pycom.io/pymakr/
