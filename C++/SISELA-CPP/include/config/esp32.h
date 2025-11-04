#pragma once
#include <Arduino.h>

namespace board {
  // LED integrado común en ESP32 DevKit V1
  static constexpr int LED_PIN = 2;
  inline void init() {
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);
  }
  inline void led_on()  { digitalWrite(LED_PIN, HIGH); }
  inline void led_off() { digitalWrite(LED_PIN, LOW); }
}
