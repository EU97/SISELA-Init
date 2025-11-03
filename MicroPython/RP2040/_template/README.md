# [Pn] · Título de la práctica (RP2040 + MicroPython)

Breve descripción: qué hace la práctica y qué aprenderás.

## Objetivos
- Objetivo 1
- Objetivo 2
- Objetivo 3

## Materiales
- Placa RP2040 (Raspberry Pi Pico, Pico W, o similar)
- Sensores/actuadores específicos
- Cables jumper y protoboard

## Diagrama de conexiones

![Wiring](./assets/wiring.svg)

- Fuente Mermaid editable: `assets/wiring.mmd`.
- **Nota de seguridad**: RP2040 usa pines de 3.3V tolerantes (NO 5V). ADC usa `read_u16()` con Vref = 3.3V (0-65535).
- El RP2040 tiene 3 canales ADC disponibles (GP26/ADC0, GP27/ADC1, GP28/ADC2) + 1 interno para temperatura.

## Mapa de pines

Consulta `PINES.md` para ver el mapeo detallado de GPxx vs funciones (GPIO, PWM, ADC, I2C, SPI, UART).

## Código

Archivo principal: `main.py`

- Parámetros ajustables al inicio (pines, frecuencias, constantes).
- Estructura recomendada: Config HW, Utilidades, Clases, Loop principal.
- Formato de salida: CSV con cabecera o logs con prefijos.
- **Diferencias con ESP32**:
  - ADC: usa `ADC.read_u16()` (16 bits, 0-65535) en lugar de `read()` (12 bits).
  - PWM: `PWM.freq()` y `PWM.duty_u16()` (0-65535) son similares.
  - Pines: numeración GPxx (GP0-GP28), LED onboard en GP25.

## Ejecución (Thonny o Pymakr)
1. Conecta la placa RP2040 por USB.
2. Selecciona el intérprete MicroPython (Raspberry Pi Pico) en Thonny o el puerto COM en Pymakr.
3. Sube `boot.py` y `main.py` a la placa.
4. Ejecuta `main.py` o reinicia la placa.
5. Observa la consola REPL y valida el comportamiento esperado.

## Visualización de datos

Revisa `docs/oscilograma.md` para graficar y analizar datos (si aplica CSV).

- Puedes copiar datos CSV desde el REPL a un archivo `.csv` y visualizar con Excel, LibreOffice o Python (Matplotlib/Pandas).

## Actividades sugeridas
- Ajusta parámetros (frecuencias, tiempos, constantes de calibración).
- Experimenta con diferentes pines PWM o ADC.
- Integra múltiples sensores/actuadores en un mismo programa.

## Solución de problemas
- **Pin no reconocido**: Verifica que uses GPxx (no Dx como Arduino).
- **ADC saturado o cero**: Confirma voltaje de entrada ≤3.3V y pin ADC correcto (GP26-28).
- **PWM sin señal**: Asegúrate de configurar `PWM(Pin(GPxx))` con `freq()` y `duty_u16()`.
- **Puerto no detectado**: Instala drivers o mantén presionado BOOTSEL al conectar para modo almacenamiento masivo.

## Recursos
- MicroPython RP2040: https://docs.micropython.org/en/latest/rp2/quickref.html
- Raspberry Pi Pico Datasheet: https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf

## Licencia y créditos
Material académico para prácticas con RP2040 + MicroPython. Uso libre con atribución.
