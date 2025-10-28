# SISELA-Init

Introducción a los Sistemas Eléctricos de Aeronaves (SISELA): un repositorio didáctico para desarrollar, comparar y documentar prácticas de instrumentación y sistemas embebidos en dos plataformas de hardware (ESP32 y RP2040) y dos enfoques de software (C++ y MicroPython).

## Objetivo del repositorio

- Reforzar los fundamentos de adquisición de datos, acondicionamiento de señales, control básico y comunicación en sistemas embebidos aplicados a aeronáutica.
- Implementar las mismas prácticas (P1..P8) en C++ y en MicroPython, y en ESP32 y RP2040, para contrastar tiempos de desarrollo, rendimiento y portabilidad.
- Fomentar documentación clara y reproducible: cada práctica incluye objetivos, metodología, resultados esperados y bitácora de pruebas. Las conexiones y diagramas se documentarán cuando implementemos cada programa específico.

## ¿Por qué varios lenguajes y plataformas?

- C++: máximo control, rendimiento y ecosistema maduro (drivers, RTOS, bibliotecas). Requiere ciclos de compilación y mayor cuidado de memoria/tiempos.
- MicroPython: desarrollo rápido, iteración interactiva y curva de aprendizaje suave; ideal para prototipos y docencia.
- ESP32: Wi‑Fi/BLE integrados, doble núcleo, ADC y periféricos robustos.
- RP2040: microcontrolador de propósito general económico, PIO para I/O determinista y muy buen soporte educativo.

Comparar ambos enfoques te ayuda a elegir la herramienta adecuada según restricciones de tiempo, costo, rendimiento y mantenimiento.

## Estructura del repositorio

- `C++/ESP32/` y `C++/RP2040/`: Implementaciones en C++ por práctica (P1..P8).
- `MicroPython/ESP32/` y `MicroPython/RP2040/`: Implementaciones en MicroPython por práctica (P1..P8).
- Cada práctica tendrá su propio `README.md` con objetivos, materiales, pasos, validaciones y resultados.

Nota: si ves referencias antiguas a “Mircorpython/”, se están migrando a `MicroPython/` y quedarán deprecadas una vez validada la nueva estructura.

## Descripciones generales de las prácticas (P1..P8)

Estas descripciones son intencionalmente generales; los detalles de conexiones/diagramas se agregarán cuando entremos a cada implementación.

- P1 · Entradas/Salidas digitales y temporización
	- Objetivo: dominar GPIO, lectura de botones con anti‑rebote, salidas digitales y temporización (parpadeo, PWM básico para LED/servo).
	- Resultados esperados: manejo confiable de señales digitales y generación de patrones temporales.

- P2 · Adquisición analógica (ADC) con sensor de posición
	- Objetivo: configurar el ADC, muestrear una señal analógica y convertirla a unidades físicas (posición/ángulo) con calibración simple.
	- Resultados esperados: curva entrada‑salida y verificación de resolución/ruido del ADC.

- P3 · Medición de temperatura con NTC
	- Objetivo: medir temperatura usando un divisor resistivo con NTC, linealizar o tabular la conversión y caracterizar la sensibilidad.
	- Resultados esperados: tabla/ecuación T(ADC), comparación con referencia y análisis de error.

- P4 · Medición de presión con ADC y acondicionamiento opcional
	- Objetivo: leer un transductor de presión, aplicar acondicionamiento (offset/ganancia/filtrado) y validar rango operativo.
	- Resultados esperados: gráfica presión vs. lectura digital y criterios de saturación/ruido.

- P5 · Sensores digitales por bus (I²C/SPI)
	- Objetivo: integrar un sensor digital (p. ej., barómetro/IMU) por I²C o SPI, leer registros y verificar calibraciones internas.
	- Resultados esperados: lectura estable de magnitudes y comprensión del protocolo y temporizaciones.

- P6 · Comunicación serie y telemetría básica
	- Objetivo: enviar/recibir datos por UART/USB, definir un formato de trama y visualizar en una PC (consola o plotter).
	- Resultados esperados: telemetría en tiempo real y logs en CSV.

- P7 · Filtrado y registro de datos
	- Objetivo: aplicar filtros simples (media móvil, RC digital), detectar eventos y registrar datos para análisis posterior.
	- Resultados esperados: series temporales comparando crudo vs. filtrado y evaluación del retardo.

- P8 · Integración y validación del sistema
	- Objetivo: combinar sensores/actuadores, cerrar ciclo (si aplica), calibrar, validar y documentar lecciones aprendidas.
	- Resultados esperados: demo final funcional con criterios de aceptación y reporte técnico.

## Índice de prácticas

### C++ · ESP32
- [P1](C++/ESP32/P1/README.md)
- [P2](C++/ESP32/P2/README.md)
- [P3](C++/ESP32/P3/README.md)
- [P4](C++/ESP32/P4/README.md)
- [P5](C++/ESP32/P5/README.md)
- [P6](C++/ESP32/P6/README.md)
- [P7](C++/ESP32/P7/README.md)
- [P8](C++/ESP32/P8/README.md)

### C++ · RP2040
- [P1](C++/RP2040/P1/README.md)
- [P2](C++/RP2040/P2/README.md)
- [P3](C++/RP2040/P3/README.md)
- [P4](C++/RP2040/P4/README.md)
- [P5](C++/RP2040/P5/README.md)
- [P6](C++/RP2040/P6/README.md)
- [P7](C++/RP2040/P7/README.md)
- [P8](C++/RP2040/P8/README.md)

### MicroPython · ESP32
- [P1](MicroPython/ESP32/P1/README.md)
- [P2](MicroPython/ESP32/P2/README.md)
- [P3](MicroPython/ESP32/P3/README.md)
- [P4](MicroPython/ESP32/P4/README.md)
- [P5](MicroPython/ESP32/P5/README.md)
- [P6](MicroPython/ESP32/P6/README.md)
- [P7](MicroPython/ESP32/P7/README.md)
- [P8](MicroPython/ESP32/P8/README.md)

### MicroPython · RP2040
- [P1](MicroPython/RP2040/P1/README.md)
- [P2](MicroPython/RP2040/P2/README.md)
- [P3](MicroPython/RP2040/P3/README.md)
- [P4](MicroPython/RP2040/P4/README.md)
- [P5](MicroPython/RP2040/P5/README.md)
- [P6](MicroPython/RP2040/P6/README.md)
- [P7](MicroPython/RP2040/P7/README.md)
- [P8](MicroPython/RP2040/P8/README.md)
