"""
Servo helper for MicroPython (RP2040)

- 50 Hz PWM (20 ms period)
- Angle mapping to pulse width (us)
- Also allows direct pulse_us control

🔄 COMPATIBLE con ESP32 y RP2040
Usa duty_u16() que funciona en ambas plataformas.
"""
try:
    from machine import Pin, PWM
    import utime as time
except ImportError:  # allow import on PC editors
    Pin = None
    PWM = None
    time = None


class Servo:
    def __init__(self, pin, *, freq=50, min_us=500, max_us=2400, angle_min=0, angle_max=180):
        if PWM is None:
            raise RuntimeError("Servo requires MicroPython machine.PWM")
        self._pin = pin
        self._pwm = PWM(Pin(pin))
        self._pwm.freq(freq)
        self._freq = freq
        self._period_us = int(1_000_000 // freq)
        self._min_us = int(min_us)
        self._max_us = int(max_us)
        self._angle_min = int(angle_min)
        self._angle_max = int(angle_max)
        # initialize to middle position
        self.angle((self._angle_min + self._angle_max) // 2)

    def deinit(self):
        try:
            self._pwm.deinit()
        except (AttributeError, OSError):
            pass

    def pulse_us(self, micros):
        # clamp to configured bounds
        if micros < self._min_us:
            micros = self._min_us
        if micros > self._max_us:
            micros = self._max_us
        duty_u16 = int(micros * 65535 // self._period_us)
        self._pwm.duty_u16(duty_u16)
        return micros

    def angle(self, degrees):
        # clamp angle
        if degrees < self._angle_min:
            degrees = self._angle_min
        if degrees > self._angle_max:
            degrees = self._angle_max
        # linear map to pulse us
        span_deg = self._angle_max - self._angle_min
        if span_deg <= 0:
            span_deg = 1
        ratio = (degrees - self._angle_min) / span_deg
        micros = int(self._min_us + ratio * (self._max_us - self._min_us))
        return self.pulse_us(micros)

    def sweep(self, start=0, end=180, step=2, delay_ms=20):
        if time is None:
            raise RuntimeError("Requires MicroPython utime module")
        if start > end:
            step = -abs(step)
        else:
            step = abs(step)
        for a in range(start, end + step, step):
            self.angle(a)
            time.sleep_ms(delay_ms)
