# Stepper driver for A4988/DRV8825 (STEP/DIR)
try:
    from machine import Pin
    import utime as time
except ImportError:
    Pin = None
    class time:
        @staticmethod
        def sleep_us(us):
            pass

class StepperA4988:
    def __init__(self, pin_step, pin_dir, pin_en=None, step_pulse_us=5, min_step_interval_us=800):
        self.step = Pin(pin_step, Pin.OUT)
        self.dir = Pin(pin_dir, Pin.OUT)
        self.en = Pin(pin_en, Pin.OUT) if pin_en is not None else None
        self.step_pulse_us = step_pulse_us
        self.min_interval = min_step_interval_us
        if self.en:
            self.enable(True)

    def enable(self, state=True):
        if self.en:
            # A4988 enable is LOW active
            self.en.value(0 if state else 1)

    def set_dir(self, cw=True):
        self.dir.value(1 if cw else 0)

    def step_once(self, interval_us=None):
        iv = interval_us or self.min_interval
        # STEP rising edge
        self.step.value(1)
        time.sleep_us(self.step_pulse_us)
        self.step.value(0)
        time.sleep_us(max(iv - self.step_pulse_us, 0))

    def move_steps(self, steps, cw=True, interval_us=None):
        self.set_dir(cw)
        for _ in range(abs(steps)):
            self.step_once(interval_us)

    def move_ramped(self, steps, cw=True, iv_start_us=2000, iv_end_us=800):
        # Linear ramp (simple) across steps
        self.set_dir(cw)
        n = abs(steps)
        for i in range(n):
            if n > 1:
                iv = iv_start_us + (iv_end_us - iv_start_us) * i // (n - 1)
            else:
                iv = iv_end_us
            self.step_once(max(iv, self.step_pulse_us+1))
