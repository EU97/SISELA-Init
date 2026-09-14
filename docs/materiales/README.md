# Materiales de laboratorio — SISELA-Init

[`SISELA_Materiales.xlsx`](SISELA_Materiales.xlsx) — desglose de materiales de las
8 prácticas (P1–P8), su clasificación y su repetición entre prácticas, incluyendo
el módulo opcional de dron con motores 2212 de P8.

## Hojas

| Hoja | Contenido |
|---|---|
| Resumen | Portada, leyenda y metodología. |
| Materiales por Práctica | Lista detallada por práctica (formato largo, una fila por componente usado). |
| Clasificación | Componentes agrupados por categoría (sensores, actuadores, semiconductores, pasivos, …). |
| Repetición entre Prácticas | Matriz componente × práctica (P1–P8) con cantidades, nº de prácticas que lo usan y cantidad recomendada a comprar. |
| Lista de Compras Consolidada | Lista deduplicada en 4 bloques: kit fijo, fungible, instrumentos de laboratorio, módulo opcional de dron. |
| Software y Herramientas | Firmware/IDE/herramientas PC (no son material físico). |

## Metodología

Catálogo construido a partir de las secciones «Equipo y Materiales» de los
manuales P1–P8, los `PINES.md` de cada práctica y `docs/dron_2212.md`. Las
cantidades de la lista de compras asumen **un kit por estación reutilizado a lo
largo de las 8 prácticas**, no una compra independiente por práctica: los
componentes de tipo *Kit fijo* / *Instrumento* se cuentan por su máximo uso
simultáneo; los de tipo *Fungible* / *Opcional (dron)* se suman.

## Regenerar

El libro se genera con un script Python (`openpyxl`), no se edita a mano.
Contacta a quien mantiene el repositorio para actualizar el catálogo si cambian
los materiales de alguna práctica.
