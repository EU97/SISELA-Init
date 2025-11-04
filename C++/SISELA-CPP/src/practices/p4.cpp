#include <Arduino.h>
#include "practices/practice.h"
#include "board_config.h"
#include "common/utils.h"

#if PRACTICE==4
namespace practices {
  static uint32_t last = 0;
  static bool on = false;
  void setup() { Serial.println("[P4] Template inicial listo."); }
  void loop() {
    if (millis() - last > 250) {
      last = millis(); on = !on;
      if (on) board::led_on(); else board::led_off();
      Serial.println("[P4] Blink");
    }
  }
}
#endif
