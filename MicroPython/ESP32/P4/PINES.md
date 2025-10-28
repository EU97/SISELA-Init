# Mapa de pines — Práctica 4: MPX5500DP

Conexión del sensor de presión piezoresistivo MPX5500DP al ESP32 mediante ADC.

## Tabla de conexiones

| Señal | Pin ESP32 | Dispositivo externo | Descripción |
|-------|-----------|---------------------|-------------|
| **ADC_IN** | **GPIO34** (ADC1_CH6) | MPX5500DP Vout (pin 3) | Salida analógica del sensor (0.66–3.3V @ VS=3.3V) |
| 3V3 | 3V3 | MPX5500DP VS (pin 2) | Alimentación del sensor (ver nota de 5V) |
| GND | GND | MPX5500DP GND (pin 1) | Tierra común |

## Notas importantes

- **GPIO34 (ADC1_CH6)**: Pin de **entrada exclusiva** (input-only), no puede usarse como salida digital.
- **Atenuación 11dB**: Configurada en software para rango 0–3.3V (ADC de 12 bits → 0–4095).
- **Promediado**: 50 muestras por lectura para reducir ruido del ADC.
- **Alimentación del sensor (VS)**: El MPX5500DP especifica **VS = 4.75–5.25V** para máxima precisión. Con VS=3.3V:
  - El sensor sigue funcionando.
  - La sensibilidad disminuye a ~66% del nominal.
  - Rango de salida: ~0.66V (20 kPa) a ~2.1V (520 kPa).
  - **Solución recomendada**: Alimentar con 5V y usar divisor resistivo 10kΩ+10kΩ para proteger ADC.

## Pinout MPX5500DP (SOT-223)

```
Vista frontal (cara con marcado):
 _____
|  1  |  GND (tierra)
|  2  |  VS (alimentación, 4.75–5.25V nominal)
|  3  |  Vout (salida analógica proporcional a presión)
|_____|
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
| 1 (ADC crudo) | No | Valor digital 0–4095 |
| 2 (Voltaje) | Opcional | 0–3.3V (corregido si calibración activa) |
| 3 (Presión kPa) | Opcional | 20–520 kPa (USA voltaje calibrado si activo) |
| 4 (CSV monitor) | Opcional | Timestamp, ADC, V, kPa |
| 5 (Calibración wizard) | N/A | Medición interactiva GND/3V3 |

## Calibración rápida (opcional)

1. Ejecuta **Modo 5** del programa.
2. Sigue instrucciones interactivas (conectar GPIO34 a GND, luego a 3V3).
3. Se guarda `calibration.json` con valores ADC medidos.
4. Para usar automáticamente, cambia `AUTO_USE_CALIBRATION = True` en `main.py`.

**Mejora**: Offset y ganancia lineales. **No corrige**: No linealidad completa del ADC ESP32.

Ver [**../_template/CALIBRACION.md**](../_template/CALIBRACION.md) para detalles teóricos.

## Referencias

- **MPX5500DP Datasheet**: https://www.nxp.com/docs/en/data-sheet/MPX5500.pdf
- **ESP32 Pinout**: https://randomnerdtutorials.com/esp32-pinout-reference-gpios/
- **ADC ESP32 Characteristics**: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/adc.html
