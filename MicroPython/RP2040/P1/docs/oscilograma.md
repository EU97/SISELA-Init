# Oscilogramas — Práctica P1 (RP2040)

Este documento ilustra, de forma simplificada, las señales esperadas para los modos principales.

> Nota: Son diagramas ASCII orientativos para comprender tiempos y relaciones. En la práctica, los niveles estarán en 0V/3.3V.

## Blink (Modo 1)

- Periodo por defecto: 1.0 s (50% duty).
- Señal observada en GP25 (LED1 onboard):

```
Tiempo (s): 0      0.5     1.0     1.5     2.0
GP25     : ┌───────┐       ┌───────┐       ┌────
          │       │       │       │       │
          │       │       │       │       │
          └───────┘───────└───────┘───────└───
Nivel    : 1       0       1       0       1
```

## Chaser (Modo 2)

- Tres LEDs encendidos secuencialmente con un retardo `period_s = 0.3 s` entre cada cambio.
- Señales en GP25 (LED1), GP16 (LED2), GP17 (LED3):

```
Tiempo (s): 0.0   0.3   0.6   0.9   1.2   1.5
LED1/GP25:  ┌───┐                     ┌───┐
           │   │                     │   │
           └───┘─────────────────────┘   └──
LED2/GP16:      ┌───┐                     ┌───
               │   │                     │   
               └───┘─────────────────────┘   
LED3/GP17:            ┌───┐                     
                     │   │                     
                     └───┘─────────────────────
```

## Monitor de entradas (Modo 3)

- `BTN1` (GP14) y `BTN2` (GP15) usan pull-up interno. Pulsar conecta a GND, leyendo 0 (LOW) en la entrada.
- En el modo monitor, `LED2` refleja `BTN1` y `LED3` refleja `BTN2`.

## Integrado (Modo 4)

- `BTN1` alterna patrón: `chaser` ↔ `blink-all`.
- `BTN2` cambia la velocidad cíclicamente entre `[0.2, 0.5, 1.0] s`.

### Blink-all (ilustración con periodo 0.5 s):

```
Tiempo (s): 0.0   0.5   1.0   1.5   2.0
LED1/2/3 :  ┌───┐      ┌───┐      ┌───
           │   │      │   │      │   
           └───┘──────└───┘──────└───
```

---

## Cómo medir (rápido)

- Conecta la sonda del osciloscopio a la GP de interés (p. ej. GP25) y la referencia a GND.
- Empieza por el modo 1 para validar amplitud y periodo; luego cambia a modo 2 para ver la secuencia.
- Para rebotes de botones (modo 4), observa GP14/GP15 al pulsar y suelta para identificar jitter/debounce.
