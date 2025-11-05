#include <Arduino.h>
#include "practices/practice.h"
#include "board_config.h"
#include "common/utils.h"
#include "pins/pins.h"
// Drivers base
#include "common/sensors.h"
#include "common/flight_controls.h"
#include "common/propulsion.h"
#include "common/landing_gear.h"

#if PRACTICE==8
namespace practices {
  static uint32_t last = 0;
  static bool on = false;
  static FlightSensors sensors;
  static FlightControls controls;
  static PropulsionSystem propulsion;
  static LandingGear gear;
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
    sensors.begin();
    controls.begin();
    propulsion.begin();
    gear.begin();
  }
  void loop() {
    if (millis() - last > 500) {
      last = millis(); on = !on;
      if (on) board::led_on(); else board::led_off();
      // Lecturas básicas de sensores
      float alt = sensors.altitude();
      float spd = sensors.speed();
      float att = sensors.attitude();
      float lux = sensors.light();
      Serial.print("[P8] alt="); Serial.print(alt,3);
      Serial.print(" spd="); Serial.print(spd,3);
      Serial.print(" att="); Serial.print(att,3);
      Serial.print(" lux="); Serial.print(lux,3);
      Serial.print(" endstop="); Serial.println(gear.endstopActive()?"ON":"off");

      // Control mínimo de demostración
      controls.setAileron((int)(alt * 180));
      controls.setElevator((int)(att * 180));
      propulsion.setThrottle(spd);
      gear.stepperStep(10, true, 600); // pasos cortos para demostrar
    }
  }
}
#endif
