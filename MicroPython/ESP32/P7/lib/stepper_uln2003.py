# Stepper driver for ULN2003 + 28BYJ-48
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
    def __init__(self, in1, in2, in3, in4, halfstep=True, step_delay_ms=3):
        self.coils = [Pin(in1, Pin.OUT), Pin(in2, Pin.OUT), Pin(in3, Pin.OUT), Pin(in4, Pin.OUT)]
        self.seq = HALFSTEP_SEQ if halfstep else FULLSTEP_SEQ
        self.delay = step_delay_ms
        self.pos = 0

    def _write_seq(self, idx):
        s = self.seq[idx]
        for coil, val in zip(self.coils, s):
            coil.value(val)

    def step(self, steps, cw=True):
        n = len(self.seq)
        inc = 1 if cw else -1
        for _ in range(abs(steps)):
            self.pos = (self.pos + inc) % n
            self._write_seq(self.pos)
            time.sleep_ms(self.delay)

    def release(self):
        for c in self.coils:
            c.value(0)
