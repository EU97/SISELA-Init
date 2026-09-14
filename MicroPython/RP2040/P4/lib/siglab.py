"""
siglab.py — utilidades de análisis de señales en el microcontrolador (SISELA-Init)

Compañero embebido de la toolkit PC `tools/sisela_signal/`. Se encarga de la
ADQUISICIÓN a tasa fija y de estadística ligera en el dispositivo; el DSP pesado
(FFT, filtros IIR, Bode, ENOB) vive en la PC.

Componentes:
  * BlockSampler   — captura un bloque de N muestras a Fs fija con planificación
                     por `ticks_us` (Fs real + jitter reportados).
  * stream_csv     — emite un stream CSV `t_us,ch0[,ch1,...]` con cadencia real
                     (sin la deriva de `sleep_ms`), consumido por `sisela_signal capture`.
  * Stats          — media / desv. típica / min / max / RMS / pp incremental (Welford).
  * MovAvg, median3, median5 — filtros mínimos para demos en vivo.
  * goertzel       — potencia de un solo bin (detección de tono / pista de THD),
                     sin FFT completa.

Portabilidad: funciona en MicroPython (ESP32 / RP2040) y también importa en CPython
(para análisis estático); en CPython las funciones de tiempo son aproximadas.

`read_fn` es SIEMPRE un callable que devuelve un número:
    ESP32   : lambda: adc.read()          # 0..4095   (12 bit)
    RP2040  : lambda: adc.read_u16()      # 0..65535  (16 bit)
    P4      : lambda: sensor.read_all()[2] # altitud en m (serie digital)
"""

try:
    import utime as _t

    def _ticks_us():
        return _t.ticks_us()

    def _ticks_diff(a, b):
        return _t.ticks_diff(a, b)

    def _sleep_us(us):
        if us > 0:
            _t.sleep_us(us)
    _MICROPYTHON = True
except ImportError:  # CPython (análisis estático / pruebas)
    import time as _t

    def _ticks_us():
        return int(_t.perf_counter() * 1_000_000)

    def _ticks_diff(a, b):
        return a - b

    def _sleep_us(us):
        if us > 0:
            _t.sleep(us / 1_000_000.0)
    _MICROPYTHON = False

try:
    import uselect as _uselect
    import sys as _sys
    _HAVE_POLL = True
except ImportError:
    try:
        import select as _uselect
        import sys as _sys
        _HAVE_POLL = hasattr(_uselect, "poll")
    except ImportError:  # pragma: no cover
        _HAVE_POLL = False


# ---------------------------------------------------------------------------
# Entrada REPL sin bloqueo (para abortar un modo con 'm' + ENTER)
# ---------------------------------------------------------------------------
def key_pressed(target="m"):
    """True si el usuario escribió `target` (+ ENTER) en el REPL. No bloquea."""
    if not _HAVE_POLL:
        return False
    try:
        p = _uselect.poll()
        p.register(_sys.stdin, _uselect.POLLIN)
        if p.poll(0):
            line = _sys.stdin.readline()
            return line.strip().lower() == target
    except Exception:
        return False
    return False


# ---------------------------------------------------------------------------
# Estadística incremental (Welford) — media, varianza, min/max, RMS, pico-a-pico
# ---------------------------------------------------------------------------
class Stats:
    def __init__(self):
        self.n = 0
        self._mean = 0.0
        self._m2 = 0.0
        self._sumsq = 0.0
        self.min = None
        self.max = None

    def add(self, x):
        x = float(x)
        self.n += 1
        d = x - self._mean
        self._mean += d / self.n
        self._m2 += d * (x - self._mean)
        self._sumsq += x * x
        if self.min is None or x < self.min:
            self.min = x
        if self.max is None or x > self.max:
            self.max = x
        return x

    @property
    def mean(self):
        return self._mean

    @property
    def variance(self):
        return self._m2 / self.n if self.n > 1 else 0.0

    @property
    def std(self):
        return self.variance ** 0.5

    @property
    def rms(self):
        return (self._sumsq / self.n) ** 0.5 if self.n else 0.0

    @property
    def pp(self):
        if self.min is None:
            return 0.0
        return self.max - self.min

    def effective_bits(self, full_scale):
        """Resolución efectiva (bits) frente al ruido: log2(FS / (sqrt(12)*sigma))."""
        s = self.std
        if s <= 0.0:
            return float("inf")
        import math
        return math.log(full_scale / (12.0 ** 0.5 * s), 2)

    def report(self, unit=""):
        u = (" " + unit) if unit else ""
        return ("n={:d}  media={:.4f}{u}  sigma={:.5f}{u}  rms={:.4f}{u}  "
                "pp={:.5f}{u}  min={:.4f}  max={:.4f}").format(
            self.n, self.mean, self.std, self.rms, self.pp,
            self.min if self.min is not None else 0.0,
            self.max if self.max is not None else 0.0, u=u)


