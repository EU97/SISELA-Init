#pragma once
#include <Arduino.h>
#include "pins/pins.h"

class FlightSensors {
public:
  void begin() {
    // No special init needed for basic analogRead
  }
  int readRaw(int pin) {
    if (pin < 0) return -1;
    return analogRead(pin);
  }
  float readNorm(int pin) {
    int v = readRaw(pin);
    if (v < 0) return -1.0f;
    #if defined(ARDUINO_ARCH_ESP32)
      return v / 4095.0f;
    #elif defined(ARDUINO_ARCH_RP2040)
      return v / 1023.0f; // Arduino core Pico default 10-bit
    #else
      return v / 1023.0f;
    #endif
  }
  float altitude() { return readNorm(PIN_ADC_ALTITUDE); }
  float speed()    { return readNorm(PIN_ADC_SPEED); }
  float attitude() { return readNorm(PIN_ADC_ATTITUDE); }
  float light()    { return readNorm(PIN_ADC_LIGHT); }
};
