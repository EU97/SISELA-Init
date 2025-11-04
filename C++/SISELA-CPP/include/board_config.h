#pragma once

// Selección de configuración por plataforma
#ifdef ARDUINO_ARCH_ESP32
  #include "config/esp32.h"
#elif defined(ARDUINO_ARCH_RP2040)
  #include "config/rp2040.h"
#else
  #warning "Plataforma no detectada; usando configuración ESP32 por defecto"
  #include "config/esp32.h"
#endif
