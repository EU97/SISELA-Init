# Mapa de pines — Práctica 4: MPX5500DP (RP2040)

Conexión del sensor de presión piezoresistivo MPX5500DP al **RP2040** mediante ADC.

## Tabla de conexiones

| Señal | Pin RP2040 | Dispositivo externo | Descripción |
|-------|------------|---------------------|-------------|
| **ADC_IN** | **GP26** (ADC0) | MPX5500DP Vout (pin 3) | Salida analógica del sensor (0.66–3.3V @ VS=3.3V) |
| 3V3(OUT) | 3V3(OUT) | MPX5500DP VS (pin 2) | Alimentación del sensor 3.3V |
| GND | GND | MPX5500DP GND (pin 1) | Tierra común |

## 🔄 Diferencias con ESP32

| Aspecto | ESP32 | RP2040 |
|---------|-------|--------|
| **Pin ADC** | GPIO34 (ADC1_CH6) | GP26 (ADC0) |
| **Resolución ADC** | 12 bits (0–4095) | 16 bits (0–65535) |
| **Rango voltaje** | 0–3.3V (con atenuación 11dB) | 0–3.3V (fijo) |
| **Configuración** | Requiere `atten()`, `width()` | No requiere configuración extra |
| **Función lectura** | `adc.read()` | `adc.read_u16()` |
| **Número de ADCs** | ADC1 (8 canales), ADC2 (10 canales) | 3 canales ADC externos (GP26-GP28) + ADC4 interno (temp) |

## Notas importantes

- **GP26 (ADC0)**: Pin multiuso que puede ser GPIO digital o entrada ADC.
- **Sin atenuación**: El RP2040 siempre mide 0–3.3V (no hay atenuación configurable).
- **Resolución superior**: 16 bits (65535 valores) vs 12 bits ESP32 (4095 valores).
- **Promediado**: 50 muestras por lectura para reducir ruido del ADC.
- **Alimentación del sensor (VS)**: El MPX5500DP especifica **VS = 4.75–5.25V** para máxima precisión. Con VS=3.3V:
  - El sensor sigue funcionando.
  - La sensibilidad disminuye a ~66% del nominal.
  - Rango de salida: ~0.66V (20 kPa) a ~2.1V (520 kPa).
  - **Solución recomendada**: Alimentar con VSYS (5V USB) y usar divisor resistivo 10kΩ+10kΩ para proteger ADC.

## Pinout MPX5500DP (SOT-223)

```
Vista frontal (cara con marcado):
 _____
|  1  |  GND (tierra)
|  2  |  VS (alimentación, 4.75–5.25V nominal)
|  3  |  Vout (salida analógica proporcional a presión)
|_____|
```

## Pinout RP2040 relevante

```
         RP2040 (Raspberry Pi Pico)
    ┌─────────────────────┐
    │                     │
GP26│ ADC0 ●              │ ADC usado para MPX5500DP
GP27│ ADC1 ●              │ (otros 3 canales ADC disponibles)
GP28│ ADC2 ●              │
    │      ●  ADC_VREF    │
    │                     │
    │      ● 3V3(OUT)     │ Alimentación sensor (3.3V)
    │      ● GND          │ Tierra común
    │      ● VSYS         │ 5V (para alimentar sensor con divisor)
    └─────────────────────┘
```

## Diagrama de conexiones

Ver **[assets/wiring.svg](assets/wiring.svg)** para diagrama visual completo.

Para editar el diagrama fuente: **[assets/wiring.mmd](assets/wiring.mmd)** (formato Mermaid).

### Generar diagrama estático

```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i assets/wiring.mmd -o assets/wiring.svg -b transparent
```

## Relación con modos del programa

| Modo | Usa calibración | Salida |
|------|-----------------|--------|
| 1 (ADC crudo) | No | Valor digital 0–65535 |
| 2 (Voltaje) | Opcional | 0–3.3V (corregido si calibración activa) |
| 3 (Presión kPa) | Opcional | 20–520 kPa (USA voltaje calibrado si activo) |
| 4 (CSV monitor) | Opcional | Timestamp, ADC, V, kPa |
| 5 (Calibración wizard) | N/A | Medición interactiva GND/3V3 |

## Calibración rápida (opcional)

1. Ejecuta **Modo 5** del programa.
2. Sigue instrucciones interactivas (conectar GP26 a GND, luego a 3V3).
3. Se guarda `calibration.json` con valores ADC medidos.
4. Para usar automáticamente, cambia `AUTO_USE_CALIBRATION = True` en `main.py`.

**Mejora**: Offset y ganancia lineales. **No corrige**: No linealidad completa del ADC RP2040.

Ver [**../_template/CALIBRACION.md**](../_template/CALIBRACION.md) para detalles teóricos.

## Comparativa de conversión ADC

### ESP32 (12 bits)
```python
voltage = (adc.read() / 4095.0) * 3.3  # 0-4095 → 0-3.3V
```

### RP2040 (16 bits)
```python
voltage = (adc.read_u16() / 65535.0) * 3.3  # 0-65535 → 0-3.3V
```

## Referencias

- **MPX5500DP Datasheet**: https://www.nxp.com/docs/en/data-sheet/MPX5500.pdf
- **RP2040 Datasheet**: https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf
- **Raspberry Pi Pico Pinout**: https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html
- **MicroPython RP2040**: https://docs.micropython.org/en/latest/rp2/quickref.html#adc-analog-to-digital-conversion
