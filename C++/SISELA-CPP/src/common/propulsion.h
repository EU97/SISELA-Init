#pragma once
#include <Arduino.h>
#include "pins/pins.h"

class PropulsionSystem {
  int _pin = -1;
public:
  void begin(int pin = PIN_PWM_MOTOR) {
    _pin = pin;
    if (_pin >= 0) {
      pinMode(_pin, OUTPUT);
      // analogWrite should be available on both cores; frequency default is OK for demo
      analogWrite(_pin, 0);
    }
  }
  void setThrottle(float pct) {
    if (_pin < 0) return;
    if (pct < 0) pct = 0; if (pct > 1) pct = 1;
    int duty = (int)(pct * 255);
    analogWrite(_pin, duty);
  }
};
