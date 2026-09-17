# Herramientas — P5 (Servos PWM)

Este directorio incluye utilidades para interactuar con el firmware de servos:

- `servo_cli.py`: envía ángulos o pulsos por el puerto serie (para usar con Modo 2 o 3).
- Para captura/análisis de señales de los Modos 5–7 (jitter PWM, muestreo/aliasing,
  respuesta al escalón), usa la toolkit compartida `tools/sisela_signal` (raíz del repo):
  `python -m sisela_signal capture --port COM5 --menu 6 --out captura.csv` y
  `python -m sisela_signal spectrum --file captura.csv --col v`. Ver `docs/analisis_senales.md`.

## Instalación (Windows)

1) Abre PowerShell en esta carpeta.
2) Crea (opcional) un entorno virtual y/o instala dependencias:

```powershell
# Opción A: usar el lanzador de Python en Windows
py -m pip install -r requirements.txt

# Opción B: si el comando `python` está configurado
python -m pip install -r requirements.txt
```

## Uso rápido: CLI de servo

Con el ESP32 en Modo 2 (ángulo) o Modo 3 (pulso), ejecuta desde PowerShell:

```powershell
# Establecer ángulo a 90°
py servo_cli.py --port COM5 angle 90

# Barrido 0–180–0 en pasos de 5°
py servo_cli.py --port COM5 sweep --min 0 --max 180 --step 5 --delay 0.05

# Enviar un pulso de 1500 us (Modo 3)
py servo_cli.py --port COM5 pulse 1500
```

## Notas

- Asegúrate de que el firmware esté en el modo correspondiente (2 o 3) antes de usar la CLI.
- Cambia `COM5` por tu puerto serie.
