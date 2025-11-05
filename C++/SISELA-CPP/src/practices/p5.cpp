#include <Arduino.h>
#include "practices/practice.h"
#include "board_config.h"
#include "common/utils.h"
#include "common/flight_controls.h"
#include "pins/pins.h"

#if PRACTICE==5
// P5: Servomotor PWM (50 Hz)
// Modos:
//   1. Barrido automático 0-180-0°
//   2. Control manual por ADC (potenciómetro en adc_altitude si disponible)

static FlightControls controls;
static int mode = 1; // 1=sweep, 2=manual ADC
static int angle = 0;
static int step = 1;
static uint32_t lastUpdate = 0;

namespace practices {
  void setup() {
    Serial.println("[P5] Servomotor PWM");
    Serial.print("Pin servo: ");
    Serial.println(PIN_SERVO_AILERON);
    
    controls.begin(PIN_SERVO_AILERON, -1); // Solo aileron
    
    if (pins().adc_altitude >= 0) {
#ifdef ARDUINO_ARCH_ESP32
      // ESP32: configurar ADC si es input-only pin
      pinMode(pins().adc_altitude, INPUT);
#elif defined(ARDUINO_ARCH_RP2040)
      pinMode(pins().adc_altitude, INPUT);
#endif
      Serial.print("ADC disponible en pin ");
      Serial.println(pins().adc_altitude);
      Serial.println("Modo 1: Barrido | Modo 2: ADC control");
      Serial.println("Envía '1' o '2' por serial para cambiar modo.");
    } else {
      Serial.println("Modo único: Barrido 0-180°");
    }
    
    angle = 90;
    controls.setAileron(angle);
  }

  void loop() {
    // Cambio de modo por serial
    if (Serial.available()) {
      char c = Serial.read();
      if (c == '1') { mode = 1; Serial.println("Modo: Barrido"); }
      if (c == '2' && pins().adc_altitude >= 0) { mode = 2; Serial.println("Modo: ADC"); }
    }
    
    if (millis() - lastUpdate >= 20) { // 50 Hz refresh
      lastUpdate = millis();
      
      if (mode == 1) {
        // Barrido automático
        angle += step;
        if (angle >= 180 || angle <= 0) step = -step;
        controls.setAileron(angle);
        
        if (angle % 30 == 0) { // Log cada 30°
          Serial.print("Ángulo: "); Serial.println(angle);
        }
      } else if (mode == 2 && pins().adc_altitude >= 0) {
        // Control por ADC
#ifdef ARDUINO_ARCH_ESP32
        int raw = analogRead(pins().adc_altitude);
        angle = map(raw, 0, 4095, 0, 180);
#elif defined(ARDUINO_ARCH_RP2040)
        int raw = analogRead(pins().adc_altitude);
        angle = map(raw, 0, 1023, 0, 180); // RP2040 Arduino: 10-bit por defecto
#endif
        controls.setAileron(angle);
        
        static uint32_t lastLog = 0;
        if (millis() - lastLog >= 500) {
          lastLog = millis();
          Serial.print("ADC: "); Serial.print(raw);
          Serial.print(" -> Ángulo: "); Serial.println(angle);
        }
      }
    }
  }
}
#endif
