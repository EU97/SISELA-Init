# Stepper driver for ULN2003 + 28BYJ-48
# 🔄 COMPATIBLE con ESP32 y RP2040
try:
    from machine import Pin
    import utime as time
except ImportError:
    Pin = None
    class time:
        @staticmethod
        def sleep_ms(ms):
            pass

FULLSTEP_SEQ = (
    (1,0,0,0),
    (0,1,0,0),
    (0,0,1,0),
    (0,0,0,1),
)

HALFSTEP_SEQ = (
    (1,0,0,0),
    (1,1,0,0),
    (0,1,0,0),
    (0,1,1,0),
    (0,0,1,0),
    (0,0,1,1),
    (0,0,0,1),
    (1,0,0,1),
)

class StepperULN2003:
    def __init__(self, pins, halfstep=True, step_delay_ms=3):
        if len(pins) != 4:
            raise ValueError("Se requieren 4 pines para ULN2003")
        self.coils = [Pin(p, Pin.OUT) for p in pins]
        self.seq = HALFSTEP_SEQ if halfstep else FULLSTEP_SEQ
        self.delay = step_delay_ms
        self.pos = 0

    def _write_seq(self, idx):
        s = self.seq[idx]
        for coil, val in zip(self.coils, s):
            coil.value(val)

    def step(self, steps, interval_us=None):
        n = len(self.seq)
        inc = 1 if steps > 0 else -1
        for _ in range(abs(steps)):
            self.pos = (self.pos + inc) % n
            self._write_seq(self.pos)
            time.sleep_ms(self.delay)

    def release(self):
        for c in self.coils:
            c.value(0)

    def disable(self):
        self.release()
