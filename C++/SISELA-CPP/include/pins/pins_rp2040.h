#pragma once
#include "pins_types.h"

// Tabla de pines por práctica (1..8) para Raspberry Pi Pico (RP2040)
static const Pins PINS_TABLE_RP2040[9] = {
  {}, // 0
  // 1: P1 — Básica (LED y Serial)
  { -1, -1, -1, -1,  -1, -1,  -1,  -1,  {18,19,5}, {26,27,28,22} },
  // 2: P2 — Reservado
  { -1, -1, -1, -1,  -1, -1,  -1,  -1,  {18,19,5}, {26,27,28,22} },
  // 3: P3 — Reservado
  { -1, -1, -1, -1,  -1, -1,  -1,  -1,  {18,19,5}, {26,27,28,22} },
  // 4: P4 — Reservado
  { -1, -1, -1, -1,  -1, -1,  -1,  -1,  {18,19,5}, {26,27,28,22} },
  // 5: P5 — Reservado
  { -1, -1, -1, -1,  -1, -1,  -1,  -1,  {18,19,5}, {26,27,28,22} },
  // 6: P6 — Reservado
  { -1, -1, -1, -1,  -1, -1,  -1,  -1,  {18,19,5}, {26,27,28,22} },
  // 7: P7 — Reservado
  { -1, -1, -1, -1,  -1, -1,  -1,  -1,  {18,19,5}, {26,27,28,22} },
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
