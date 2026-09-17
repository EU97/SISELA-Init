#include <Arduino.h>
#include "practices/practice.h"
#include "board_config.h"
#include "common/utils.h"
#include "common/flight_controls.h"
#include "common/siglab.h"
#include "pins/pins.h"

#if PRACTICE==5
// P5: Servomotor PWM (50 Hz)
// Modos:
//   1. Barrido automático 0-180-0°
//   2. Control manual por ADC (potenciómetro en adc_altitude si disponible)
//   5. Jitter de PWM (mantiene un ángulo fijo para medirlo con el osciloscopio)
//   6. Muestreo y aliasing (seno del generador -> ADC, bloque CSV a Fs fija)
//   7. Respuesta al escalón del servo-lazo (realimentación de posición por ADC)

static FlightControls controls;
static int mode = 1;
static int angle = 0;
static int step = 1;
static uint32_t lastUpdate = 0;

// ADC del RP2040 en Arduino: por defecto 10 bit. Se fija a 12 bit para igualar
// a MicroPython (0..4095) — inofensivo en ESP32 (ya es 12 bit).
static const int ADC_BITS = 12;
static const int ADC_FS = (1 << ADC_BITS) - 1;   // 4095
static const float ADC_VREF = 3.3f;

// Bloque para los modos 6 y 7
static int adcRead() { return analogRead(pins().adc_altitude); }

static void run_adc_block(float fs, uint16_t n, const char *note) {
  serialPrintf(Serial, "%s  Fs=%.1f Hz  n=%u  (Nyquist %.1f Hz)\n", note, fs, n, fs / 2.0f);
  const uint16_t N = 1024;
  siglab::BlockSampler<N> bs(fs);
  auto r = bs.run(adcRead);
  r.report(Serial);
  Serial.println("t_us,counts,v");
  for (uint16_t i = 0; i < N; i++)
    serialPrintf(Serial, "%lu,%.0f,%.4f\n", (unsigned long)r.t_us[i],
                  r.samples[i], r.samples[i] / ADC_FS * ADC_VREF);
  serialPrintf(Serial, "# fin fs_real=%.2f jitter_us=%.2f full_scale=%d\n",
                r.fs_actual, r.jitter_us, ADC_FS);
}

namespace practices {
  void setup() {
    Serial.println("[P5] Servomotor PWM + analisis de senales");
    serialPrintf(Serial, "Pin servo: %d\n", PIN_SERVO_AILERON);

    controls.begin(PIN_SERVO_AILERON, -1);
    analogReadResolution(ADC_BITS);

    if (pins().adc_altitude >= 0) {
      pinMode(pins().adc_altitude, INPUT);
      serialPrintf(Serial, "ADC en pin %d (%d bit)\n", pins().adc_altitude, ADC_BITS);
    }
    Serial.println("Modos: 1=Barrido 2=ADC 5=JitterPWM 6=Muestreo/aliasing 7=Escalon");
    Serial.println("Envia el numero + ENTER.  Toolkit PC: tools/sisela_signal/");

    angle = 90;
    controls.setAileron(angle);
  }

  void loop() {
    if (Serial.available()) {
      char c = Serial.read();
      if (c == '1') { mode = 1; Serial.println("Modo: Barrido"); }
      else if (c == '2' && pins().adc_altitude >= 0) { mode = 2; Serial.println("Modo: ADC"); }
      else if (c == '5') {
        mode = 5;
        controls.setAileron(90);
        Serial.println("Modo 5: manteniendo 90 (pulso ~1500 us). Mide con el osciloscopio:");
        Serial.println("  Measure -> Pulse Width -> StdDev.  ESP32 ~100 ns, RP2040 ~10 ns.");
      }
      else if (c == '6' && pins().adc_altitude >= 0) {
        Serial.println("Generador -> ADC: seno 0-3.3 V (offset 1.65 V). Verifica con el osciloscopio.");
        run_adc_block(2000.0f, 1024, "[modo 6] muestreo/aliasing:");
        Serial.println("PC: python -m sisela_signal alias --file cap.csv --true-f <f_gen>");
        mode = 0;
      }
      else if (c == '7' && pins().adc_altitude >= 0) {
        Serial.println("[modo 7] escalon 60->120 con realimentacion en ADC");
        controls.setAileron(60); delay(600);
        // pre-muestras, escalon, resto
        siglab::BlockSampler<64> pre(500.0f);
        auto rp = pre.run(adcRead);
        controls.setAileron(120);
        siglab::BlockSampler<448> post(500.0f);
        auto rq = post.run(adcRead);
        Serial.println("t_us,counts,v");
        for (uint16_t i = 0; i < 64; i++)
          serialPrintf(Serial, "%lu,%.0f,%.4f\n", (unsigned long)rp.t_us[i], rp.samples[i],
                        rp.samples[i] / ADC_FS * ADC_VREF);
        uint32_t off = rp.t_us[63];
        for (uint16_t i = 0; i < 448; i++)
          serialPrintf(Serial, "%lu,%.0f,%.4f\n", (unsigned long)(off + rq.t_us[i]), rq.samples[i],
                        rq.samples[i] / ADC_FS * ADC_VREF);
        Serial.println("# fin  PC: python -m sisela_signal characterize --file step.csv --col v --mode step");
        mode = 0;
      }
    }

    if (mode == 1 && millis() - lastUpdate >= 20) {
      lastUpdate = millis();
      angle += step;
      if (angle >= 180 || angle <= 0) step = -step;
      controls.setAileron(angle);
      if (angle % 30 == 0) { Serial.print("Angulo: "); Serial.println(angle); }
    } else if (mode == 2 && pins().adc_altitude >= 0 && millis() - lastUpdate >= 20) {
      lastUpdate = millis();
      int raw = analogRead(pins().adc_altitude);
      angle = map(raw, 0, ADC_FS, 0, 180);
      controls.setAileron(angle);
      static uint32_t lastLog = 0;
      if (millis() - lastLog >= 500) {
        lastLog = millis();
        serialPrintf(Serial, "ADC: %d -> Angulo: %d\n", raw, angle);
      }
    }
  }
}
#endif
