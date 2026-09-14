# Herramientas — P5 RP2040 (Servos PWM)

- `servo_cli.py`: envía ángulos o pulsos por el puerto serie (modos 2 y 3 del firmware).
  Requiere `pyserial` (`pip install -r requirements.txt`).

  ```bash
  python servo_cli.py --port /dev/ttyACM0 angle 90
  python servo_cli.py --port /dev/ttyACM0 pulse 1500
  python servo_cli.py --port /dev/ttyACM0 sweep --min 0 --max 180 --step 5 --delay 0.05
  ```

## Análisis de señales (modos 5–7)

Para los modos de análisis de señales (jitter de PWM, muestreo/aliasing, respuesta al
escalón) usa la toolkit compartida:
[`tools/sisela_signal/`](../../../../tools/sisela_signal/README.md).

```bash
pip install -r ../../../../tools/sisela_signal/requirements.txt
PYTHONPATH=../../../../tools python -m sisela_signal --help
```

Ver [../docs/analisis_senales.md](../docs/analisis_senales.md) para el procedimiento
completo con el generador de funciones y el osciloscopio.
