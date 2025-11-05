#include <Arduino.h>
#include "practices/practice.h"
#include "board_config.h"
#include "common/utils.h"
#include "pins/pins.h"
#include <math.h>

#if PRACTICE==3
// P3: Sensor de Temperatura (NTC Termistor o LM35)
// Dos opciones de sensor seleccionables por menú, con modo CSV y regreso al menú del sensor actual.

// Tipo de sensor
static uint8_t sensorType = 1;  // 1=NTC, 2=LM35

// Parámetros del NTC
static const float V_SUPPLY = 3.3;
static const float R_SERIES = 10000.0;  // 10kΩ en serie
static const float NTC_R0 = 10000.0;     // NTC @ 25°C
static const float NTC_BETA = 3950.0;    // Coeficiente Beta típico
static const float T0_KELVIN = 273.15 + 25.0;

// Parámetros del LM35
// LM35: 10mV/°C, rango 0-100°C (o -55°C a +150°C según versión)
static const float LM35_MV_PER_C = 10.0;  // 10mV por grado Celsius

// Pin ADC y estado
static int adcPin = -1;
static uint32_t lastRead = 0;
static const uint16_t SAMPLES = 16;      // Promedio de muestras
static uint8_t mode = 3;                 // NTC: 1=ADC, 2=Resistencia, 3=Temperatura, 4=CSV | LM35: 1=ADC, 2=Temperatura, 3=CSV
static bool csvHeaderPrinted = false;
static uint32_t csvStartMs = 0;

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

  // LM35: Voltaje → Temperatura °C
  // Conversión directa: T(°C) = V(mV) / 10mV/°C = V(V) * 1000 / 10 = V * 100
  float lm35_voltage_to_temp_c(float voltage) {
    return voltage * 100.0;  // 10mV/°C = 0.01V/°C → V * 100 = °C
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

  static void print_platform_info() {
#ifdef ARDUINO_ARCH_ESP32
    Serial.println("Plataforma: ESP32 (12-bit ADC, 0-4095)");
    Serial.printf("Pin: GPIO%d\n", adcPin);
#elif defined(ARDUINO_ARCH_RP2040)
    Serial.println("Plataforma: RP2040 (10-bit ADC, 0-1023)");
    Serial.printf("Pin: GP%d\n", adcPin);
#endif
  }

  static void print_sensor_config() {
    if (sensorType == 1) {
      Serial.println("\n=== Configuración NTC ===");
      Serial.printf("V_SUPPLY: %.1f V\n", V_SUPPLY);
      Serial.printf("R_SERIES: %.0f Ω\n", R_SERIES);
      Serial.printf("NTC_R0: %.0f Ω @ 25°C\n", NTC_R0);
      Serial.printf("BETA: %.0f\n", NTC_BETA);
      Serial.println("Conexión: 3V3 → R_SERIES → [ADC] → NTC → GND");
    } else {
      Serial.println("\n=== Configuración LM35 ===");
      Serial.printf("V_SUPPLY: %.1f V\n", V_SUPPLY);
      Serial.printf("Sensibilidad: %.0f mV/°C\n", LM35_MV_PER_C);
      Serial.println("Rango típico: 0-100°C (LM35DZ)");
      Serial.println("Conexión: LM35 Vout → [ADC] (Vs=5V o 3.3V)");
      Serial.println("Nota: Máxima precisión con Vs=5V");
    }
  }

  static void print_format_info() {
    Serial.println("Formato de salida:");
    if (sensorType == 1) {
      switch (mode) {
        case 1: Serial.println("ADC_RAW | Voltaje"); break;
        case 2: Serial.println("ADC_RAW | Voltaje | Resistencia"); break;
        case 3: Serial.println("ADC_RAW | Voltaje | Resistencia | Temperatura"); break;
        case 4: Serial.println("CSV: t_ms,adc,v_node_v,r_ntc_ohm,t_c"); break;
      }
    } else {
      switch (mode) {
        case 1: Serial.println("ADC_RAW | Voltaje"); break;
        case 2: Serial.println("ADC_RAW | Voltaje | Temperatura"); break;
        case 3: Serial.println("CSV: t_ms,adc,v_node_v,t_c"); break;
      }
    }
    Serial.println("------------------------------------------");
  }

  static void show_mode_menu_and_select() {
    Serial.println("\n=== Modos ===");
    uint8_t maxMode = 0;
    uint8_t defaultMode = 3; // NTC default 3, LM35 default 2 (adjust below)
    if (sensorType == 1) {
      Serial.println("1) ADC crudo + Voltaje");
      Serial.println("2) Resistencia NTC");
      Serial.println("3) Temperatura °C");
      Serial.println("4) Monitor CSV (t,adc,V,R,T)");
      maxMode = 4;
      defaultMode = 3;
    } else {
      Serial.println("1) ADC crudo + Voltaje");
      Serial.println("2) Temperatura °C");
      Serial.println("3) Monitor CSV (t,adc,V,T)");
      maxMode = 3;
      defaultMode = 2;
    }
    Serial.printf("\nEscribe 1..%d y ENTER. Default: %d en 5s\n", maxMode, defaultMode);

    // Esperar input 5 segundos
    uint32_t start = millis();
    mode = defaultMode;
    while (millis() - start < 5000) {
      if (Serial.available()) {
        char c = Serial.read();
        if (c >= '1' && c <= ('0' + maxMode)) {
          mode = c - '0';
          while (Serial.available()) Serial.read();
          break;
        }
      }
    }

    Serial.print("\n[P3] Modo seleccionado: ");
    Serial.println(mode);
    if (sensorType == 1) {
      switch (mode) {
        case 1: Serial.println("Modo 1: ADC crudo + Voltaje nodo"); break;
        case 2: Serial.println("Modo 2: Resistencia NTC (Ω)"); break;
        case 3: Serial.println("Modo 3: Temperatura (°C)"); break;
        case 4: Serial.println("Modo 4: Monitor CSV"); csvHeaderPrinted = false; csvStartMs = millis(); break;
      }
    } else {
      switch (mode) {
        case 1: Serial.println("Modo 1: ADC crudo + Voltaje"); break;
        case 2: Serial.println("Modo 2: Temperatura (°C)"); break;
        case 3: Serial.println("Modo 3: Monitor CSV"); csvHeaderPrinted = false; csvStartMs = millis(); break;
      }
    }
    Serial.println("Escribe 'm' y ENTER para volver al menú de modos.\n");
    print_format_info();
  }

  void setup() {
    Serial.println("\n[P3] Sensor de Temperatura");
    Serial.println("==========================================");

    // Menú de selección de sensor
    Serial.println("\n=== Seleccionar Tipo de Sensor ===");
    Serial.println("1) NTC Termistor (10kΩ, Beta=3950)");
    Serial.println("2) LM35 (Sensor lineal 10mV/°C)");
    Serial.println("\nEscribe 1 o 2 y ENTER. Default: 1 en 5s");

    // Esperar selección de sensor 5 segundos
    uint32_t start = millis();
    while (millis() - start < 5000) {
      if (Serial.available()) {
        char c = Serial.read();
        if (c >= '1' && c <= '2') {
          sensorType = c - '0';
          while (Serial.available()) Serial.read();
          break;
        }
      }
    }

    Serial.print("\n[P3] Sensor seleccionado: ");
    if (sensorType == 1) {
      Serial.println("NTC Termistor");
    } else {
      Serial.println("LM35");
    }
    Serial.println("==========================================\n");

    adcPin = pins().adc_altitude;
    if (adcPin < 0) {
      Serial.println("ERROR: Pin ADC no definido para P3.");
      return;
    }

    pinMode(adcPin, INPUT);

    print_platform_info();
    print_sensor_config();

    // Selección inicial de modo (según sensor)
    show_mode_menu_and_select();
  }

  void loop() {
    if (adcPin < 0) return;

    // Check menú de modos actual
    if (Serial.available()) {
      char c = Serial.read();
      while (Serial.available()) Serial.read();
      if (c == 'm' || c == 'M') {
        Serial.println("\n[P3] Volviendo al menú del sensor actual...");
        show_mode_menu_and_select();
        return;
      }
    }

    // Lectura periódica (10 Hz = 100 ms)
    if (millis() - lastRead >= 100) {
      lastRead = millis();

      float adc_val = adc_read_avg();
      float voltage = adc_to_voltage(adc_val);

      // CSV modes
      if ((sensorType == 1 && mode == 4) || (sensorType == 2 && mode == 3)) {
        if (!csvHeaderPrinted) {
          if (sensorType == 1) {
            Serial.println("t_ms,adc,v_node_v,r_ntc_ohm,t_c");
          } else {
            Serial.println("t_ms,adc,v_node_v,t_c");
          }
          csvHeaderPrinted = true;
          csvStartMs = millis();
        }
        uint32_t t_ms = millis() - csvStartMs;
        if (sensorType == 1) {
          float r_ntc = voltage_to_ntc_res(voltage);
          float temp_c = ntc_res_to_temp_c(r_ntc);
          Serial.print(t_ms);
          Serial.print(",");
          Serial.print((int)adc_val);
          Serial.print(",");
          Serial.print(voltage, 4);
          Serial.print(",");
          Serial.print(r_ntc, 1);
          Serial.print(",");
          Serial.println(temp_c, 2);
        } else {
          float temp_c = lm35_voltage_to_temp_c(voltage);
          Serial.print(t_ms);
          Serial.print(",");
          Serial.print((int)adc_val);
          Serial.print(",");
          Serial.print(voltage, 4);
          Serial.print(",");
          Serial.println(temp_c, 2);
        }
        return; // ya imprimimos en modo CSV
      }

      // Modos normales (no CSV)
      Serial.print("ADC: ");
      Serial.print((int)adc_val);
      Serial.print(" | V: ");
      Serial.print(voltage, 3);
      Serial.print(" V");

      if (sensorType == 1) {
        // NTC: modo 2 muestra resistencia, modo 3 temperatura
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
      } else {
        // LM35: modo 2 muestra temperatura directamente
        if (mode >= 2) {
          float temp_c = lm35_voltage_to_temp_c(voltage);
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
