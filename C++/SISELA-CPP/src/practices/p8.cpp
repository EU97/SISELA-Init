#include <Arduino.h>
#include "practices/practice.h"
#include "board_config.h"
#include "common/utils.h"
#include "pins/pins.h"
#include "common/sensors.h"
#include "common/flight_controls.h"
#include "common/propulsion.h"
#include "common/landing_gear.h"
#include "common/esc.h"
#include "common/quad_mixer.h"
#include "common/siglab.h"

#if PRACTICE==8
// ============================================================================
// P8: Sistema Integrado de Control Aeronáutico — C++/PlatformIO
//
// Espejo funcional del firmware MicroPython (MicroPython/*/P8/main.py):
//   1) Panel de instrumentos       6) Diagnóstico del sistema
//   2) Control manual de superficies  7) Configuración (rápida)
//   3) Control de potencia         8) Dron: motores 2212 (ESC + mezclador X) [opcional]
//   4) Tren de aterrizaje          9) Análisis de señales (latencia / muestreo)
//   5) Piloto automático simple    m) volver al menú   q) apagar y quedar en reposo
//
// Módulo de dron (opcional, ENABLE_DRONE): 4x ESC controlan motores brushless
// tipo 2212 con la misma máquina de armado fail-safe que la versión
// MicroPython (lib/esc.py). Ver docs/dron_2212.md antes de energizar.
// ============================================================================

// --- Módulo opcional: dron con motores 2212 --------------------------------
// Cambia a 1 solo cuando tengas 4x ESC + motores 2212 conectados.
#define ENABLE_DRONE 0
#if defined(ARDUINO_ARCH_ESP32)
static const int ESC_PINS[4] = {13, 14, 16, 17};   // M1..M4
#else
static const int ESC_PINS[4] = {6, 7, 8, 9};       // M1..M4 (RP2040)
#endif
static const int ESC_MIN_US = 1000, ESC_MAX_US = 2000;

static FlightSensors sensors;
static FlightControls controls;
static PropulsionSystem propulsion;
static LandingGear gear;
static QuadESC quad;
static bool droneReady = false;

// ----------------------------------------------------------------------------
// Utilidades de E/S por serie (equivalentes a input()/wait_key() de Python)
// ----------------------------------------------------------------------------
static String readLineBlocking() {
  String s;
  while (true) {
    if (Serial.available()) {
      char c = (char)Serial.read();
      if (c == '\n' || c == '\r') { if (s.length()) return s; else continue; }
      s += c;
    }
  }
}

static bool checkMenuBreak() {
  if (Serial.available()) {
    char c = (char)Serial.peek();
    if (c == 'm' || c == 'M') {
      String s = Serial.readStringUntil('\n');
      return true;
    }
    Serial.read();  // descarta el carácter (barrido/estado, no es comando)
  }
  return false;
}

static int readKeyNonBlocking() {
  if (Serial.available()) return Serial.read();
  return -1;
}

// ----------------------------------------------------------------------------
// Modo 1: Panel de instrumentos
// ----------------------------------------------------------------------------
static void modeInstruments() {
  Serial.println(F("\n[P8] Panel de instrumentos. 'm'+ENTER para volver."));
  uint32_t last = 0;
  while (!checkMenuBreak()) {
    if (millis() - last >= 200) {
      last = millis();
      serialPrintf(Serial, "alt=%.2f  spd=%.2f  att=%.2f  lux=%.2f | aileron=%d elevator=%d | "
                    "thr=%.0f%% | endstop=%s\n",
                    sensors.altitude(), sensors.speed(), sensors.attitude(), sensors.light(),
                    controls.aileron(), controls.elevator(), propulsion.getThrottle(),
                    gear.endstopActive() ? "ON" : "off");
    }
  }
}

// ----------------------------------------------------------------------------
// Modo 2: Control manual de superficies
// ----------------------------------------------------------------------------
static void modeManualSurfaces() {
  Serial.println(F("\n[P8] Superficies: a/d aileron, w/s elevador, c centrar, m volver."));
  while (true) {
    int k = readKeyNonBlocking();
    if (k < 0) { delay(20); continue; }
    if (k == 'm' || k == 'M') return;
    if (k == 'a') controls.setAileron(controls.aileron() - 5);
    else if (k == 'd') controls.setAileron(controls.aileron() + 5);
    else if (k == 'w') controls.setElevator(controls.elevator() + 5);
    else if (k == 's') controls.setElevator(controls.elevator() - 5);
    else if (k == 'c') { controls.setAileron(90); controls.setElevator(90); }
    else continue;
    serialPrintf(Serial, "aileron=%d  elevator=%d\n", controls.aileron(), controls.elevator());
  }
}

