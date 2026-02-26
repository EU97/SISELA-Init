#include <Arduino.h>
#include <Wire.h>
#include "practices/practice.h"
#include "board_config.h"

#if PRACTICE==4
// ============================================================================
// P4: Altímetro Barométrico — Sensor BMP180 (I2C)
//
// BMP180: Presión barométrica + temperatura con compensación por
//         11 coeficientes de calibración (EEPROM).
// Interfaz: I2C @ 0x77
// Rango: 300–1100 hPa, −40 – +85 °C
// Altitud: h = 44330 × (1 − (P/P₀)^(1/5.255))
// ============================================================================

static const uint8_t BMP180_ADDR = 0x77;

// Registros
static const uint8_t REG_ID      = 0xD0;
static const uint8_t REG_CALIB   = 0xAA;
static const uint8_t REG_CTRL    = 0xF4;
static const uint8_t REG_DATA    = 0xF6;

// Comandos
static const uint8_t CMD_TEMP    = 0x2E;
static const uint8_t CMD_PRES    = 0x34;  // + (oss << 6)

// Configuración
static const uint8_t OSS = 1;             // Sobremuestreo estándar
static float SEA_LEVEL_PA = 101325.0f;    // QNH (Pa)
static uint32_t lastRead = 0;
static uint8_t mode = 3;                  // 1=Raw, 2=T+P, 3=Altitude

// Coeficientes de calibración
static int16_t  AC1, AC2, AC3, B1, B2, MB, MC, MD;
static uint16_t AC4, AC5, AC6;
static int32_t  B5_val;   // Cache de B5

// I2C pines (defaults del framework)
#ifdef ARDUINO_ARCH_ESP32
  // ESP32: SDA=21, SCL=22 (Wire default)
  static const int SDA_P = 21;
  static const int SCL_P = 22;
#elif defined(ARDUINO_ARCH_RP2040)
  // RP2040: SDA=4, SCL=5 (Wire default Arduino-Pico)
  static const int SDA_P = 4;
  static const int SCL_P = 5;
#endif

// ============================================================================
// Helpers I2C
// ============================================================================
static uint8_t bmp_read8(uint8_t reg) {
  Wire.beginTransmission(BMP180_ADDR);
  Wire.write(reg);
  Wire.endTransmission(false);
  Wire.requestFrom(BMP180_ADDR, (uint8_t)1);
  return Wire.read();
}

static int16_t bmp_read16s(uint8_t reg) {
  Wire.beginTransmission(BMP180_ADDR);
  Wire.write(reg);
  Wire.endTransmission(false);
  Wire.requestFrom(BMP180_ADDR, (uint8_t)2);
  int16_t val = (Wire.read() << 8) | Wire.read();
  return val;
}

static uint16_t bmp_read16u(uint8_t reg) {
  Wire.beginTransmission(BMP180_ADDR);
  Wire.write(reg);
  Wire.endTransmission(false);
  Wire.requestFrom(BMP180_ADDR, (uint8_t)2);
  uint16_t val = (Wire.read() << 8) | Wire.read();
  return val;
}

static void bmp_write8(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(BMP180_ADDR);
  Wire.write(reg);
  Wire.write(val);
  Wire.endTransmission();
}

// ============================================================================
// Calibración
// ============================================================================
static bool read_calibration() {
  AC1 = bmp_read16s(0xAA);
  AC2 = bmp_read16s(0xAC);
  AC3 = bmp_read16s(0xAE);
  AC4 = bmp_read16u(0xB0);
  AC5 = bmp_read16u(0xB2);
  AC6 = bmp_read16u(0xB4);
  B1  = bmp_read16s(0xB6);
  B2  = bmp_read16s(0xB8);
  MB  = bmp_read16s(0xBA);
  MC  = bmp_read16s(0xBC);
  MD  = bmp_read16s(0xBE);
  // Validar (AC1 == 0 probablemente falla de I2C)
  return (AC1 != 0 && AC1 != -1);
}

// ============================================================================
// Lecturas crudas
// ============================================================================
static int32_t read_raw_temp() {
  bmp_write8(REG_CTRL, CMD_TEMP);
  delay(5);
  return (int32_t)bmp_read16u(REG_DATA);
}

static int32_t read_raw_pressure() {
  bmp_write8(REG_CTRL, CMD_PRES | (OSS << 6));
  uint8_t delays[] = {5, 8, 14, 26};
  delay(delays[OSS]);
  Wire.beginTransmission(BMP180_ADDR);
  Wire.write(REG_DATA);
  Wire.endTransmission(false);
  Wire.requestFrom(BMP180_ADDR, (uint8_t)3);
  int32_t val = ((int32_t)Wire.read() << 16) |
                ((int32_t)Wire.read() << 8)  |
                 (int32_t)Wire.read();
  return val >> (8 - OSS);
}

// ============================================================================
// Compensación (datasheet Bosch)
// ============================================================================
static float compensate_temp(int32_t UT) {
  int32_t X1 = ((UT - (int32_t)AC6) * (int32_t)AC5) >> 15;
  int32_t X2 = ((int32_t)MC << 11) / (X1 + (int32_t)MD);
  B5_val = X1 + X2;
  return ((B5_val + 8) >> 4) / 10.0f;
}

