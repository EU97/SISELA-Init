#pragma once
#include <Arduino.h>

namespace board {
  // LED integrado en Raspberry Pi Pico (GP25)
  static constexpr int LED_PIN = LED_BUILTIN; // definido por core
  inline void init() {
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);
  }
  inline void led_on()  { digitalWrite(LED_PIN, HIGH); }
  inline void led_off() { digitalWrite(LED_PIN, LOW); }
}
