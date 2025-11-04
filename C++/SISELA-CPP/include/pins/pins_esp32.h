#pragma once
#include "pins_types.h"

// Tabla de pines por práctica (1..8) para ESP32 DevKit v1
// Índice 0 sin uso para que PRACTICE coincida con el índice
static const Pins PINS_TABLE_ESP32[9] = {
  {}, // 0 - no usado
  // 1: P1 — Básica (LED y Serial)
  {
    /*adc_altitude*/-1, /*adc_speed*/-1, /*adc_attitude*/-1, /*adc_light*/-1,
    /*servo_aileron*/-1, /*servo_elevator*/-1,
    /*pwm_motor*/-1,
    /*endstop*/-1,
    /*a4988*/{19,21,5},
    /*uln2003*/{26,25,33,32}
  },
  // 2: P2 — Reservado (rellenar al portar)
  { -1, -1, -1, -1,  -1, -1,  -1,  -1,  {19,21,5}, {26,25,33,32} },
  // 3: P3 — Reservado
  { -1, -1, -1, -1,  -1, -1,  -1,  -1,  {19,21,5}, {26,25,33,32} },
  // 4: P4 — Reservado
  { -1, -1, -1, -1,  -1, -1,  -1,  -1,  {19,21,5}, {26,25,33,32} },
  // 5: P5 — Reservado
  { -1, -1, -1, -1,  -1, -1,  -1,  -1,  {19,21,5}, {26,25,33,32} },
  // 6: P6 — Reservado
  { -1, -1, -1, -1,  -1, -1,  -1,  -1,  {19,21,5}, {26,25,33,32} },
  // 7: P7 — Reservado
  { -1, -1, -1, -1,  -1, -1,  -1,  -1,  {19,21,5}, {26,25,33,32} },
  // 8: P8 — Integrada (según documentación MicroPython)
  {
    /*adc_altitude*/34,
    /*adc_speed*/35,
    /*adc_attitude*/32,
    /*adc_light*/33,
    /*servo_aileron*/25,
    /*servo_elevator*/26,
    /*pwm_motor*/18,
    /*endstop*/4,
    /*a4988*/{19,21,5},
    /*uln2003*/{26,25,33,32}
  }
};
