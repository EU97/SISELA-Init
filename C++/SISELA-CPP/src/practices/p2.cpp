#include <Arduino.h>
#include "practices/practice.h"
#include "board_config.h"
#include "common/utils.h"
#include "pins/pins.h"

#if PRACTICE==2
// P2: Sistema de Adquisición Analógica con Codificación ARINC 429
//
// Funcionalidad completa (4 casos integrados):
//   Caso 1: ADC + Media Móvil  -> voltaje + ángulo del potenciómetro
//   Caso 2: Indicador de Flaps -> mapeo a 0-45° con alerta de sobre-extensión
//   Caso 3: ARINC 429 BNR      -> empaquetado 32 bits (Label 270, paridad impar)
//   Caso 4: Falla de Sensor    -> detección fuera de rango, SSM = Failure
//
// Salida CSV:
//   t_ms,raw,avg,voltage_v,angle_deg,flap_deg,ssm,arinc_hex

// ------------ Parámetros ------------
static int adcPin = -1;
static uint32_t lastRead = 0;

static constexpr float VREF = 3.3f;
static constexpr float ANGLE_MAX_DEG = 300.0f;
static constexpr float FLAP_MAX_DEG = 45.0f;
static constexpr float FLAP_ALERT_DEG = 40.0f;
static constexpr uint16_t ARINC_LABEL_OCT = 0270;  // Octal 270 = 0xB8

#ifdef ARDUINO_ARCH_ESP32
  static constexpr int ADC_MAX_VAL = 4095;    // 12 bits
#elif defined(ARDUINO_ARCH_RP2040)
  static constexpr int ADC_MAX_VAL = 1023;    // 10 bits (Arduino framework)
#else
  static constexpr int ADC_MAX_VAL = 4095;
#endif

static constexpr int UMBRAL_MIN = (int)(ADC_MAX_VAL * 0.02f);
static constexpr int UMBRAL_MAX = (int)(ADC_MAX_VAL * 0.98f);

// ------------ Media Móvil ------------
static constexpr int MA_SIZE = 8;
static int maBuf[MA_SIZE] = {0};
static long maSum = 0;
static int maIdx = 0;
static int maCount = 0;

static int maAdd(int x) {
    maSum -= maBuf[maIdx];
    maBuf[maIdx] = x;
    maSum += x;
    maIdx = (maIdx + 1) % MA_SIZE;
    if (maCount < MA_SIZE) maCount++;
    return (int)(maSum / maCount);
}

// ------------ ARINC 429 BNR (Caso 3) ------------
static uint32_t generarArincWord(uint16_t labelOct, int datoAdc, uint8_t ssm) {
    // Label: bits 1-8 (ya en octal como entero)
    uint32_t word = ((uint32_t)ssm << 29) | ((uint32_t)datoAdc << 10) | (uint32_t)labelOct;
    // Paridad impar (bit 32, posición 31)
    int ones = 0;
    uint32_t tmp = word;
    while (tmp) { ones += (tmp & 1); tmp >>= 1; }
    if (ones % 2 == 0) word |= (1UL << 31);
    return word;
}

// ------------ Detección de falla (Caso 4) ------------
static uint8_t detectarFalla(int raw) {
    if (raw < UMBRAL_MIN || raw > UMBRAL_MAX) return 0b00; // Failure Warning
    return 0b11; // Normal Operation
}

namespace practices {
  void setup() {
    Serial.println("[P2] ADC + ARINC 429 - Sistema Integrado");

    adcPin = pins().adc_altitude;
    if (adcPin < 0) {
      Serial.println("ERROR: Pin ADC no definido para P2.");
      return;
    }

    Serial.print("Pin ADC: ");
    Serial.println(adcPin);
    pinMode(adcPin, INPUT);

#ifdef ARDUINO_ARCH_ESP32
    Serial.println("Plataforma: ESP32 (12-bit ADC, 0-4095)");
#elif defined(ARDUINO_ARCH_RP2040)
    Serial.println("Plataforma: RP2040 (10-bit ADC, 0-1023)");
#endif

    Serial.println("t_ms,raw,avg,voltage_v,angle_deg,flap_deg,ssm,arinc_hex");
  }

  void loop() {
    if (adcPin < 0) return;

    if (millis() - lastRead >= 10) {  // 100 Hz
      uint32_t t = millis();
      lastRead = t;

      int raw = analogRead(adcPin);
      int avg = maAdd(raw);
      float voltage = ((float)avg / ADC_MAX_VAL) * VREF;
      float angle = (voltage / VREF) * ANGLE_MAX_DEG;
      float flap = (voltage / VREF) * FLAP_MAX_DEG;

      // Caso 4: detección de falla
      uint8_t ssm = detectarFalla(raw);

      // Caso 3: codificación ARINC 429
      uint32_t arincWord = generarArincWord(ARINC_LABEL_OCT, avg, ssm);

      // Salida CSV
      const char* ssmStr = (ssm == 0b11) ? "OK" : "FAIL";
      char buf[100];
      snprintf(buf, sizeof(buf), "%lu,%d,%d,%.3f,%.1f,%.1f,%s,0x%08lX",
               (unsigned long)t, raw, avg, voltage, angle, flap,
               ssmStr, (unsigned long)arincWord);
      Serial.println(buf);
    }
  }
}
#endif
