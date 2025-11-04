#pragma once
#include <Arduino.h>

struct StepperA4988Pins {
  int step = -1;
  int dir  = -1;
  int en   = -1; // LOW = enabled
};

struct StepperULN2003Pins {
  int in1 = -1;
  int in2 = -1;
  int in3 = -1;
  int in4 = -1;
};

struct Pins {
  // ADC sensors (generic names reused en prácticas avanzadas)
  int adc_altitude = -1;
  int adc_speed    = -1;
  int adc_attitude = -1;
  int adc_light    = -1; // en RP2040 puede omitirse si se usa sensor interno

  // Servos (superficies de control)
  int servo_aileron  = -1;
  int servo_elevator = -1;

  // PWM motor / throttle
  int pwm_motor = -1;

  // Endstop
  int endstop = -1;

  // Stepper drivers (solo uno aplica según macro de driver)
  StepperA4988Pins a4988;
  StepperULN2003Pins uln2003;
};
