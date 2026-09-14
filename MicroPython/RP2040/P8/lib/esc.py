"""
esc.py — Driver de ESC (Electronic Speed Controller) para motores brushless
(p. ej. 2212) mediante señal PWM tipo servo: 50 Hz, pulso 1000–2000 µs.

Un ESC "escucha" la misma señal que un servo, pero la interpreta como
**throttle** (0–100 %), no como ángulo, y exige una secuencia de **armado**
antes de aceptar comandos:

    esc = ESC(pin)          # PWM 50 Hz, 1000–2000 us
    esc.arm()                # sostiene 1000 us ~2 s (obligatorio)
    esc.throttle(20)         # 20 % de potencia
    esc.stop()                # throttle 0 % (sigue armado)
    esc.deinit()               # throttle 0 % + libera el PWM

⚠️ SEGURIDAD — leer antes de energizar el sistema:
  * Retira las hélices para CUALQUIER prueba de banco, calibración o test
    de este módulo. Un motor 2212 con hélice puede causar cortes graves.
  * Alimenta el ESC desde una batería LiPo dedicada (o fuente de banco
    limitada en corriente, p. ej. 3 A), NUNCA desde el riel 5V/3.3V del MCU.
  * Ten siempre una parada de emergencia accesible (ver `stop()`/`disarm()`
    y el modo 8 → opción 5 del firmware de P8).
  * Un ESC sin armar ignora el throttle: `throttle()` lanza `RuntimeError`
    si no se llamó `arm()` antes (fallo seguro por diseño).

Ver docs/dron_2212.md para especificaciones del motor 2212, presupuesto de
potencia, cableado y procedimiento completo de armado/calibración.
"""
from machine import Pin, PWM
import utime


class ESC:
    """Un canal ESC (un motor). Instancia 4 para un cuadricóptero en X."""

    def __init__(self, pin, freq=50, min_us=1000, max_us=2000, label=""):
        self.label = label or "pin{}".format(pin)
        self._pwm = PWM(Pin(pin))
        self._pwm.freq(freq)
        self._period_us = int(1_000_000 / freq)
        self._min_us = min_us
        self._max_us = max_us
        self._armed = False
        self._throttle = 0.0
        self._pulse_us(min_us)  # señal segura (mínimo) desde el arranque

    # -- internos ------------------------------------------------------
    def _pulse_us(self, us):
        us = max(self._min_us, min(self._max_us, us))
        duty = int(us * 65535 / self._period_us)
        self._pwm.duty_u16(duty)
        return us

    # -- API pública -----------------------------------------------------
    def arm(self, hold_s=2.0, verbose=True):
        """Secuencia de armado: throttle mínimo sostenido `hold_s` segundos.

        Ejecutar SIN hélices la primera vez. Algunos ESC emiten pitidos de
        confirmación (nº de celdas de la batería, luego "listo")."""
        if verbose:
            print("[ESC {}] Armando (throttle 0%, {:.1f} s)...".format(self.label, hold_s))
        self._pulse_us(self._min_us)
        utime.sleep_ms(int(hold_s * 1000))
        self._armed = True
        self._throttle = 0.0
        if verbose:
            print("[ESC {}] Armado.".format(self.label))

    def is_armed(self):
        return self._armed

    def throttle(self, percent):
        """Establece throttle 0–100 %. Requiere `arm()` previo (fail-safe)."""
        if not self._armed:
            raise RuntimeError("ESC '{}' no armado: llama a arm() primero.".format(self.label))
        percent = max(0.0, min(100.0, float(percent)))
        us = self._min_us + (percent / 100.0) * (self._max_us - self._min_us)
        self._pulse_us(int(us))
        self._throttle = percent
        return percent

    def get_throttle(self):
        return self._throttle

    def pulse_us(self):
        """Ancho de pulso actual en microsegundos (para medir jitter)."""
        return self._min_us + (self._throttle / 100.0) * (self._max_us - self._min_us)

    def stop(self):
        """Throttle a 0 % sin desarmar (para pausas breves)."""
        self._pulse_us(self._min_us)
        self._throttle = 0.0

    def disarm(self):
        """Detiene y desarma: throttle() volverá a exigir arm()."""
        self.stop()
        self._armed = False

    def deinit(self):
        self.stop()
        utime.sleep_ms(50)
        self._pwm.deinit()
        self._armed = False


class QuadESC:
    """Conjunto de 4 ESC (M1..M4) con utilidades de armado/parada conjuntas."""

    def __init__(self, pins, freq=50, min_us=1000, max_us=2000):
        labels = ("M1_FL", "M2_FR", "M3_RL", "M4_RR")
        self.escs = [ESC(p, freq=freq, min_us=min_us, max_us=max_us, label=labels[i])
                     for i, p in enumerate(pins)]

    def arm_all(self, hold_s=2.0):
        print("[QuadESC] Armando los 4 ESC. Verifica que NO hay hélices montadas.")
        for esc in self.escs:
            esc.arm(hold_s=hold_s, verbose=False)
        print("[QuadESC] Los 4 ESC armados.")

    def set_all(self, throttles):
        """throttles: lista/tupla de 4 valores 0..100 (orden M1..M4)."""
        return [esc.throttle(t) for esc, t in zip(self.escs, throttles)]

    def emergency_stop(self):
        for esc in self.escs:
            esc.stop()

    def disarm_all(self):
        for esc in self.escs:
            esc.disarm()

    def deinit(self):
        for esc in self.escs:
            esc.deinit()

    def pulses_us(self):
        return [esc.pulse_us() for esc in self.escs]
