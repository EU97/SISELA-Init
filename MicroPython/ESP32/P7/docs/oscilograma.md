# P7 — Formas de onda y mediciones (Motores a Pasos)

## Qué medir

### A4988/DRV8825 (NEMA 17)

- **STEP (GPIO18)**: tren de pulsos; frecuencia relacionada con RPM y pasos/revolución.
- **DIR (GPIO19)**: nivel alto/bajo define dirección de giro.
- **Intervalo entre pulsos STEP**: debe coincidir con cálculo de RPM a pasos/segundo.

### ULN2003 (28BYJ-48)

- **Secuencia IN1-IN4 (GPIO26, 25, 33, 32)**: patrones de activación para half-step o full-step.
- **Tiempo entre cambios de secuencia**: relacionado con RPM (4096 pasos/rev en half-step).

## Parámetros de prueba sugeridos

- **RPM**: 30, 60, 120 (variar según driver y carga mecánica).
- **Pasos**: 200 (una revolución NEMA 1/1), 100 (media vuelta), valores negativos para retroceso.
- **Frecuencia esperada de STEP**: para NEMA a 60 RPM con 200 pasos/rev → ~200 Hz.

## Capturas esperadas

### A4988/DRV8825

- Canal 1: STEP (pulsos rectangulares 0-3.3 V).
- Canal 2: DIR (nivel constante durante movimiento en una dirección).
- Medir período de STEP y verificar coincidencia con RPM configurado.

### ULN2003

- Canales en IN1-IN4: observar secuencia de activación (ejemplo half-step: 1-0-0-0, 1-1-0-0, 0-1-0-0, etc.).
- Intervalo de tiempo entre cambios de estado relacionado con velocidad en RPM.

## Notas

- Verifica GND común entre ESP32 y fuente del motor.
- Para NEMA, ajusta VREF del driver para corriente nominal del motor.
- Si el motor vibra sin girar, revisa secuencia (ULN2003) o cableado de bobinas (NEMA).
- En modo homing, el fin de carrera debe detener el motor al alcanzar el límite (valor=0 en GPIO4).