# ---------------------------------------------------------------------------
# Captura en bloque a Fs fija
# ---------------------------------------------------------------------------
class BlockResult:
    __slots__ = ("samples", "fs_nominal", "fs_actual", "jitter_us",
                 "dt_min_us", "dt_max_us", "t_us")

    def __init__(self, samples, t_us, fs_nominal):
        self.samples = samples
        self.t_us = t_us
        self.fs_nominal = fs_nominal
        n = len(t_us)
        if n >= 2:
            dts = [t_us[i] - t_us[i - 1] for i in range(1, n)]
            mean_dt = sum(dts) / len(dts)
            self.fs_actual = 1_000_000.0 / mean_dt if mean_dt > 0 else 0.0
            var = sum((d - mean_dt) ** 2 for d in dts) / len(dts)
            self.jitter_us = var ** 0.5
            self.dt_min_us = min(dts)
            self.dt_max_us = max(dts)
        else:
            self.fs_actual = 0.0
            self.jitter_us = 0.0
            self.dt_min_us = self.dt_max_us = 0.0

    def report(self):
        return ("Fs solicitada={:.1f} Hz | Fs real={:.1f} Hz ({:+.2f} %) | "
                "jitter σ={:.2f} µs | dt=[{:.1f}, {:.1f}] µs | n={:d}").format(
            self.fs_nominal, self.fs_actual,
            100.0 * (self.fs_actual - self.fs_nominal) / self.fs_nominal
            if self.fs_nominal else 0.0,
            self.jitter_us, self.dt_min_us, self.dt_max_us, len(self.samples))


class BlockSampler:
    """
    Captura N muestras a `fs_hz` llamando `read_fn()` en cada instante.

        bs = BlockSampler(lambda: adc.read_u16(), fs_hz=5000, n=2048)
        res = bs.run()
        print(res.report())
        bs.dump_csv(res)          # imprime t_us,ch0 para la toolkit PC
    """

    def __init__(self, read_fn, fs_hz, n):
        self.read_fn = read_fn
        self.fs_hz = float(fs_hz)
        self.n = int(n)
        self.period_us = int(1_000_000.0 / self.fs_hz)

    def run(self):
        n = self.n
        period = self.period_us
        read = self.read_fn
        samples = [0] * n
        t_us = [0] * n
        t0 = _ticks_us()
        next_t = t0
        for i in range(n):
            # espera activa hasta el instante planificado
            while _ticks_diff(_ticks_us(), next_t) < 0:
                pass
            samples[i] = read()
            t_us[i] = _ticks_diff(_ticks_us(), t0)
            next_t += period
        return BlockResult(samples, t_us, self.fs_hz)

    @staticmethod
    def dump_csv(res, col="ch0"):
        print("t_us,{}".format(col))
        s = res.samples
        t = res.t_us
        for i in range(len(s)):
            print("{},{}".format(t[i], s[i]))
        print("# end n={} fs_actual={:.1f} jitter_us={:.2f}".format(
            len(s), res.fs_actual, res.jitter_us))


# ---------------------------------------------------------------------------
# Stream CSV continuo a cadencia real (para `sisela_signal capture`)
# ---------------------------------------------------------------------------
def stream_csv(read_fn, fs_hz, cols=("ch0",), max_samples=0, stop_key="m",
               header=True):
    """
    Emite `t_us,<cols>` a `fs_hz` con planificación por `ticks_us`. `read_fn`
    devuelve un escalar (1 columna) o una tupla/lista (varias columnas).

    Se detiene con `stop_key` + ENTER, o tras `max_samples` (0 = ilimitado).
    """
    if isinstance(cols, str):
        cols = (cols,)
    if header:
        print("t_us," + ",".join(cols))
    period_us = int(1_000_000.0 / float(fs_hz))
    t0 = _ticks_us()
    next_t = t0
    i = 0
    while True:
        while _ticks_diff(_ticks_us(), next_t) < 0:
            pass
        v = read_fn()
        t = _ticks_diff(_ticks_us(), t0)
        if isinstance(v, (tuple, list)):
            print("{},".format(t) + ",".join(_fmt(x) for x in v))
        else:
            print("{},{}".format(t, _fmt(v)))
        next_t += period_us
        i += 1
        if max_samples and i >= max_samples:
            break
        if stop_key and (i & 0x1F) == 0 and key_pressed(stop_key):
            break
    print("# end n={}".format(i))
    return i


