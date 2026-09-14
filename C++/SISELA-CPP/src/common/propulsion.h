#pragma once
#include <Arduino.h>
#include "pins/pins.h"

// PropulsionSystem — control de potencia por PWM (motor DC / MOSFET / ESC).
//
// API en PORCENTAJE (0–100), no en fracción 0–1. Se usa desde P6 (conmutación
// de potencia) y P8 (propulsión + módulo de dron). `setThrottle()` acepta
// cualquier valor y lo recorta a [0,100] antes de convertirlo a duty de 8
// bits (analogWrite).
class PropulsionSystem {
  int _pin = -1;
  float _throttle = 0.0f;  // último valor aplicado, en %
 public:
  void begin(int pin = PIN_PWM_MOTOR) {
    _pin = pin;
    if (_pin >= 0) {
      pinMode(_pin, OUTPUT);
      analogWrite(_pin, 0);
    }
    _throttle = 0.0f;
  }

  // percent: 0–100. Valores fuera de rango se recortan (no se interpretan
  // como fracción 0–1).
  float setThrottle(float percent) {
    if (_pin < 0) return 0.0f;
    if (percent < 0) percent = 0; if (percent > 100) percent = 100;
    _throttle = percent;
    int duty = (int)((percent / 100.0f) * 255.0f + 0.5f);
    analogWrite(_pin, duty);
    return _throttle;
  }

  float getThrottle() const { return _throttle; }

  void emergencyStop() { setThrottle(0); }

  // Rampa suave bloqueante (uso educativo en banco de pruebas).
  void rampTo(float targetPercent, uint32_t durationMs = 2000, int steps = 20) {
    float start = _throttle;
    if (targetPercent < 0) targetPercent = 0; if (targetPercent > 100) targetPercent = 100;
    uint32_t stepDelay = durationMs / (steps > 0 ? steps : 1);
    float delta = (targetPercent - start) / steps;
    for (int i = 0; i < steps; i++) {
      setThrottle(start + delta * (i + 1));
      delay(stepDelay);
    }
  }
};
