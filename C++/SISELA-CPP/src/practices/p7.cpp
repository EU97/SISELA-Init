#include <Arduino.h>
#include "practices/practice.h"
#include "board_config.h"
#include "common/utils.h"
#include "common/landing_gear.h"
#include "pins/pins.h"

#if PRACTICE==7
// P7: Control de Motores a Pasos (A4988 o ULN2003)
// Modos: 1) Jog, 2) Mover N pasos, 3) Barrido, 4) Homing

static LandingGear stepper;
static uint8_t mode = 4;  // 1=jog, 2=move N, 3=sweep, 4=homing
static const int DEFAULT_RPM = 60;
static const int STEPS_PER_REV = 200;  // NEMA 17 typical
static const int MAX_STEPS_FORWARD = 400;  // límite barrido

namespace practices {
  
  // Convertir RPM → intervalo entre pasos (us)
  uint32_t rpm_to_interval_us(int rpm, int steps_per_rev) {
    if (rpm <= 0) return 100000;
    float steps_per_sec = (rpm * steps_per_rev) / 60.0;
    if (steps_per_sec <= 0) return 100000;
    return (uint32_t)(1000000.0 / steps_per_sec);
  }
  
  void setup() {
    Serial.println("\n[P7] Control de Motores a Pasos");
    
    stepper.begin();
    
#if defined(STEPPER_ULN2003)
    Serial.println("Driver: ULN2003 (28BYJ-48)");
    Serial.printf("Pines: IN1=GP%d, IN2=GP%d, IN3=GP%d, IN4=GP%d\n", 
                  PIN_STEPPER_IN1, PIN_STEPPER_IN2, PIN_STEPPER_IN3, PIN_STEPPER_IN4);
#else
    Serial.println("Driver: A4988/DRV8825");
    Serial.printf("Pines: STEP=GP%d, DIR=GP%d", PIN_STEPPER_STEP, PIN_STEPPER_DIR);
    if (PIN_STEPPER_EN >= 0) {
      Serial.printf(", EN=GP%d\n", PIN_STEPPER_EN);
    } else {
      Serial.println();
    }
#endif
    
    if (PIN_ENDSTOP >= 0) {
      Serial.printf("Endstop: GP%d (pull-up, activo LOW)\n", PIN_ENDSTOP);
    } else {
      Serial.println("Endstop: No configurado");
    }
    
    Serial.println("\n=== Modos ===");
    Serial.println("1) Jog ('+' avanza, '-' retrocede)");
    Serial.println("2) Mover N pasos (con RPM)");
    Serial.println("3) Barrido (avanza hasta límite/endstop, retrocede, repite)");
    Serial.println("4) Homing (buscar fin de carrera)");
    Serial.println("\nEscribe 1, 2, 3 o 4 y ENTER. Default: 4 en 5s");
    
    // Esperar input 5 segundos
    uint32_t start = millis();
    while (millis() - start < 5000) {
      if (Serial.available()) {
        char c = Serial.read();
        if (c >= '1' && c <= '4') {
          mode = c - '0';
          while (Serial.available()) Serial.read();
          break;
        }
      }
    }
    
    Serial.print("\n[P7] Modo seleccionado: ");
    Serial.println(mode);
    
    switch (mode) {
      case 1: 
        Serial.println("Modo 1: Jog. Escribe '+' o '-' y ENTER.");
        Serial.println("'m' para volver al menú.");
        break;
      case 2: 
        Serial.println("Modo 2: Mover N pasos.");
        Serial.println("Ingresa número de pasos (ej: 200, -200) y ENTER:");
        break;
      case 3: 
        Serial.println("Modo 3: Barrido continuo.");
        Serial.println("'m' para detener y volver al menú.");
        break;
      case 4: 
        Serial.println("Modo 4: Homing (buscar fin de carrera).");
        if (PIN_ENDSTOP < 0) {
          Serial.println("ADVERTENCIA: Endstop no configurado. Abortando homing.");
          mode = 1;  // Fallback a jog
        }
        break;
    }
    Serial.println();
  }

