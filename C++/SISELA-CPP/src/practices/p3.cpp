#include <Arduino.h>
#include "practices/practice.h"
#include "board_config.h"
#include "common/utils.h"
#include "pins/pins.h"
#include <math.h>

#if PRACTICE==3
// P3: Sensor de Temperatura NTC (Termistor)
// Cálculo de temperatura mediante ecuación Beta

// Parámetros del NTC
static const float V_SUPPLY = 3.3;
static const float R_SERIES = 10000.0;  // 10kΩ en serie
static const float NTC_R0 = 10000.0;     // NTC @ 25°C
static const float NTC_BETA = 3950.0;    // Coeficiente Beta típico
static const float T0_KELVIN = 273.15 + 25.0;

// Pin ADC
static int adcPin = -1;
static uint32_t lastRead = 0;
static const uint16_t SAMPLES = 16;      // Promedio de muestras
static uint8_t mode = 3;                  // 1=ADC raw, 2=Resistencia, 3=Temperatura

namespace practices {
  
  // Leer ADC con promedio
  float adc_read_avg() {
    uint32_t sum = 0;
    for (uint16_t i = 0; i < SAMPLES; i++) {
      sum += analogRead(adcPin);
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
  
  // Voltaje → Resistencia NTC
  // Divisor: V_SUPPLY → R_SERIES → [nodo] → NTC → GND
  // V_nodo = V_SUPPLY * R_NTC / (R_SERIES + R_NTC)
  // Despejando: R_NTC = R_SERIES * V_nodo / (V_SUPPLY - V_nodo)
  float voltage_to_ntc_res(float v_node) {
    float denom = V_SUPPLY - v_node;
    if (denom < 1e-6) denom = 1e-6;  // evitar división por cero
    return R_SERIES * (v_node / denom);
  }
  
  // Resistencia NTC → Temperatura °C (Ecuación Beta)
  // 1/T = 1/T0 + (1/Beta) * ln(R/R0)
  float ntc_res_to_temp_c(float r_ntc) {
    if (r_ntc < 1.0) r_ntc = 1.0;  // evitar log(0)
    float invT = (1.0 / T0_KELVIN) + (1.0 / NTC_BETA) * log(r_ntc / NTC_R0);
    float T_kelvin = 1.0 / invT;
    return T_kelvin - 273.15;
  }
  
  void setup() {
    Serial.println("\n[P3] Sensor NTC - Temperatura con Ecuación Beta");
    
    adcPin = pins().adc_altitude;
    if (adcPin < 0) {
      Serial.println("ERROR: Pin ADC no definido para P3.");
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
    
    Serial.println("\n=== Configuración NTC ===");
    Serial.printf("V_SUPPLY: %.1f V\n", V_SUPPLY);
    Serial.printf("R_SERIES: %.0f Ω\n", R_SERIES);
    Serial.printf("NTC_R0: %.0f Ω @ 25°C\n", NTC_R0);
    Serial.printf("BETA: %.0f\n", NTC_BETA);
    
    Serial.println("\n=== Modos ===");
    Serial.println("1) ADC crudo + Voltaje");
    Serial.println("2) Resistencia NTC");
    Serial.println("3) Temperatura °C");
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
    
    Serial.print("\n[P3] Modo seleccionado: ");
    Serial.println(mode);
    
    switch (mode) {
      case 1: Serial.println("Modo 1: ADC crudo + Voltaje nodo"); break;
      case 2: Serial.println("Modo 2: Resistencia NTC (Ω)"); break;
      case 3: Serial.println("Modo 3: Temperatura (°C)"); break;
    }
    Serial.println("Escribe 'm' y ENTER para volver al menú.\n");
    Serial.println("Formato de salida:");
    switch (mode) {
      case 1: Serial.println("ADC_RAW | Voltaje"); break;
      case 2: Serial.println("ADC_RAW | Voltaje | Resistencia"); break;
      case 3: Serial.println("ADC_RAW | Voltaje | Resistencia | Temperatura"); break;
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
        Serial.println("\n[P3] Volviendo al menú...");
        setup();
        return;
      }
    }
    
    // Lectura periódica (10 Hz = 100 ms)
    if (millis() - lastRead >= 100) {
      lastRead = millis();
      
      float adc_val = adc_read_avg();
      float voltage = adc_to_voltage(adc_val);
      
      Serial.print("ADC: ");
      Serial.print((int)adc_val);
      Serial.print(" | V: ");
      Serial.print(voltage, 3);
      Serial.print(" V");
      
      if (mode >= 2) {
        float r_ntc = voltage_to_ntc_res(voltage);
        Serial.print(" | R_NTC: ");
        Serial.print(r_ntc, 1);
        Serial.print(" Ω");
        
        if (mode >= 3) {
          float temp_c = ntc_res_to_temp_c(r_ntc);
          Serial.print(" | T: ");
          Serial.print(temp_c, 2);
          Serial.print(" °C");
        }
      }
      
      Serial.println();
    }
  }
}
#endif
