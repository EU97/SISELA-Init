#pragma once

#define STR_IMPL(x) #x
#define STRINGIFY(x) STR_IMPL(x)

inline void delay_ms(unsigned long ms) {
  delay(ms);
}
