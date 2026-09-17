#pragma once

#include <stdarg.h>
#include <stdio.h>

// Selección de configuración por plataforma
#ifdef ARDUINO_ARCH_ESP32
  #include "config/esp32.h"
#elif defined(ARDUINO_ARCH_RP2040)
  #include "config/rp2040.h"
#else
  #warning "Plataforma no detectada; usando configuración ESP32 por defecto"
  #include "config/esp32.h"
#endif

// El core Arduino-mbed de RP2040 (`platform = raspberrypi`) no implementa
// Stream::printf / Serial.printf (a diferencia del core ESP32). Se emula con
// vsnprintf + print() para que el mismo código sirva en ambas plataformas.
inline void serialPrintf(Stream &io, const char *fmt, ...) {
  char buf[160];
  va_list args;
  va_start(args, fmt);
  vsnprintf(buf, sizeof(buf), fmt, args);
  va_end(args);
  io.print(buf);
}
