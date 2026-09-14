"""
quad_mixer.py — Mezclador de control para cuadricóptero en configuración X
(4 motores, cada uno con su ESC y motor brushless, p. ej. 2212).

Convierte comandos de throttle/roll/pitch/yaw en 4 valores de throttle por
motor (0–100 %):

              CW  M1 ┐      ┌ M2  CCW
        (front-left)  \\    /  (front-right)
                        \\  /
                         ⌂⌂         ← frente del dron
                        /  \\
        (rear-left)    /    \\  (rear-right)
             CCW  M3 ┘      └ M4  CW

    M1 = throttle + roll - pitch + yaw
    M2 = throttle - roll - pitch - yaw
    M3 = throttle + roll + pitch - yaw
    M4 = throttle - roll + pitch + yaw

⚠️ Este mezclador es de **lazo abierto**: no hay IMU ni PID, así que no
estabiliza un vuelo real. Es la capa de actuación de bajo nivel (throttle →
señal ESC) sobre la que se puede construir un controlador de vuelo completo.
Ver docs/dron_2212.md, sección "Ruta de extensión a vuelo estabilizado".
"""


def mix_x(throttle, roll=0.0, pitch=0.0, yaw=0.0, authority=0.5):
    """
    throttle : 0..100 (%)
    roll, pitch, yaw : -100..100 (autoridad relativa de cada eje)
    authority : fracción de `roll`/`pitch`/`yaw` que se aplica (0..1);
                limita cuánto puede desviar cada eje el throttle base.

    Retorna [m1, m2, m3, m4], cada uno recortado a 0..100.
    """
    r = roll * authority
    p = pitch * authority
    y = yaw * authority
    raw = (
        throttle + r - p + y,   # M1 front-left  (CW)
        throttle - r - p - y,   # M2 front-right (CCW)
        throttle + r + p - y,   # M3 rear-left   (CCW)
        throttle - r + p + y,   # M4 rear-right  (CW)
    )
    return [0.0 if v < 0.0 else (100.0 if v > 100.0 else v) for v in raw]


def mix_x_report(throttle, roll=0.0, pitch=0.0, yaw=0.0, authority=0.5):
    """Como mix_x(), pero además regresa un texto legible para el REPL."""
    m = mix_x(throttle, roll, pitch, yaw, authority)
    txt = "M1={:5.1f}%  M2={:5.1f}%  M3={:5.1f}%  M4={:5.1f}%".format(*m)
    return m, txt
