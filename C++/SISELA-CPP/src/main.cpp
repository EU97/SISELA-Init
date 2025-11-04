#include <Arduino.h>
#include "board_config.h"
#include "practices/practice.h"
#include "common/utils.h"

#ifndef PRACTICE
#define PRACTICE 1
#endif

void setup() {
  Serial.begin(115200);
  #if defined(ARDUINO_ARCH_RP2040)
  while (!Serial && millis() < 2000) {}
  #endif
  Serial.println();
  Serial.print("SISELA Unified — Practice ");
  Serial.println(STRINGIFY(PRACTICE));
  Serial.print("Platform: ");
  #if defined(ARDUINO_ARCH_ESP32)
    Serial.println("ESP32");
  #elif defined(ARDUINO_ARCH_RP2040)
    Serial.println("RP2040");
  #else
    Serial.println("Unknown");
  #endif

  board::init();
  practices::setup();
}

void loop() {
  practices::loop();
}
