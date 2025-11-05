#pragma once
#include <Arduino.h>
#include "pins/pins.h"

class LandingGear {
public:
  void begin() {
    #if defined(STEPPER_ULN2003)
      if (PIN_STEPPER_IN1 >= 0) pinMode(PIN_STEPPER_IN1, OUTPUT);
      if (PIN_STEPPER_IN2 >= 0) pinMode(PIN_STEPPER_IN2, OUTPUT);
      if (PIN_STEPPER_IN3 >= 0) pinMode(PIN_STEPPER_IN3, OUTPUT);
      if (PIN_STEPPER_IN4 >= 0) pinMode(PIN_STEPPER_IN4, OUTPUT);
    #else
      if (PIN_STEPPER_STEP >= 0) pinMode(PIN_STEPPER_STEP, OUTPUT);
      if (PIN_STEPPER_DIR >= 0) pinMode(PIN_STEPPER_DIR, OUTPUT);
      if (PIN_STEPPER_EN >= 0) { pinMode(PIN_STEPPER_EN, OUTPUT); digitalWrite(PIN_STEPPER_EN, LOW); }
    #endif
    if (PIN_ENDSTOP >= 0) pinMode(PIN_ENDSTOP, INPUT_PULLUP);
  }

  void stepperStep(int steps, bool dirCW = true, unsigned usDelay = 800) {
    #if defined(STEPPER_ULN2003)
      static const uint8_t seq[8][4] = {
        {1,0,0,0},{1,1,0,0},{0,1,0,0},{0,1,1,0},
        {0,0,1,0},{0,0,1,1},{0,0,0,1},{1,0,0,1}
      };
      int idx = 0;
      for (int s=0; s<abs(steps); ++s) {
        const uint8_t* st = seq[idx];
        digitalWrite(PIN_STEPPER_IN1, st[0]);
        digitalWrite(PIN_STEPPER_IN2, st[1]);
        digitalWrite(PIN_STEPPER_IN3, st[2]);
        digitalWrite(PIN_STEPPER_IN4, st[3]);
        delayMicroseconds(usDelay);
        idx += dirCW ? 1 : -1;
        if (idx < 0) idx = 7; else if (idx > 7) idx = 0;
      }
    #else
      if (PIN_STEPPER_DIR >= 0) digitalWrite(PIN_STEPPER_DIR, dirCW ? HIGH : LOW);
      for (int s=0; s<abs(steps); ++s) {
        digitalWrite(PIN_STEPPER_STEP, HIGH);
        delayMicroseconds(usDelay);
        digitalWrite(PIN_STEPPER_STEP, LOW);
        delayMicroseconds(usDelay);
      }
    #endif
  }

  bool endstopActive() const {
    if (PIN_ENDSTOP < 0) return false;
    return digitalRead(PIN_ENDSTOP) == LOW; // activo a GND
  }
};
