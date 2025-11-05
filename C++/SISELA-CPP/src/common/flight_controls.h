#pragma once
#include <Arduino.h>
#include "pins/pins.h"

#ifdef ARDUINO_ARCH_ESP32
#include <ESP32Servo.h>
#elif defined(ARDUINO_ARCH_RP2040)
// RP2040 usa PWM nativo para servos (50 Hz, 1000-2000 µs)
#endif

// Control de servos R/C con PWM de 50 Hz real
// ESP32: usa librería ESP32Servo
// RP2040: usa PWM nativo (analogWriteFreq + analogWrite)
class FlightControls {
#ifdef ARDUINO_ARCH_ESP32
  Servo _servoAil, _servoElev;
#elif defined(ARDUINO_ARCH_RP2040)
  int _ail = -1, _elev = -1;
#endif
  int _ailAngle = 90, _elevAngle = 90;

public:
  void begin(int ail = PIN_SERVO_AILERON, int elev = PIN_SERVO_ELEVATOR) {
#ifdef ARDUINO_ARCH_ESP32
    // ESP32Servo: attach con rango 1000-2000 µs (estándar R/C)
    if (ail >= 0) {
      _servoAil.attach(ail, 1000, 2000);
      _servoAil.write(90); // Centro inicial
    }
    if (elev >= 0) {
      _servoElev.attach(elev, 1000, 2000);
      _servoElev.write(90);
    }
#elif defined(ARDUINO_ARCH_RP2040)
    // RP2040: PWM nativo a 50 Hz con analogWriteFreq
    _ail = ail; _elev = elev;
    if (_ail >= 0) {
      pinMode(_ail, OUTPUT);
      analogWriteFreq(50); // 50 Hz para servos R/C
      analogWriteRange(20000); // Periodo 20 ms = 20000 µs
      setAileron(90); // Centro inicial
    }
    if (_elev >= 0) {
      pinMode(_elev, OUTPUT);
      analogWriteFreq(50);
      analogWriteRange(20000);
      setElevator(90);
    }
#endif
  }

  void setAileron(int angle) {
    _ailAngle = constrain(angle, 0, 180);
#ifdef ARDUINO_ARCH_ESP32
    if (_servoAil.attached()) _servoAil.write(_ailAngle);
#elif defined(ARDUINO_ARCH_RP2040)
    if (_ail >= 0) {
      // Mapear 0-180° a 1000-2000 µs
      int pulseWidth = map(_ailAngle, 0, 180, 1000, 2000);
      analogWrite(_ail, pulseWidth);
    }
#endif
  }

  void setElevator(int angle) {
    _elevAngle = constrain(angle, 0, 180);
#ifdef ARDUINO_ARCH_ESP32
    if (_servoElev.attached()) _servoElev.write(_elevAngle);
#elif defined(ARDUINO_ARCH_RP2040)
    if (_elev >= 0) {
      int pulseWidth = map(_elevAngle, 0, 180, 1000, 2000);
      analogWrite(_elev, pulseWidth);
    }
#endif
  }

  int aileron() const { return _ailAngle; }
  int elevator() const { return _elevAngle; }
};
