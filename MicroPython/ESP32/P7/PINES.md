# PINES — P7 Motores a pasos

Dos configuraciones soportadas (elige una):

1) A4988/DRV8825 (NEMA 17)

- STEP → GPIO18 (configurable)
- DIR → GPIO19 (configurable)
- ENABLE (opcional) → GPIO5 (activo en LOW)
- MS1/MS2/MS3 (opcional) → fijan microstepping
- VMOT (motor) con fuente externa; GND en común con el ESP32

2) ULN2003 + 28BYJ-48 (5 V)

- IN1 → GPIO26
- IN2 → GPIO25
- IN3 → GPIO33
- IN4 → GPIO32
- VCC 5 V para el motor y GND común

Fin de carrera (opcional):

- ENDSTOP → GPIO4 (pull-up interno), contacto a GND

Consulta los diagramas `assets/wiring_*.svg` para detalles.