// ----------------------------------------------------------------------------
// Modo 3: Control de potencia
// ----------------------------------------------------------------------------
static void modePower() {
  Serial.println(F("\n[P8] Potencia: +/- 5%%, 0-9 directo x10, SPACE emergencia, m volver."));
  while (true) {
    int k = readKeyNonBlocking();
    if (k < 0) { delay(20); continue; }
    if (k == 'm' || k == 'M') return;
    if (k == '+') propulsion.setThrottle(propulsion.getThrottle() + 5);
    else if (k == '-') propulsion.setThrottle(propulsion.getThrottle() - 5);
    else if (k == ' ') propulsion.emergencyStop();
    else if (k >= '0' && k <= '9') propulsion.setThrottle((k - '0') * 10);
    else continue;
    serialPrintf(Serial, "throttle=%.0f%%\n", propulsion.getThrottle());
  }
}

// ----------------------------------------------------------------------------
// Modo 4: Tren de aterrizaje
// ----------------------------------------------------------------------------
static void modeGear() {
  Serial.println(F("\n[P8] Tren: e extender, r retraer, h homing, s estado, m volver."));
  while (true) {
    int k = readKeyNonBlocking();
    if (k < 0) { delay(20); continue; }
    if (k == 'm' || k == 'M') return;
    if (k == 'e') gear.stepperStep(400, true, 600);
    else if (k == 'r') gear.stepperStep(400, false, 600);
    else if (k == 'h') { while (!gear.endstopActive()) gear.stepperStep(1, false, 800); }
    else if (k == 's') serialPrintf(Serial, "endstop=%s\n", gear.endstopActive() ? "ON" : "off");
  }
}

// ----------------------------------------------------------------------------
// Modo 5: Piloto automático simple
// ----------------------------------------------------------------------------
static void modeAutopilot() {
  Serial.println(F("\n[P8] Piloto automatico simple. 'm'+ENTER para desactivar."));
  propulsion.setThrottle(60);
  while (!checkMenuBreak()) {
    float att = sensors.attitude();  // 0..1
    int elevator = 90 - (int)((att - 0.5f) * 90);
    if (elevator < 45) elevator = 45; if (elevator > 135) elevator = 135;
    controls.setElevator(elevator);
    controls.setAileron(90);
    delay(100);
  }
  controls.setAileron(90); controls.setElevator(90);
  propulsion.setThrottle(0);
}

// ----------------------------------------------------------------------------
// Modo 6: Diagnóstico
// ----------------------------------------------------------------------------
static void modeDiagnostics() {
  Serial.println(F("\n[P8] Diagnostico..."));
  serialPrintf(Serial, "Sensores: alt=%.2f spd=%.2f att=%.2f lux=%.2f\n",
                sensors.altitude(), sensors.speed(), sensors.attitude(), sensors.light());
  controls.setAileron(45); delay(200); controls.setAileron(135); delay(200); controls.setAileron(90);
  propulsion.setThrottle(30); delay(300); propulsion.setThrottle(0);
  serialPrintf(Serial, "Endstop: %s\n", gear.endstopActive() ? "ACTIVADO" : "LIBRE");
  Serial.println(F("Diagnostico completado."));
}

// ----------------------------------------------------------------------------
// Modo 7: Configuración rápida
// ----------------------------------------------------------------------------
static void modeConfig() {
  Serial.println(F("\n[P8] Config: [1] centrar servos  [2] test rapido  m volver"));
  while (true) {
    int k = readKeyNonBlocking();
    if (k < 0) { delay(20); continue; }
    if (k == 'm' || k == 'M') return;
    if (k == '1') { controls.setAileron(90); controls.setElevator(90); Serial.println(F("Servos centrados.")); }
    else if (k == '2') { propulsion.setThrottle(30); delay(300); propulsion.setThrottle(0); Serial.println(F("Test OK.")); }
  }
}

