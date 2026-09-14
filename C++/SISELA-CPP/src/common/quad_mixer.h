#pragma once

// ============================================================================
// quad_mixer.h — Mezclador de control para cuadricóptero en configuración X.
// Ver MicroPython/*/P8/lib/quad_mixer.py para el diagrama y las ecuaciones.
//
//     M1 = throttle + roll - pitch + yaw   (front-left,  CW)
//     M2 = throttle - roll - pitch - yaw   (front-right, CCW)
//     M3 = throttle + roll + pitch - yaw   (rear-left,   CCW)
//     M4 = throttle - roll + pitch + yaw   (rear-right,  CW)
//
// Lazo abierto (sin IMU ni PID) — capa de actuación de bajo nivel. Ver
// docs/dron_2212.md, "Ruta de extensión a vuelo estabilizado".
// ============================================================================

inline void mixX(float throttle, float roll, float pitch, float yaw,
                 float out[4], float authority = 0.5f) {
  float r = roll * authority, p = pitch * authority, y = yaw * authority;
  float raw[4] = {
    throttle + r - p + y,
    throttle - r - p - y,
    throttle + r + p - y,
    throttle - r + p + y,
  };
  for (int i = 0; i < 4; i++) {
    float v = raw[i];
    out[i] = v < 0.0f ? 0.0f : (v > 100.0f ? 100.0f : v);
  }
}
