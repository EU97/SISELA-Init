#include <Arduino.h>
#include "practices/practice.h"
#include "board_config.h"
#include "common/utils.h"
#include "pins/pins.h"

#if PRACTICE==2
// P2: Potenciómetro ADC
// Lee valor analógico y muestra: RAW, Voltaje, Porcentaje

static int adcPin = -1;
static uint32_t lastRead = 0;

namespace practices {
  void setup() {
    Serial.println("[P2] Potenciómetro ADC");
    
    adcPin = pins().adc_altitude;
    if (adcPin < 0) {
      Serial.println("ERROR: Pin ADC no definido para P2.");
      return;
    }
    
    Serial.print("Pin ADC: ");
    Serial.println(adcPin);
    
#ifdef ARDUINO_ARCH_ESP32
    pinMode(adcPin, INPUT);
    // ESP32: ADC configurado automáticamente, 12-bit por defecto
    Serial.println("Plataforma: ESP32 (12-bit ADC, 0-4095)");
#elif defined(ARDUINO_ARCH_RP2040)
    pinMode(adcPin, INPUT);
    Serial.println("Plataforma: RP2040 (10-bit ADC, 0-1023)");
#endif
    
    Serial.println("Formato: ADC_RAW | Voltaje | Porcentaje");
    Serial.println("------------------------------------------");
  }

  void loop() {
    if (adcPin < 0) return; // Pin no configurado
    
    if (millis() - lastRead >= 200) { // 5 Hz
      lastRead = millis();
      
      int raw = analogRead(adcPin);
      float voltage, percentage;
      
#ifdef ARDUINO_ARCH_ESP32
      // ESP32: 12 bits (0-4095) @ 3.3V
      voltage = (raw / 4095.0) * 3.3;
      percentage = (raw / 4095.0) * 100.0;
#elif defined(ARDUINO_ARCH_RP2040)
      // RP2040: 10 bits (0-1023) @ 3.3V en Arduino
      voltage = (raw / 1023.0) * 3.3;
      percentage = (raw / 1023.0) * 100.0;
#endif
      
      Serial.print("ADC: ");
      Serial.print(raw);
      Serial.print(" | V: ");
      Serial.print(voltage, 3);
      Serial.print(" V | ");
      Serial.print(percentage, 1);
      Serial.println(" %");
    }
  }
}
#endif
