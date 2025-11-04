#pragma once
#include "pins_types.h"
#include "../board_config.h"

#if PRACTICE < 1 || PRACTICE > 8
  #error "PRACTICE debe estar entre 1 y 8"
#endif

#ifdef ARDUINO_ARCH_ESP32
  #include "pins_esp32.h"
  inline const Pins& pins() { return PINS_TABLE_ESP32[PRACTICE]; }
#elif defined(ARDUINO_ARCH_RP2040)
  #include "pins_rp2040.h"
  inline const Pins& pins() { return PINS_TABLE_RP2040[PRACTICE]; }
#else
  #include "pins_esp32.h"
  inline const Pins& pins() { return PINS_TABLE_ESP32[PRACTICE]; }
#endif

// Macros de conveniencia
#define PIN_ADC_ALTITUDE  (pins().adc_altitude)
#define PIN_ADC_SPEED     (pins().adc_speed)
#define PIN_ADC_ATTITUDE  (pins().adc_attitude)
#define PIN_ADC_LIGHT     (pins().adc_light)
#define PIN_SERVO_AILERON (pins().servo_aileron)
#define PIN_SERVO_ELEVATOR (pins().servo_elevator)
#define PIN_PWM_MOTOR     (pins().pwm_motor)
#define PIN_ENDSTOP       (pins().endstop)

// Selección de driver de stepper
#if defined(STEPPER_ULN2003)
  #define PIN_STEPPER_IN1 (pins().uln2003.in1)
  #define PIN_STEPPER_IN2 (pins().uln2003.in2)
  #define PIN_STEPPER_IN3 (pins().uln2003.in3)
  #define PIN_STEPPER_IN4 (pins().uln2003.in4)
#else
  // Por defecto A4988
  #define PIN_STEPPER_STEP (pins().a4988.step)
  #define PIN_STEPPER_DIR  (pins().a4988.dir)
  #define PIN_STEPPER_EN   (pins().a4988.en)
#endif