static int32_t compensate_pressure(int32_t UP) {
  int32_t B6 = B5_val - 4000;
  int32_t X1 = ((int32_t)B2 * ((B6 * B6) >> 12)) >> 11;
  int32_t X2 = ((int32_t)AC2 * B6) >> 11;
  int32_t X3 = X1 + X2;
  int32_t B3 = ((((int32_t)AC1 * 4 + X3) << OSS) + 2) >> 2;
  X1 = ((int32_t)AC3 * B6) >> 13;
  X2 = ((int32_t)B1 * ((B6 * B6) >> 12)) >> 16;
  X3 = ((X1 + X2) + 2) >> 2;
  uint32_t B4 = ((uint32_t)AC4 * (uint32_t)(X3 + 32768)) >> 15;
  uint32_t B7 = ((uint32_t)UP - B3) * (50000UL >> OSS);
  int32_t p;
  if (B7 < 0x80000000UL)
    p = (B7 * 2) / B4;
  else
    p = (B7 / B4) * 2;
  X1 = (p >> 8) * (p >> 8);
  X1 = (X1 * 3038) >> 16;
  X2 = (-7357 * p) >> 16;
  p = p + ((X1 + X2 + 3791) >> 4);
  return p;
}

static float calc_altitude(int32_t p_pa) {
  return 44330.0f * (1.0f - powf((float)p_pa / SEA_LEVEL_PA, 1.0f / 5.255f));
}

// ============================================================================
// Lectura combinada
// ============================================================================
static void read_all(float &temp, int32_t &pres, float &alt) {
  int32_t UT = read_raw_temp();
  int32_t UP = read_raw_pressure();
  temp = compensate_temp(UT);
  pres = compensate_pressure(UP);
  alt  = calc_altitude(pres);
}

// ============================================================================
// Setup / Loop
// ============================================================================
namespace practices {

  void setup() {
    Serial.println("\n[P4] Altímetro Barométrico BMP180 (I2C)");

    Wire.begin(SDA_P, SCL_P);

    Serial.printf("I2C: SDA=%d, SCL=%d\n", SDA_P, SCL_P);

    // Verificar ID
    uint8_t id = bmp_read8(REG_ID);
    if (id != 0x55) {
      Serial.printf("ERROR: BMP180 no detectado (ID=0x%02X, esperado 0x55)\n", id);
      Serial.println("Verifica conexiones I2C.");
      return;
    }
    Serial.println("BMP180 detectado (ID=0x55)");

    if (!read_calibration()) {
      Serial.println("ERROR: Calibración inválida.");
      return;
    }

    // Mostrar coeficientes
    Serial.println("\n=== Coeficientes de Calibración ===");
    Serial.printf("  AC1=%d AC2=%d AC3=%d\n", AC1, AC2, AC3);
    Serial.printf("  AC4=%u AC5=%u AC6=%u\n", AC4, AC5, AC6);
    Serial.printf("  B1=%d B2=%d\n", B1, B2);
    Serial.printf("  MB=%d MC=%d MD=%d\n", MB, MC, MD);
    Serial.printf("  OSS=%d, QNH=%.1f hPa\n", OSS, SEA_LEVEL_PA / 100.0f);

    // Lectura inicial
    float T; int32_t P; float h;
    read_all(T, P, h);
    Serial.printf("\nInicial: T=%.1f°C  P=%.2f hPa  Alt=%.1f m\n",
                  T, P / 100.0f, h);

    Serial.println("\n=== Modos ===");
    Serial.println("1) Datos crudos (UT, UP)");
    Serial.println("2) Temperatura + Presión compensadas");
    Serial.println("3) Altímetro (altitud m/ft)");
    Serial.println("\nEscribe 1, 2 o 3 + ENTER. Default: 3 en 5s");

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

    Serial.printf("\nModo: %d\n", mode);
    Serial.println("Escribe 'm' + ENTER para cambiar modo.\n");
  }

  void loop() {
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

    // Lectura periódica (5 Hz)
    if (millis() - lastRead < 200) return;
    lastRead = millis();

    int32_t UT = read_raw_temp();
    int32_t UP = read_raw_pressure();
    float T = compensate_temp(UT);
    int32_t P = compensate_pressure(UP);
    float P_hPa = P / 100.0f;
    float h = calc_altitude(P);
    float h_ft = h * 3.28084f;

    switch (mode) {
      case 1:
        Serial.printf("UT: %ld  UP: %ld  T: %.1f°C  P: %ld Pa\n",
                      (long)UT, (long)UP, T, (long)P);
        break;

      case 2:
        Serial.printf("T: %.1f °C  |  P: %.2f hPa (%ld Pa)\n",
                      T, P_hPa, (long)P);
        break;

      case 3:
        Serial.printf("Alt: %.1f m (%.0f ft)  P: %.2f hPa  T: %.1f°C  QNH: %.1f\n",
                      h, h_ft, P_hPa, T, SEA_LEVEL_PA / 100.0f);
        break;
    }
  }
}
#endif