// ----------------------------------------------------------------------------
// Modo 8: Dron con motores 2212 (ESC + mezclador X) — opcional
// ----------------------------------------------------------------------------
static void modeDrone() {
  if (!droneReady) {
    Serial.println(F("\n[P8] Modulo de dron no disponible."));
    Serial.println(F("Define ENABLE_DRONE 1 y conecta 4x ESC + motores 2212. Ver docs/dron_2212.md."));
    return;
  }
  Serial.println(F("\n[P8] DRON — motores 2212. RETIRA LAS HELICES antes de continuar."));
  Serial.println(F("[1] Armar 4 ESC  [2] Test individual  [3] Mezclador X  [4] Jitter PWM  [5] PARADA  m volver"));
  while (true) {
    int k = readKeyNonBlocking();
    if (k < 0) { delay(20); continue; }
    if (k == 'm' || k == 'M') { quad.emergencyStop(); return; }

    if (k == '1') {
      Serial.println(F("Confirma hélices retiradas: envía 'y' para continuar, cualquier otra tecla cancela."));
      while (Serial.available() == 0) {}
      int c = Serial.read();
      if (c == 'y' || c == 'Y') { quad.armAll(2000); Serial.println(F("4 ESC armados.")); }
      else Serial.println(F("Armado cancelado."));
    } else if (k == '2') {
      if (!quad.anyArmed()) { Serial.println(F("Arma los ESC primero (1).")); continue; }
      Serial.println(F("Motor 1-4 + ENTER:"));
      String idx = readLineBlocking(); int i = idx.toInt() - 1;
      if (i < 0 || i > 3) { Serial.println(F("Indice invalido.")); continue; }
      Serial.println(F("throttle% (<=20 recomendado sin helice) + ENTER, o 'm':"));
      while (true) {
        String v = readLineBlocking();
        if (v == "m" || v == "M") { quad.motor(i).stop(); break; }
        float pct = v.toFloat();
        float r = quad.motor(i).throttle(pct);
        serialPrintf(Serial, "M%d -> %.1f%% (pulso ~%.0fus)\n", i + 1, r, quad.motor(i).pulseUsNow());
      }
    } else if (k == '3') {
      if (!quad.anyArmed()) { Serial.println(F("Arma los ESC primero (1).")); continue; }
      Serial.println(F("Mezclador X: t/T throttle, r/R roll, p/P pitch, y/Y yaw, SPACE=estop, m=volver"));
      float thr = 0, roll = 0, pitch = 0, yaw = 0;
      while (true) {
        int kk = readKeyNonBlocking();
        if (kk < 0) { delay(20); continue; }
        if (kk == ' ') { quad.emergencyStop(); thr = roll = pitch = yaw = 0; Serial.println(F("EMERGENCIA.")); continue; }
        if (kk == 'm' || kk == 'M') { quad.emergencyStop(); break; }
        if (kk == 't') thr = max(0.0f, thr - 5); else if (kk == 'T') thr = min(100.0f, thr + 5);
        else if (kk == 'r') roll -= 10; else if (kk == 'R') roll += 10;
        else if (kk == 'p') pitch -= 10; else if (kk == 'P') pitch += 10;
        else if (kk == 'y') yaw -= 10; else if (kk == 'Y') yaw += 10;
        else continue;
        float m[4]; mixX(thr, roll, pitch, yaw, m);
        quad.setAll(m);
        serialPrintf(Serial, "thr=%.0f roll=%.0f pitch=%.0f yaw=%.0f -> M1=%.1f M2=%.1f M3=%.1f M4=%.1f\n",
                      thr, roll, pitch, yaw, m[0], m[1], m[2], m[3]);
      }
    } else if (k == '4') {
      if (!quad.anyArmed()) { Serial.println(F("Arma los ESC primero (1).")); continue; }
      serialPrintf(Serial, "Manteniendo M1 (pin %d) a 15%% 20s. CH1 osciloscopio -> ese pin.\n", ESC_PINS[0]);
      quad.motor(0).throttle(15);
      uint32_t t0 = millis();
      while (millis() - t0 < 20000) { if (checkMenuBreak()) break; delay(100); }
      quad.motor(0).stop();
      Serial.println(F("Listo. PC: python -m sisela_signal characterize --scope --file scopeCH1.csv --col CH1 --mode adc"));
    } else if (k == '5') {
      quad.emergencyStop(); quad.disarmAll();
      Serial.println(F("PARADA DE EMERGENCIA: 4 motores a 0% y ESC desarmados."));
    }
  }
}