def _fmt(x):
    if isinstance(x, float):
        return "{:.5f}".format(x)
    return str(x)


# ---------------------------------------------------------------------------
# Filtros mínimos en el dispositivo (demos en vivo)
# ---------------------------------------------------------------------------
class MovAvg:
    """Media móvil de ventana N."""

    def __init__(self, n):
        self.n = max(1, int(n))
        self.buf = [0.0] * self.n
        self.idx = 0
        self.count = 0
        self.sum = 0.0

    def add(self, x):
        x = float(x)
        self.sum -= self.buf[self.idx]
        self.buf[self.idx] = x
        self.sum += x
        self.idx = (self.idx + 1) % self.n
        if self.count < self.n:
            self.count += 1
        return self.sum / self.count


class Ema:
    """Filtro exponencial de 1er orden: y += alpha*(x - y)."""

    def __init__(self, alpha, y0=0.0):
        self.alpha = float(alpha)
        self.y = float(y0)
        self._init = False

    def add(self, x):
        x = float(x)
        if not self._init:
            self.y = x
            self._init = True
        else:
            self.y += self.alpha * (x - self.y)
        return self.y

    @staticmethod
    def alpha_for_cutoff(fc, fs):
        import math
        dt = 1.0 / fs
        rc = 1.0 / (2.0 * math.pi * fc)
        return dt / (rc + dt)


def median3(a, b, c):
    """Mediana de 3 valores (quita spikes de 1 muestra)."""
    if a > b:
        a, b = b, a
    if b > c:
        b, c = c, b
    if a > b:
        a, b = b, a
    return b


class Median:
    """Mediana deslizante de ventana impar N (N pequeño: 3, 5, 7)."""

    def __init__(self, n=5):
        self.n = int(n) | 1
        self.buf = []

    def add(self, x):
        self.buf.append(float(x))
        if len(self.buf) > self.n:
            self.buf.pop(0)
        s = sorted(self.buf)
        return s[len(s) // 2]


# ---------------------------------------------------------------------------
# Goertzel — potencia de un solo bin (sin FFT)
# ---------------------------------------------------------------------------
def goertzel(samples, f_target, fs):
    """
    Potencia (magnitud²) del bin de frecuencia `f_target` en `samples`.
    Útil para medir la amplitud de un tono conocido o estimar THD comparando
    la fundamental con sus armónicos, sin una FFT completa.
    """
    import math
    n = len(samples)
    if n == 0 or fs <= 0:
        return 0.0
    k = int(0.5 + (n * f_target) / fs)
    w = (2.0 * math.pi / n) * k
    cw = math.cos(w)
    coeff = 2.0 * cw
    s_prev = 0.0
    s_prev2 = 0.0
    mean = sum(samples) / n
    for x in samples:
        s = (x - mean) + coeff * s_prev - s_prev2
        s_prev2 = s_prev
        s_prev = s
    power = s_prev2 * s_prev2 + s_prev * s_prev - coeff * s_prev * s_prev2
    return power / (n * n / 4.0)


def goertzel_amplitude(samples, f_target, fs):
    """Amplitud aproximada del tono f_target (goertzel() ya devuelve ~A²)."""
    return goertzel(samples, f_target, fs) ** 0.5


def thd_hint(samples, f0, fs, n_harm=5):
    """
    Estimación rápida de THD (%) por Goertzel: sqrt(sum(P_hk)) / sqrt(P_f0).
    Solo válida si f0 y sus armónicos están por debajo de Fs/2.
    """
    p0 = goertzel(samples, f0, fs)
    if p0 <= 0:
        return 0.0
    ph = 0.0
    nyq = fs / 2.0
    for h in range(2, n_harm + 2):
        fh = f0 * h
        if fh >= nyq:
            break
        ph += goertzel(samples, fh, fs)
    return 100.0 * (ph / p0) ** 0.5


# ---------------------------------------------------------------------------
# Ayuda de nivel: valor recomendado de Fs para no violar Nyquist
# ---------------------------------------------------------------------------
def nyquist_ok(f_signal_max, fs):
    """True si fs cumple Nyquist con margen (fs >= 2.5 * f_signal_max)."""
    return fs >= 2.5 * f_signal_max


def alias_of(f, fs):
    """Frecuencia aparente de un tono `f` muestreado a `fs` (para el modo demo)."""
    fn = fs / 2.0
    r = f % fs
    return fs - r if r > fn else r
