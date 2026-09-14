#pragma once
#include <Arduino.h>
#include <math.h>

// ============================================================================
// siglab.h — utilidades de análisis de señales en el microcontrolador (C++)
//
// Compañero embebido de la toolkit PC `tools/sisela_signal/`. Adquisición a Fs
// fija + estadística ligera en el dispositivo; el DSP pesado (FFT, IIR, Bode,
// ENOB) vive en la PC.
//
//   siglab::BlockSampler<2048> bs(5000.0f);
//   auto r = bs.run([](){ return (float)analogRead(A0); });
//   r.report(Serial);
//   bs.dumpCsv(Serial, r, "ch0");
//
//   siglab::Stats st;  st.add(x); ... st.report(Serial, "LSB");
//   float thd = siglab::thdHint(buf, n, f0, fs);
//
// Nota RP2040: llamar `analogReadResolution(12)` en setup() para igualar la
// resolución de MicroPython (12 bit) — por defecto el core Arduino da 10 bit.
// ============================================================================

namespace siglab {

// ---------------------------------------------------------------------------
// Estadística incremental (Welford)
// ---------------------------------------------------------------------------
class Stats {
  uint32_t _n = 0;
  double _mean = 0.0, _m2 = 0.0, _sumsq = 0.0;
  double _min = 0.0, _max = 0.0;
 public:
  void add(double x) {
    _n++;
    double d = x - _mean;
    _mean += d / _n;
    _m2 += d * (x - _mean);
    _sumsq += x * x;
    if (_n == 1) { _min = _max = x; }
    else { if (x < _min) _min = x; if (x > _max) _max = x; }
  }
  uint32_t n() const { return _n; }
  double mean() const { return _mean; }
  double variance() const { return _n > 1 ? _m2 / _n : 0.0; }
  double stddev() const { return sqrt(variance()); }
  double rms() const { return _n ? sqrt(_sumsq / _n) : 0.0; }
  double pp() const { return _max - _min; }
  double minv() const { return _min; }
  double maxv() const { return _max; }
  // Resolución efectiva (bits): log2(FS / (sqrt(12)*sigma))
  double effectiveBits(double fullScale) const {
    double s = stddev();
    return s > 0.0 ? log(fullScale / (sqrt(12.0) * s)) / log(2.0) : INFINITY;
  }
  void report(Stream &io, const char *unit = "") const {
    io.printf("n=%lu media=%.4f%s sigma=%.5f%s rms=%.4f%s pp=%.5f%s min=%.4f max=%.4f\n",
              (unsigned long)_n, _mean, unit, stddev(), unit, rms(), unit,
              pp(), unit, _min, _max);
  }
};

// ---------------------------------------------------------------------------
// Captura en bloque a Fs fija (planificación por micros())
// ---------------------------------------------------------------------------
template <uint16_t N>
struct BlockResult {
  float samples[N];
  uint32_t t_us[N];
  float fs_nominal = 0.0f;
  float fs_actual = 0.0f;
  float jitter_us = 0.0f;
  uint32_t dt_min_us = 0, dt_max_us = 0;

  void compute() {
    if (N < 2) return;
    double sum = 0.0;
    dt_min_us = 0xFFFFFFFFUL;
    dt_max_us = 0;
    for (uint16_t i = 1; i < N; i++) {
      uint32_t d = t_us[i] - t_us[i - 1];
      sum += d;
      if (d < dt_min_us) dt_min_us = d;
      if (d > dt_max_us) dt_max_us = d;
    }
    double meanDt = sum / (N - 1);
    fs_actual = meanDt > 0 ? (float)(1e6 / meanDt) : 0.0f;
    double var = 0.0;
    for (uint16_t i = 1; i < N; i++) {
      double d = (double)(t_us[i] - t_us[i - 1]) - meanDt;
      var += d * d;
    }
    jitter_us = (float)sqrt(var / (N - 1));
  }

  void report(Stream &io) const {
    float err = fs_nominal ? 100.0f * (fs_actual - fs_nominal) / fs_nominal : 0.0f;
    io.printf("Fs solicitada=%.1f Hz | Fs real=%.1f Hz (%+.2f %%) | "
              "jitter sigma=%.2f us | dt=[%lu, %lu] us | n=%u\n",
              fs_nominal, fs_actual, err, jitter_us,
              (unsigned long)dt_min_us, (unsigned long)dt_max_us, (unsigned)N);
  }
};

template <uint16_t N>
class BlockSampler {
  float _fs;
  uint32_t _period_us;
 public:
  explicit BlockSampler(float fs_hz) : _fs(fs_hz),
      _period_us((uint32_t)(1e6f / fs_hz)) {}

  template <typename ReadFn>
  BlockResult<N> run(ReadFn read) {
    BlockResult<N> r;
    r.fs_nominal = _fs;
    uint32_t t0 = micros();
    uint32_t next = t0;
    for (uint16_t i = 0; i < N; i++) {
      while ((int32_t)(micros() - next) < 0) { /* espera activa */ }
      r.samples[i] = (float)read();
      r.t_us[i] = micros() - t0;
      next += _period_us;
    }
    r.compute();
    return r;
  }

