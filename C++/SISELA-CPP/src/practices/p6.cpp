#include <Arduino.h>
#include "practices/practice.h"
#include "board_config.h"
#include "common/utils.h"
#include "common/propulsion.h"
#include "common/siglab.h"
#include "pins/pins.h"

#if PRACTICE==6
// P6: Conmutación de potencia (PWM + transistor)
// Control de carga mediante PWM (LED/motor/resistencia calefactora)
// Modos:
//   1. Rampa automática 0-100% duty
//   2. Control manual por serial (enviar 0-100)
//   3. Control por ADC si disponible
//   4. Registro CSV (barrido con muestreo), para tools/sisela_signal

static PropulsionSystem propulsion;
static int mode = 1; // 1=rampa, 2=serial, 3=ADC, 4=registro CSV
static int duty = 0;
static int step = 1;
static uint32_t lastUpdate = 0;

static void mode_csv_log() {
  const int n = 200;       // 50 Hz * 4 s
  const float fsHz = 50.0f;
  const uint32_t periodUs = (uint32_t)(1e6f / fsHz);
  float d = 0.0f, dir = 1.0f;
  const float stepPct = 100.0f / (n / 2.0f);
  Serial.println("t_us,duty_pct,adc_raw");
  uint32_t t0 = micros();
  uint32_t next = t0;
  for (int i = 0; i < n; i++) {
    while ((int32_t)(micros() - next) < 0) { /* espera activa */ }
    propulsion.setThrottle((int)d);
    int raw = 0;
    if (pins().adc_altitude >= 0) {
      raw = analogRead(pins().adc_altitude);
    }
    serialPrintf(Serial, "%lu,%.1f,%d\n", (unsigned long)(micros() - t0), d, raw);
    d += dir * stepPct;
    if (d >= 100.0f) { d = 100.0f; dir = -1.0f; }
    else if (d <= 0.0f) { d = 0.0f; dir = 1.0f; }
    next += periodUs;
  }
  serialPrintf(Serial, "# end n=%d\n", n);
  propulsion.setThrottle(0);
  Serial.println("Cambiando a modo Rampa...\n");
}

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
      Serial.println("Modos: 1=Rampa | 2=Serial | 3=ADC | 4=Registro CSV");
    } else {
      Serial.println("Modos: 1=Rampa | 2=Serial | 4=Registro CSV");
    }

    Serial.println("Envía '1', '2', '3' o '4' para cambiar modo");
    Serial.println("En modo 2: envía 0-100 para duty %");
    Serial.println("Modo 4 (PC): python -m sisela_signal capture --port COMx --menu 4 --out cap.csv");
    
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
      else if (input == "4") { mode = 4; Serial.println("Modo: Registro CSV"); mode_csv_log(); mode = 1; }
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
