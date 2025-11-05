#include <Arduino.h>
#include "practices/practice.h"
#include "board_config.h"
#include "common/utils.h"
#include "pins/pins.h"

#if PRACTICE==4
// P4: Sensor de Presión MPX5500DP (20-520 kPa)
// Transfer function: Vout = VS × (0.2 × P + 0.2)
// Inversa: P(kPa) = (Vout - Vmin) / sensitivity + Pmin

// Parámetros del sensor MPX5500DP
static const float V_SUPPLY = 3.3;       // Voltaje del sensor (V)
static const float P_MIN = 20.0;         // Presión mínima (kPa)
static const float P_MAX = 520.0;        // Presión máxima (kPa)
static const float VOUT_MIN_IDEAL = V_SUPPLY * 0.2;  // 0.66V @ 3.3V
static const float VOUT_MAX_IDEAL = V_SUPPLY * 1.0;  // 3.3V @ 3.3V
static const float SENSITIVITY = (VOUT_MAX_IDEAL - VOUT_MIN_IDEAL) / (P_MAX - P_MIN);  // V/kPa

// Pin ADC
static int adcPin = -1;
static uint32_t lastRead = 0;
static const uint16_t SAMPLES = 50;      // Promedio de muestras
static uint8_t mode = 3;                  // 1=ADC raw, 2=Voltaje, 3=Presión

namespace practices {
  
  // Leer ADC con promedio
  float adc_read_avg() {
    uint32_t sum = 0;
    for (uint16_t i = 0; i < SAMPLES; i++) {
      sum += analogRead(adcPin);
      delay(1);
    }
    return sum / (float)SAMPLES;
  }
  
  // Convertir ADC → Voltaje
  float adc_to_voltage(float adc_val) {
#ifdef ARDUINO_ARCH_ESP32
    // ESP32: 12-bit (0-4095) @ 3.3V
    return (adc_val / 4095.0) * V_SUPPLY;
#elif defined(ARDUINO_ARCH_RP2040)
    // RP2040: 10-bit (0-1023) @ 3.3V en Arduino
    return (adc_val / 1023.0) * V_SUPPLY;
#endif
  }
  
  // Voltaje → Presión kPa (MPX5500DP)
  // P(kPa) = (Vout - Vmin) / sensitivity + Pmin
  float voltage_to_pressure_kpa(float voltage) {
    if (voltage < VOUT_MIN_IDEAL) return P_MIN;
    if (voltage > VOUT_MAX_IDEAL) return P_MAX;
    return ((voltage - VOUT_MIN_IDEAL) / SENSITIVITY) + P_MIN;
  }
  
  void setup() {
    Serial.println("\n[P4] Sensor de Presión MPX5500DP");
    
    adcPin = pins().adc_altitude;
    if (adcPin < 0) {
      Serial.println("ERROR: Pin ADC no definido para P4.");
      return;
    }
    
    pinMode(adcPin, INPUT);
    
#ifdef ARDUINO_ARCH_ESP32
    Serial.println("Plataforma: ESP32 (12-bit ADC, 0-4095)");
    Serial.printf("Pin: GPIO%d\n", adcPin);
#elif defined(ARDUINO_ARCH_RP2040)
    Serial.println("Plataforma: RP2040 (10-bit ADC, 0-1023)");
    Serial.printf("Pin: GP%d\n", adcPin);
#endif
    
    Serial.println("\n=== Configuración MPX5500DP ===");
    Serial.printf("V_SUPPLY: %.1f V\n", V_SUPPLY);
    Serial.printf("Rango: %.0f - %.0f kPa\n", P_MIN, P_MAX);
    Serial.printf("Vout_min: %.2f V @ %.0f kPa\n", VOUT_MIN_IDEAL, P_MIN);
    Serial.printf("Vout_max: %.2f V @ %.0f kPa\n", VOUT_MAX_IDEAL, P_MAX);
    Serial.printf("Sensibilidad: %.6f V/kPa\n", SENSITIVITY);
    
    Serial.println("\nATENCIÓN: MPX5500DP requiere VS=4.75-5.25V para especificación.");
    Serial.println("Con VS=3.3V funciona pero con menor precisión.");
    Serial.println("Para máxima precisión usar 5V + divisor de voltaje para ADC.");
    
    Serial.println("\n=== Modos ===");
    Serial.println("1) ADC crudo + Voltaje");
    Serial.println("2) Voltaje del sensor");
    Serial.println("3) Presión (kPa)");
    Serial.println("\nEscribe 1, 2 o 3 y ENTER. Default: 3 en 5s");
    
    // Esperar input 5 segundos
    uint32_t start = millis();
    while (millis() - start < 5000) {
      if (Serial.available()) {
        char c = Serial.read();
        if (c >= '1' && c <= '3') {
          mode = c - '0';
          while (Serial.available()) Serial.read();
          break;
        }
      }
    }
    
    Serial.print("\n[P4] Modo seleccionado: ");
    Serial.println(mode);
    
    switch (mode) {
      case 1: Serial.println("Modo 1: ADC crudo + Voltaje"); break;
      case 2: Serial.println("Modo 2: Voltaje del sensor (V)"); break;
      case 3: Serial.println("Modo 3: Presión (kPa)"); break;
    }
    Serial.println("Escribe 'm' y ENTER para volver al menú.\n");
    Serial.println("Formato de salida:");
    switch (mode) {
      case 1: Serial.println("ADC_RAW | Voltaje"); break;
      case 2: Serial.println("Voltaje"); break;
      case 3: Serial.println("ADC_RAW | Voltaje | Presión"); break;
    }
    Serial.println("------------------------------------------");
  }

  void loop() {
    if (adcPin < 0) return;
    
    // Check menú
    if (Serial.available()) {
      char c = Serial.read();
      while (Serial.available()) Serial.read();
      if (c == 'm' || c == 'M') {
        Serial.println("\n[P4] Volviendo al menú...");
        setup();
        return;
      }
    }
    
    // Lectura periódica (10 Hz = 100 ms)
    if (millis() - lastRead >= 100) {
      lastRead = millis();
      
      float adc_val = adc_read_avg();
      float voltage = adc_to_voltage(adc_val);
      
      switch (mode) {
        case 1:
          Serial.print("ADC: ");
          Serial.print((int)adc_val);
          Serial.print(" | V: ");
          Serial.print(voltage, 3);
          Serial.println(" V");
          break;
          
        case 2:
          Serial.print("V: ");
          Serial.print(voltage, 3);
          Serial.println(" V");
          break;
          
        case 3: {
          float pressure = voltage_to_pressure_kpa(voltage);
          Serial.print("ADC: ");
          Serial.print((int)adc_val);
          Serial.print(" | V: ");
          Serial.print(voltage, 3);
          Serial.print(" V | P: ");
          Serial.print(pressure, 2);
          Serial.println(" kPa");
          break;
        }
      }
    }
  }
}
#endif
