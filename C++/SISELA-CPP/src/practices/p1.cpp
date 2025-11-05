#include <Arduino.h>
#include "practices/practice.h"
#include "board_config.h"
#include "common/utils.h"
#include "pins/pins.h"

#if PRACTICE==1
// P1: Fundamentos de MCUs y Entorno de Desarrollo
// 4 modos: 1) Blink LED1, 2) Chaser 3 LEDs, 3) Monitor botones, 4) Integrado

// Pin mappings (usando campos de la tabla de forma creativa)
static int LED1_PIN;  // LED onboard (board::LED_PIN)
static int LED2_PIN;  // pins().servo_aileron
static int LED3_PIN;  // pins().servo_elevator
static int BTN1_PIN;  // pins().a4988.step
static int BTN2_PIN;  // pins().a4988.dir

// Estado
static uint8_t mode = 4;  // 1=blink, 2=chaser, 3=monitor, 4=integrated
static uint32_t lastToggle = 0;
static uint32_t lastSample = 0;
static int chaserPos = 0;
static bool blinkState = false;

// Modo integrado
static uint8_t speedIdx = 1;           // 0=200ms, 1=500ms, 2=1000ms
static const uint16_t speeds[3] = {200, 500, 1000};
static uint8_t pattern = 0;            // 0=chaser, 1=blink-all
static bool lastBtn1 = HIGH;
static bool lastBtn2 = HIGH;
static uint32_t lastDebounce = 0;

namespace practices {
  void setup() {
    Serial.println("\n[P1] Fundamentos de MCUs - LEDs y Botones");
    
    // LED1 onboard
#ifdef ARDUINO_ARCH_ESP32
    LED1_PIN = 2;  // GPIO2
#elif defined(ARDUINO_ARCH_RP2040)
    LED1_PIN = LED_BUILTIN;  // GP25
#endif
    
    // LED2, LED3 (externos)
    LED2_PIN = pins().servo_aileron;  // ESP32: GPIO4, RP2040: GP16
    LED3_PIN = pins().servo_elevator; // ESP32: GPIO5, RP2040: GP17
    
    // BTN1, BTN2 (reusando campos a4988)
    BTN1_PIN = pins().a4988.step;     // ESP32: GPIO13, RP2040: GP14
    BTN2_PIN = pins().a4988.dir;      // ESP32: GPIO14, RP2040: GP15
    
    // Configurar pines
    pinMode(LED1_PIN, OUTPUT);
    pinMode(LED2_PIN, OUTPUT);
    pinMode(LED3_PIN, OUTPUT);
    pinMode(BTN1_PIN, INPUT_PULLUP);  // activo LOW
    pinMode(BTN2_PIN, INPUT_PULLUP);
    
    digitalWrite(LED1_PIN, LOW);
    digitalWrite(LED2_PIN, LOW);
    digitalWrite(LED3_PIN, LOW);
    
#ifdef ARDUINO_ARCH_ESP32
    Serial.println("Plataforma: ESP32");
    Serial.printf("LEDs: GPIO%d (onboard), GPIO%d, GPIO%d\n", LED1_PIN, LED2_PIN, LED3_PIN);
    Serial.printf("Botones: GPIO%d, GPIO%d (pull-up, activo LOW)\n", BTN1_PIN, BTN2_PIN);
#elif defined(ARDUINO_ARCH_RP2040)
    Serial.println("Plataforma: RP2040");
    Serial.printf("LEDs: GP%d (onboard), GP%d, GP%d\n", LED1_PIN, LED2_PIN, LED3_PIN);
    Serial.printf("Botones: GP%d, GP%d (pull-up, activo LOW)\n", BTN1_PIN, BTN2_PIN);
#endif
    
    Serial.println("\n=== Menú de modos ===");
    Serial.println("1) Blink LED1");
    Serial.println("2) Secuencia 3 LEDs (chaser)");
    Serial.println("3) Monitor de entradas (BTN1/BTN2)");
    Serial.println("4) Integrado (BTN1=patrón, BTN2=velocidad)");
    Serial.println("\nEscribe 1, 2, 3 o 4 y ENTER. Default: 4 en 5s");
    
    // Esperar input 5 segundos
    uint32_t start = millis();
    while (millis() - start < 5000) {
      if (Serial.available()) {
        char c = Serial.read();
        if (c >= '1' && c <= '4') {
          mode = c - '0';
          // Limpiar buffer
          while (Serial.available()) Serial.read();
          break;
        }
      }
    }
    
    Serial.print("\n[P1] Modo seleccionado: ");
    Serial.println(mode);
    
    switch (mode) {
      case 1: Serial.println("Modo 1: Blink LED1 cada 1s"); break;
      case 2: Serial.println("Modo 2: Chaser 3 LEDs (300ms)"); break;
      case 3: Serial.println("Modo 3: Monitor botones (200ms)"); break;
      case 4: Serial.println("Modo 4: Integrado (BTN1=patrón, BTN2=velocidad)"); break;
    }
    Serial.println("Escribe 'm' y ENTER para volver al menú.\n");
  }

