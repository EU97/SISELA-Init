#include <Arduino.h>
#include "practices/practice.h"
#include "board_config.h"
#include "common/utils.h"
#include "common/propulsion.h"
#include "pins/pins.h"

#if PRACTICE==6
// P6: Conmutación de potencia (PWM + transistor)
// Control de carga mediante PWM (LED/motor/resistencia calefactora)
// Modos:
//   1. Rampa automática 0-100% duty
//   2. Control manual por serial (enviar 0-100)
//   3. Control por ADC si disponible

static PropulsionSystem propulsion;
static int mode = 1; // 1=rampa, 2=serial, 3=ADC
static int duty = 0;
static int step = 1;
static uint32_t lastUpdate = 0;

namespace practices {
  void setup() {
    Serial.println("[P6] Conmutación de potencia (PWM)");
    Serial.print("Pin PWM: ");
    Serial.println(PIN_PWM_MOTOR);
    
    propulsion.begin(PIN_PWM_MOTOR);
    propulsion.setThrottle(0);
    
    if (pins().adc_altitude >= 0) {
#ifdef ARDUINO_ARCH_ESP32
      pinMode(pins().adc_altitude, INPUT);
#elif defined(ARDUINO_ARCH_RP2040)
      pinMode(pins().adc_altitude, INPUT);
#endif
      Serial.print("ADC en pin ");
      Serial.println(pins().adc_altitude);
      Serial.println("Modos: 1=Rampa | 2=Serial | 3=ADC");
    } else {
      Serial.println("Modos: 1=Rampa | 2=Serial");
    }
    
    Serial.println("Envía '1', '2', '3' para cambiar modo");
    Serial.println("En modo 2: envía 0-100 para duty %");
    
#ifdef ARDUINO_ARCH_RP2040
    // RP2040: configurar frecuencia PWM para switching de potencia
    analogWriteFreq(1000); // 1 kHz típico para LEDs/motores
#endif
  }

  void loop() {
    // Cambio de modo y duty por serial
    if (Serial.available()) {
      String input = Serial.readStringUntil('\n');
      input.trim();
      
      if (input == "1") { mode = 1; Serial.println("Modo: Rampa"); }
      else if (input == "2") { mode = 2; Serial.println("Modo: Serial. Envía 0-100"); }
      else if (input == "3" && pins().adc_altitude >= 0) { mode = 3; Serial.println("Modo: ADC"); }
      else if (mode == 2) {
        int val = input.toInt();
        if (val >= 0 && val <= 100) {
          duty = val;
          propulsion.setThrottle(duty);
          Serial.print("Duty: "); Serial.print(duty); Serial.println("%");
        }
      }
    }
    
    if (millis() - lastUpdate >= 50) {
      lastUpdate = millis();
      
      if (mode == 1) {
        // Rampa automática
        duty += step;
        if (duty >= 100 || duty <= 0) step = -step;
        propulsion.setThrottle(duty);
        
        if (duty % 10 == 0) {
          Serial.print("Duty: "); Serial.print(duty); Serial.println("%");
        }
      } else if (mode == 3 && pins().adc_altitude >= 0) {
        // Control por ADC
#ifdef ARDUINO_ARCH_ESP32
        int raw = analogRead(pins().adc_altitude);
        duty = map(raw, 0, 4095, 0, 100);
#elif defined(ARDUINO_ARCH_RP2040)
        int raw = analogRead(pins().adc_altitude);
        duty = map(raw, 0, 1023, 0, 100);
#endif
        propulsion.setThrottle(duty);
        
        static uint32_t lastLog = 0;
        if (millis() - lastLog >= 500) {
          lastLog = millis();
          Serial.print("ADC: "); Serial.print(raw);
          Serial.print(" -> Duty: "); Serial.print(duty); Serial.println("%");
        }
      }
    }
  }
}
#endif
