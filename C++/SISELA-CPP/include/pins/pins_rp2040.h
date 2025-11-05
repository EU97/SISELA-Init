#pragma once
#include "pins_types.h"

// Tabla de pines por práctica (1..8) para Raspberry Pi Pico (RP2040)
static const Pins PINS_TABLE_RP2040[9] = {
  {}, // 0
  // 1: P1 — Básica (LED y Serial)
  { -1, -1, -1, -1,  -1, -1,  -1,  -1,  {-1,-1,-1}, {-1,-1,-1,-1} },
  // 2: P2 — Potenciómetro ADC (GP26)
  { 26, -1, -1, -1,  -1, -1,  -1,  -1,  {-1,-1,-1}, {-1,-1,-1,-1} },
  // 3: P3 — NTC (ADC GP26)
  { 26, -1, -1, -1,  -1, -1,  -1,  -1,  {-1,-1,-1}, {-1,-1,-1,-1} },
  // 4: P4 — MPX5500DP (ADC GP26)
  { 26, -1, -1, -1,  -1, -1,  -1,  -1,  {-1,-1,-1}, {-1,-1,-1,-1} },
  // 5: P5 — Servo PWM (GP18) + ADC opcional (GP26)
  { 26, -1, -1, -1,  18, -1,  -1,  -1,  {-1,-1,-1}, {-1,-1,-1,-1} },
  // 6: P6 — Conmutación de potencia (PWM GP18) + ADC opcional (GP26)
  { 26, -1, -1, -1,  -1, -1,  18,  -1,  {-1,-1,-1}, {-1,-1,-1,-1} },
  // 7: P7 — Stepper (A4988 o ULN2003) + Endstop opcional (GP4)
  { -1, -1, -1, -1,  -1, -1,  -1,   4,  {18,19,5}, {26,27,28,22} },
  // 8: P8 — Integrada (según documentación MicroPython)
  {
    /*adc_altitude*/26,
    /*adc_speed*/27,
    /*adc_attitude*/28,
    /*adc_light*/-1, // se puede usar TEMP interna
    /*servo_aileron*/14,
    /*servo_elevator*/15,
    /*pwm_motor*/13,
    /*endstop*/4,
    /*a4988*/{18,19,5},
    /*uln2003*/{26,27,28,22}
  }
};
