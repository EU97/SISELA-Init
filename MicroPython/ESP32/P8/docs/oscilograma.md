# Oscilogramas — ESP32 P8

## Objetivo
Registrar las señales PWM y de control generadas por el ESP32 en la práctica P8, para documentar el comportamiento de los servos, motor DC y el driver de motor paso a paso (ULN2003/A4988).

## Señales a medir
- PWM de servos (GPIO25, GPIO26)
- PWM de motor DC (GPIO18)
- Señales de control para el driver de motor paso a paso (GPIO25, GPIO26, GPIO32, GPIO33)
- Señal de endstop (GPIO4)

## Ejemplo de oscilogramas

### 1. PWM Servo (50 Hz)
- Señal cuadrada, periodo 20 ms
- Pulso variable (1–2 ms)

### 2. PWM Motor DC
- Frecuencia y ciclo de trabajo variable según velocidad

### 3. Control Stepper (ULN2003/A4988)
- Secuencia de pulsos en los 4 pines de control
- Frecuencia según velocidad de avance

### 4. Endstop
- Transición de alto a bajo al presionar el switch

## Notas
- Utiliza un osciloscopio de 2 canales mínimo para comparar señales.
- Documenta capturas de pantalla y anota condiciones de prueba (posición, velocidad, etc).

---

> **Referencia:** Ver también los diagramas de cableado en `assets/` para identificar pines y conexiones.