  void loop() {
    // Check menú
    if (Serial.available()) {
      char c = Serial.read();
      String input = String(c);
      while (Serial.available()) {
        input += (char)Serial.read();
        delay(1);
      }
      input.trim();
      
      if (input.equalsIgnoreCase("m")) {
        Serial.println("\n[P7] Volviendo al menú...");
        setup();
        return;
      }
      
      // Procesar según modo
      switch (mode) {
        case 1: mode_jog(input); break;
        case 2: mode_move_n(input); break;
        case 3: /* continuo, no necesita input */ break;
        case 4: /* homing al inicio */ break;
      }
    }
    
    // Ejecutar modo continuo
    if (mode == 3) {
      mode_sweep();
    } else if (mode == 4) {
      mode_homing();
      mode = 1;  // Después de homing, pasar a jog
    }
  }
  
  // Modo 1: Jog manual
  void mode_jog(String cmd) {
    uint32_t interval = rpm_to_interval_us(DEFAULT_RPM, STEPS_PER_REV);
    
    if (cmd == "+") {
      stepper.stepperStep(1, true, interval);
      Serial.println("→ Adelante (1 paso)");
    } else if (cmd == "-") {
      stepper.stepperStep(1, false, interval);
      Serial.println("← Atrás (1 paso)");
    } else {
      Serial.println("Usa '+' o '-' para mover, 'm' para menú.");
    }
  }
  
  // Modo 2: Mover N pasos
  void mode_move_n(String cmd) {
    int steps = cmd.toInt();
    
    if (steps == 0 && !cmd.startsWith("0")) {
      Serial.println("Entrada inválida. Ingresa número de pasos (ej: 200, -200):");
      return;
    }
    
    Serial.print("Moviendo ");
    Serial.print(steps);
    Serial.print(" pasos @ ");
    Serial.print(DEFAULT_RPM);
    Serial.println(" RPM...");
    
    uint32_t interval = rpm_to_interval_us(DEFAULT_RPM, STEPS_PER_REV);
    bool dir = steps > 0;
    stepper.stepperStep(abs(steps), dir, interval);
    
    Serial.println("Movimiento completado.");
    Serial.println("Ingresa próximo número de pasos o 'm' para menú:");
  }
  
  // Modo 3: Barrido continuo
  void mode_sweep() {
    static bool sweeping = false;
    static bool forward = true;
    static int moved = 0;
    static uint32_t lastStep = 0;
    
    if (!sweeping) {
      Serial.println("→ Avanzando hasta límite...");
      sweeping = true;
      forward = true;
      moved = 0;
    }
    
    uint32_t interval = rpm_to_interval_us(DEFAULT_RPM, STEPS_PER_REV);
    uint32_t now = millis();
    
    // Control de velocidad (no usar delay para permitir check de serial)
    if (now - lastStep < 10) return;
    lastStep = now;
    
    if (forward) {
      // Avanzar
      if (moved < MAX_STEPS_FORWARD && !stepper.endstopActive()) {
        stepper.stepperStep(1, true, interval);
        moved++;
      } else {
        if (stepper.endstopActive()) {
          Serial.println("Fin de carrera alcanzado.");
        } else {
          Serial.print("Límite alcanzado (");
          Serial.print(MAX_STEPS_FORWARD);
          Serial.println(" pasos).");
        }
        delay(1000);
        Serial.println("← Retrocediendo...");
        forward = false;
      }
    } else {
      // Retroceder
      if (moved > 0) {
        stepper.stepperStep(1, false, interval);
        moved--;
      } else {
        Serial.println("Posición inicial. Reiniciando barrido...\n");
        delay(1000);
        forward = true;
      }
    }
  }
  
  // Modo 4: Homing (buscar fin de carrera)
  void mode_homing() {
    if (PIN_ENDSTOP < 0) {
      Serial.println("[ERROR] Endstop no configurado. No se puede hacer homing.");
      return;
    }
    
    Serial.println("Homing: Retrocediendo hasta fin de carrera...");
    
    uint32_t interval = rpm_to_interval_us(DEFAULT_RPM / 2, STEPS_PER_REV);  // más lento
    int max_steps = 1000;  // límite de seguridad
    int steps_moved = 0;
    
    while (!stepper.endstopActive() && steps_moved < max_steps) {
      stepper.stepperStep(1, false, interval);  // retroceder
      steps_moved++;
      
      if (steps_moved % 50 == 0) {
        Serial.print(".");
      }
    }
    
    if (stepper.endstopActive()) {
      Serial.println("\n✓ Homing completado (fin de carrera alcanzado).");
    } else {
      Serial.println("\n⚠ Homing abortado (límite de seguridad alcanzado).");
    }
    
    delay(1000);
    Serial.println("Cambiando a modo Jog...\n");
  }
}

#endif