  void dumpCsv(Stream &io, const BlockResult<N> &r, const char *col = "ch0") {
    io.printf("t_us,%s\n", col);
    for (uint16_t i = 0; i < N; i++)
      io.printf("%lu,%.5f\n", (unsigned long)r.t_us[i], r.samples[i]);
    io.printf("# end n=%u fs_actual=%.1f jitter_us=%.2f\n",
              (unsigned)N, r.fs_actual, r.jitter_us);
  }
};

// ---------------------------------------------------------------------------
// Stream CSV continuo a cadencia real (para `sisela_signal capture`)
// ---------------------------------------------------------------------------
// Emite `t_us,<col>` a fs_hz hasta que llega 'm' por Serial o se alcanza
// max_samples (0 = ilimitado). Devuelve el nº de muestras emitidas.
template <typename ReadFn>
uint32_t streamCsv(Stream &io, ReadFn read, float fs_hz,
                   const char *col = "ch0", uint32_t max_samples = 0,
                   char stop_key = 'm') {
  io.printf("t_us,%s\n", col);
  uint32_t period_us = (uint32_t)(1e6f / fs_hz);
  uint32_t t0 = micros();
  uint32_t next = t0;
  uint32_t i = 0;
  while (true) {
    while ((int32_t)(micros() - next) < 0) { /* espera activa */ }
    float v = (float)read();
    io.printf("%lu,%.5f\n", (unsigned long)(micros() - t0), v);
    next += period_us;
    i++;
    if (max_samples && i >= max_samples) break;
    if ((i & 0x1F) == 0 && io.available() && io.read() == stop_key) break;
  }
  io.printf("# end n=%lu\n", (unsigned long)i);
  return i;
}

// ---------------------------------------------------------------------------
// Filtros mínimos
// ---------------------------------------------------------------------------
template <uint16_t N>
class MovAvg {
  float _buf[N] = {0};
  uint16_t _idx = 0, _count = 0;
  double _sum = 0.0;
 public:
  float add(float x) {
    _sum -= _buf[_idx];
    _buf[_idx] = x;
    _sum += x;
    _idx = (_idx + 1) % N;
    if (_count < N) _count++;
    return (float)(_sum / _count);
  }
};

class Ema {
  float _a, _y = 0.0f;
  bool _init = false;
 public:
  explicit Ema(float alpha) : _a(alpha) {}
  float add(float x) {
    if (!_init) { _y = x; _init = true; }
    else _y += _a * (x - _y);
    return _y;
  }
  static float alphaForCutoff(float fc, float fs) {
    float dt = 1.0f / fs;
    float rc = 1.0f / (2.0f * PI * fc);
    return dt / (rc + dt);
  }
};

inline float median3(float a, float b, float c) {
  if (a > b) { float t = a; a = b; b = t; }
  if (b > c) { float t = b; b = c; c = t; }
  if (a > b) { float t = a; a = b; b = t; }
  return b;
}

// ---------------------------------------------------------------------------
// Goertzel — potencia de un solo bin (sin FFT)
// ---------------------------------------------------------------------------
inline float goertzelPower(const float *x, uint16_t n, float fTarget, float fs) {
  if (n == 0 || fs <= 0.0f) return 0.0f;
  int k = (int)(0.5f + (n * fTarget) / fs);
  float w = (2.0f * PI / n) * k;
  float coeff = 2.0f * cosf(w);
  double mean = 0.0;
  for (uint16_t i = 0; i < n; i++) mean += x[i];
  mean /= n;
  double s_prev = 0.0, s_prev2 = 0.0;
  for (uint16_t i = 0; i < n; i++) {
    double s = (x[i] - mean) + coeff * s_prev - s_prev2;
    s_prev2 = s_prev;
    s_prev = s;
  }
  double p = s_prev2 * s_prev2 + s_prev * s_prev - coeff * s_prev * s_prev2;
  return (float)(p / ((double)n * n / 4.0));  // ~A^2 para un tono de amplitud A
}

inline float goertzelAmplitude(const float *x, uint16_t n, float fTarget, float fs) {
  return sqrtf(goertzelPower(x, n, fTarget, fs));
}

// THD (%) aproximada por Goertzel: sqrt(sum(P_hk) / P_f0)
inline float thdHint(const float *x, uint16_t n, float f0, float fs, int nHarm = 5) {
  float p0 = goertzelPower(x, n, f0, fs);
  if (p0 <= 0.0f) return 0.0f;
  float ph = 0.0f;
  float nyq = fs / 2.0f;
  for (int h = 2; h <= nHarm + 1; h++) {
    float fh = f0 * h;
    if (fh >= nyq) break;
    ph += goertzelPower(x, n, fh, fs);
  }
  return 100.0f * sqrtf(ph / p0);
}

// ---------------------------------------------------------------------------
// Ayudas de nivel
// ---------------------------------------------------------------------------
inline bool nyquistOk(float fSignalMax, float fs) { return fs >= 2.5f * fSignalMax; }

inline float aliasOf(float f, float fs) {
  float fn = fs / 2.0f;
  float r = fmodf(f, fs);
  return r > fn ? fs - r : r;
}

}  // namespace siglab
