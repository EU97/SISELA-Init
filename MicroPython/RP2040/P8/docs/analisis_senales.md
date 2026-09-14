# Análisis de señales — Práctica 8 (Sistema Integrado)

P8 integra los sensores y actuadores de P2–P7 en un solo sistema. El foco del
análisis de señales aquí no es un canal aislado, sino la **cadena completa**
(sensor → procesamiento → actuador) y el **muestreo simultáneo de varios
canales**. También aplica el análisis de jitter de P5 al PWM de los ESC si el
[módulo opcional de dron](dron_2212.md) está habilitado.

Modos del firmware: **9) Análisis de señales** → 1) latencia, 2) muestreo
multicanal. Módulo dron: **8) Dron** → 4) jitter del PWM del ESC.
Herramienta PC: [`tools/sisela_signal/`](../../../../tools/sisela_signal/README.md).

## 1. Latencia de la cadena sensor → actuador

Cada ciclo de un sistema de control real tiene un retardo entre adquirir el
dato y aplicar la corrección. El modo 9→1 mide, con `ticks_us`, el tiempo de
`leer ADC (altitud) → calcular → mover servo (alerón)` en 200 ciclos y
reporta media, σ y la tasa de actualización efectiva (1/latencia media).

- Una latencia alta o muy variable (σ grande) limita el ancho de banda
  máximo que puede tener un lazo de control cerrado sobre este hardware.
- Compara la latencia con el periodo de un lazo de vuelo real (p. ej. un
  controlador de vuelo típico corre el lazo de actitud a 1–8 kHz — muy por
  encima de lo que un `main.py` interpretado en MicroPython puede lograr;
  es una de las razones por las que los controladores de vuelo reales usan
  C/C++ compilado con interrupciones, no un intérprete).

## 2. Muestreo multicanal y anti-aliasing

El modo 9→2 muestrea los 4 sensores ADC (altitud, velocidad, actitud, luz)
a una Fs común y emite `t_us,alt_m,spd_kt,att_deg,lux`. Preguntas a resolver:

- ¿Los 4 canales se leen realmente al mismo instante, o hay un *skew*
  (desfase) entre ellos por leerlos secuencialmente? Con Fs=50 Hz y 4
  lecturas ADC (~100 µs cada una en el peor caso), el *skew* es pequeño
  frente al periodo de muestreo, pero crece si se añaden más canales o un
  sensor más lento (p. ej. I2C).
- Cada canal tiene su propio ancho de banda físico: la actitud puede
  cambiar en décimas de segundo, la luz ambiente en segundos. Elegir una
  única Fs para todos implica sobremuestrear los canales lentos o
  submuestrear los rápidos — discutir el compromiso.
- Con el generador de funciones inyectando un seno conocido en uno de los
  canales ADC (como en P5, modo 6), se puede verificar el aliasing también
  aquí y decidir si la Fs elegida es suficiente para la dinámica esperada
  del sensor real que ese canal representa (velocidad, altitud, etc.).

```bash
python -m sisela_signal spectrum --file cap.csv --col alt_m --psd
python -m sisela_signal spectrum --file cap.csv --col spd_kt --psd
python -m sisela_signal alias    --file cap.csv --col att_deg --true-f <f_generador>
```

## 3. Jitter del PWM de los ESC (módulo dron)

Idéntico en método al modo 5 de P5, aplicado a la señal que llega a cada
ESC. Ver [dron_2212.md](dron_2212.md) sección 6. Un jitter alto en la señal
del ESC se traduce en variación del empuje motor a motor, relevante para la
estabilidad de un cuadricóptero real.

## 4. Procedimiento sugerido

1. Modo 9 → 1: capturar 3 corridas de latencia y promediar. Anotar en la
   Tabla 8-A.
2. Modo 9 → 2: capturar un bloque multicanal en reposo (sin excitar los
   sensores) y con el generador inyectando un seno en el canal de actitud.
3. (Si `ENABLE_DRONE=True`) Modo 8 → 4: jitter del ESC M1, comparar con la
   Tabla 5-A de la Práctica 5.

## 5. Tablas de registro

**Tabla 8-A — Latencia de la cadena de control**

| Corrida | media (µs) | σ (µs) | tasa efectiva (Hz) |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |

**Tabla 8-B — Muestreo multicanal (Fs=50 Hz)**

| Canal | Fs real (Hz) | jitter σ (µs) | ¿aliasing detectado? |
|---|---|---|---|
| altitud | | | |
| velocidad | | | |
| actitud | | | |
| luz | | | |

## 6. Preguntas

1. ¿Qué limita la latencia medida: el tiempo de conversión ADC, el
   intérprete de MicroPython, o la escritura del PWM del servo?
2. Si quisieras reducir la latencia a la mitad, ¿qué cambiarías primero:
   el lenguaje (MicroPython → C++), el hardware (ESP32 → RP2040), o el
   algoritmo?
3. ¿Por qué un controlador de vuelo real corre su lazo de actitud en C/C++
   con interrupciones y no en un lenguaje interpretado?
4. En el muestreo multicanal, ¿qué pasaría si uno de los 4 sensores fuera
   en realidad un I2C lento (como el BMP180 de P4) en lugar de un ADC? ¿Cómo
   cambiaría el diseño del muestreo multicanal?
