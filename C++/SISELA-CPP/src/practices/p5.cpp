#include <Arduino.h>
#include "practices/practice.h"
#include "board_config.h"
#include "common/utils.h"

#if PRACTICE==5
namespace practices {
  static uint32_t last = 0;
  static bool on = false;
  void setup() { Serial.println("[P5] Template inicial listo."); }
  void loop() {
    if (millis() - last > 200) {
      last = millis(); on = !on;
      if (on) board::led_on(); else board::led_off();
      Serial.println("[P5] Blink");
    }
  }
}
#endif
