#pragma once
#include <Arduino.h>

#ifdef ARDUINO_ARCH_ESP32
#include <ESP32Servo.h>
#endif

// ============================================================================
// esc.h — Control de ESC (Electronic Speed Controller) para motores
// brushless (p. ej. 2212) mediante señal PWM tipo servo: 50 Hz, 1000-2000 us.
//
// Máquina de estados fail-safe: throttle() se niega (-1) si no se armó antes
// con arm(). Ver MicroPython/*/P8/lib/esc.py y docs/dron_2212.md para la
// documentación completa de seguridad (retirar hélices, alimentación LiPo
// dedicada, secuencia de armado, parada de emergencia).
// ============================================================================

class ESC {
#ifdef ARDUINO_ARCH_ESP32
  Servo _servo;
#endif
  int _pin = -1;
  int _minUs = 1000, _maxUs = 2000;
  bool _armed = false;
  float _throttle = 0.0f;

  void pulseUs(int us) {
    if (us < _minUs) us = _minUs;
    if (us > _maxUs) us = _maxUs;
#ifdef ARDUINO_ARCH_ESP32
    _servo.writeMicroseconds(us);
#elif defined(ARDUINO_ARCH_RP2040)
    analogWrite(_pin, us);
#endif
  }

 public:
  void begin(int pin, int minUs = 1000, int maxUs = 2000) {
    _pin = pin; _minUs = minUs; _maxUs = maxUs;
    if (_pin < 0) return;
#ifdef ARDUINO_ARCH_ESP32
    _servo.attach(_pin, minUs, maxUs);
#elif defined(ARDUINO_ARCH_RP2040)
    pinMode(_pin, OUTPUT);
    analogWriteFreq(50);
    analogWriteRange(20000);  // permite escribir directamente en microsegundos
#endif
    pulseUs(minUs);  // señal segura desde el arranque
  }

  // Secuencia de armado: throttle mínimo sostenido holdMs. Ejecutar SIN
  // hélices. BLOQUEA durante holdMs (uso educativo en banco de pruebas).
  void arm(uint32_t holdMs = 2000) {
    if (_pin < 0) return;
    pulseUs(_minUs);
    delay(holdMs);
    _armed = true;
    _throttle = 0.0f;
  }

  bool armed() const { return _armed; }

  // Retorna el throttle aplicado, o -1 si el ESC no está armado.
  float throttle(float percent) {
    if (!_armed) return -1.0f;
    if (percent < 0) percent = 0; if (percent > 100) percent = 100;
    int us = _minUs + (int)((percent / 100.0f) * (_maxUs - _minUs));
    pulseUs(us);
    _throttle = percent;
    return percent;
  }

  float getThrottle() const { return _throttle; }
  float pulseUsNow() const { return _minUs + (_throttle / 100.0f) * (_maxUs - _minUs); }

  void stop() { pulseUs(_minUs); _throttle = 0.0f; }
  void disarm() { stop(); _armed = false; }
};

// Conjunto de 4 ESC (M1..M4) para un cuadricóptero en configuración X.
class QuadESC {
  ESC _esc[4];
 public:
  void begin(const int pins[4], int minUs = 1000, int maxUs = 2000) {
    for (int i = 0; i < 4; i++) _esc[i].begin(pins[i], minUs, maxUs);
  }
  ESC& motor(int i) { return _esc[i]; }
  void armAll(uint32_t holdMs = 2000) { for (int i = 0; i < 4; i++) _esc[i].arm(holdMs); }
  void setAll(const float t[4]) { for (int i = 0; i < 4; i++) _esc[i].throttle(t[i]); }
  void emergencyStop() { for (int i = 0; i < 4; i++) _esc[i].stop(); }
  void disarmAll() { for (int i = 0; i < 4; i++) _esc[i].disarm(); }
  bool anyArmed() { for (int i = 0; i < 4; i++) if (_esc[i].armed()) return true; return false; }
};