// ----------------------------------------------------------------------------
// Modo 9: Análisis de señales (latencia / muestreo multicanal)
// ----------------------------------------------------------------------------
static void modeSignalAnalysis() {
  Serial.println(F("\n[P8] Analisis de senales: [1] latencia  [2] muestreo multicanal  m volver"));
  while (true) {
    int k = readKeyNonBlocking();
    if (k < 0) { delay(20); continue; }
    if (k == 'm' || k == 'M') return;

    if (k == '1') {
      const int N = 200;
      siglab::Stats st;
      for (int i = 0; i < N; i++) {
        uint32_t t0 = micros();
        float alt = sensors.altitude();
        controls.setAileron((int)(alt * 180));
        st.add(micros() - t0);
      }
      controls.setAileron(90);
      Serial.print("Latencia (us): "); st.report(Serial, "us");
      serialPrintf(Serial, "Tasa efectiva ~ %.1f Hz\n", st.mean() > 0 ? 1e6 / st.mean() : 0.0);
    } else if (k == '2') {
      const int Fs = 50, N = 500;
      serialPrintf(Serial, "Captura multicanal a %d Hz, %d muestras.\n", Fs, N);
      // Nombres de columna idénticos a la versión MicroPython (main.py del P8),
      // para que la misma toolkit PC (tools/sisela_signal) y los mismos
      // comandos funcionen sin cambios sobre cualquiera de las dos salidas.
      Serial.println(F("t_us,alt_m,spd_kt,att_deg,lux"));
      uint32_t period = 1000000UL / Fs, t0 = micros(), next = t0;
      for (int i = 0; i < N; i++) {
        while ((int32_t)(micros() - next) < 0) {}
        serialPrintf(Serial, "%lu,%.4f,%.4f,%.4f,%.4f\n", (unsigned long)(micros() - t0),
                      sensors.altitude(), sensors.speed(), sensors.attitude(), sensors.light());
        next += period;
      }
      Serial.println(F("# fin. PC: python -m sisela_signal spectrum --file cap.csv --col alt_m --psd"));
    }
  }
}

// ----------------------------------------------------------------------------
namespace practices {
  void setup() {
    Serial.println(F("[P8] Sistema Integrado de Control Aeronautico (C++)"));
    sensors.begin();
    controls.begin();
    propulsion.begin();
    gear.begin();
#if ENABLE_DRONE
    quad.begin(ESC_PINS, ESC_MIN_US, ESC_MAX_US);
    droneReady = true;
    Serial.println(F("[P8] Modulo dron listo (SIN ARMAR). Usa el modo 8, opcion 1."));
#else
    Serial.println(F("[P8] Modulo dron deshabilitado (ENABLE_DRONE 0)."));
#endif
    Serial.println(F("Listo. Escribe el numero de modo + ENTER."));
  }

  void loop() {
    Serial.println(F("\n1 Instrumentos  2 Superficies  3 Potencia  4 Tren  5 Autopiloto"));
    Serial.println(F("6 Diagnostico   7 Config       8 Dron(2212) 9 Analisis senales"));
    Serial.print(F("Selecciona opcion: "));
    String choice = readLineBlocking();
    choice.trim();

    if (choice == "1") modeInstruments();
    else if (choice == "2") modeManualSurfaces();
    else if (choice == "3") modePower();
    else if (choice == "4") modeGear();
    else if (choice == "5") modeAutopilot();
    else if (choice == "6") modeDiagnostics();
    else if (choice == "7") modeConfig();
    else if (choice == "8") modeDrone();
    else if (choice == "9") modeSignalAnalysis();
    else if (choice == "q" || choice == "Q") {
      controls.setAileron(90); controls.setElevator(90);
      propulsion.setThrottle(0);
      if (droneReady) { quad.emergencyStop(); quad.disarmAll(); }
      Serial.println(F("Sistema en reposo. Reinicia la placa para volver a operar."));
      while (true) delay(1000);
    } else {
      Serial.println(F("Opcion invalida."));
    }
  }
}
#endif
