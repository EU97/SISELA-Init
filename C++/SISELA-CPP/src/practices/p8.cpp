#include <Arduino.h>
#include "practices/practice.h"
#include "board_config.h"
#include "common/utils.h"
#include "pins/pins.h"

#if PRACTICE==8
namespace practices {
  static uint32_t last = 0;
  static bool on = false;
  void setup() {
    Serial.println("[P8] Template inicial listo.");
    Serial.print("Servo aileron pin: "); Serial.println(PIN_SERVO_AILERON);
    Serial.print("PWM motor pin: "); Serial.println(PIN_PWM_MOTOR);
    #if defined(STEPPER_ULN2003)
      Serial.println("Stepper: ULN2003");
      Serial.print("IN1:"); Serial.println(PIN_STEPPER_IN1);
    #else
      Serial.println("Stepper: A4988");
      Serial.print("STEP:"); Serial.println(PIN_STEPPER_STEP);
    #endif
  }
  void loop() {
    if (millis() - last > 140) {
      last = millis(); on = !on;
      if (on) board::led_on(); else board::led_off();
      Serial.println("[P8] Blink");
    }
  }
}
#endif