  void loop() {
    // Check para volver al menú
    if (Serial.available()) {
      char c = Serial.read();
      while (Serial.available()) Serial.read();
      if (c == 'm' || c == 'M') {
        Serial.println("\n[P1] Volviendo al menú...");
        setup();  // Re-setup para mostrar menú
        return;
      }
    }
    
    // Ejecutar modo actual
    switch (mode) {
      case 1: mode_blink(); break;
      case 2: mode_chaser(); break;
      case 3: mode_monitor(); break;
      case 4: mode_integrated(); break;
    }
  }
  
  // Modo 1: Blink LED1 cada 1 segundo
  void mode_blink() {
    if (millis() - lastToggle >= 1000) {
      lastToggle = millis();
      blinkState = !blinkState;
      digitalWrite(LED1_PIN, blinkState ? HIGH : LOW);
      Serial.println(blinkState ? "LED1 ON" : "LED1 OFF");
    }
  }
  
  // Modo 2: Chaser en 3 LEDs (300ms cada uno)
  void mode_chaser() {
    if (millis() - lastToggle >= 300) {
      lastToggle = millis();
      
      // Apagar todos
      digitalWrite(LED1_PIN, LOW);
      digitalWrite(LED2_PIN, LOW);
      digitalWrite(LED3_PIN, LOW);
      
      // Encender uno
      switch (chaserPos) {
        case 0: digitalWrite(LED1_PIN, HIGH); break;
        case 1: digitalWrite(LED2_PIN, HIGH); break;
        case 2: digitalWrite(LED3_PIN, HIGH); break;
      }
      
      chaserPos = (chaserPos + 1) % 3;
    }
  }
  
  // Modo 3: Monitor botones (reflejar en LED2/LED3)
  void mode_monitor() {
    if (millis() - lastSample >= 200) {
      lastSample = millis();
      
      bool btn1 = digitalRead(BTN1_PIN) == LOW;  // pulsado
      bool btn2 = digitalRead(BTN2_PIN) == LOW;
      
      // Reflejar en LEDs
      digitalWrite(LED2_PIN, btn1 ? HIGH : LOW);
      digitalWrite(LED3_PIN, btn2 ? HIGH : LOW);
      
      Serial.print("BTN1=");
      Serial.print(btn1 ? "PRESSED" : "RELEASED");
      Serial.print(" | BTN2=");
      Serial.println(btn2 ? "PRESSED" : "RELEASED");
    }
  }
  
  // Modo 4: Integrado - BTN1 alterna patrón, BTN2 cambia velocidad
  void mode_integrated() {
    uint32_t now = millis();
    
    // Lectura de botones con debounce
    bool btn1 = digitalRead(BTN1_PIN) == LOW;
    bool btn2 = digitalRead(BTN2_PIN) == LOW;
    
    if (now - lastDebounce > 120) {
      // Detectar flanco descendente BTN1 (patrón)
      if (btn1 && !lastBtn1) {
        pattern ^= 1;  // toggle
        Serial.print("[Integrado] Patrón -> ");
        Serial.println(pattern == 0 ? "chaser" : "blink-all");
        lastDebounce = now;
      }
      
      // Detectar flanco descendente BTN2 (velocidad)
      if (btn2 && !lastBtn2) {
        speedIdx = (speedIdx + 1) % 3;
        Serial.print("[Integrado] Velocidad -> ");
        Serial.print(speeds[speedIdx]);
        Serial.println(" ms");
        lastDebounce = now;
      }
      
      lastBtn1 = btn1;
      lastBtn2 = btn2;
    }
    
    // Ejecutar patrón actual
    uint16_t period = speeds[speedIdx];
    
    if (pattern == 0) {
      // Chaser
      if (now - lastToggle >= period) {
        lastToggle = now;
        
        digitalWrite(LED1_PIN, LOW);
        digitalWrite(LED2_PIN, LOW);
        digitalWrite(LED3_PIN, LOW);
        
        switch (chaserPos) {
          case 0: digitalWrite(LED1_PIN, HIGH); break;
          case 1: digitalWrite(LED2_PIN, HIGH); break;
          case 2: digitalWrite(LED3_PIN, HIGH); break;
        }
        
        chaserPos = (chaserPos + 1) % 3;
      }
    } else {
      // Blink all
      if (now - lastToggle >= period) {
        lastToggle = now;
        blinkState = !blinkState;
        digitalWrite(LED1_PIN, blinkState ? HIGH : LOW);
        digitalWrite(LED2_PIN, blinkState ? HIGH : LOW);
        digitalWrite(LED3_PIN, blinkState ? HIGH : LOW);
      }
    }
  }
}

#endif
