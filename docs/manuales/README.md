# Manuales de práctica (LaTeX)

Fuentes LaTeX de los manuales de práctica de SISELA-Init.

## Contexto

Los manuales originales (`~/Descargas/manuales/Manuales/pN.pdf`) se generaron con
LaTeX/MiKTeX en otra máquina y **sus fuentes `.tex` no están en el repositorio**. Estos
archivos **recrean** los manuales de **P4 y P5** (Fase 1) reproduciendo su contenido y
añadiendo:

- una sección nueva **«Análisis de Señales»** (muestreo/Nyquist/aliasing, DFT y ventanas,
  filtrado FIR/IIR, SNR/SINAD/ENOB/THD),
- los **modos de firmware** nuevos (P4: 6–7; P5: 5–7),
- la **toolkit PC** `tools/sisela_signal/` en «Equipo» y «Herramientas»,
- preguntas y entregables ampliados.

> **Fidelidad visual:** la tipografía y el estilo de los diagramas son *aproximados* a
> los PDF originales (fuentes: `libertinus` serif + `helvet` sans; diagramas en TikZ).
> El **contenido técnico** (ecuaciones, tablas del datasheet, procedimientos) es completo.

P6–P8 se recrearán en la Fase 2; P1–P3 solo si se solicita (Fase 3).

## Compilar

```bash
cd docs/manuales
make            # -> build/p4.pdf, build/p5.pdf
make p4         # solo P4
make clean      # borra auxiliares
```

Requiere `pdflatex` y los paquetes listados en el `Makefile` (TeX Live completo o MiKTeX).
Los PDF se generan en `build/` (ignorado por git).

## Archivos

| Archivo | Contenido |
|---|---|
| `preamble.tex` | estilo común FIME/UANL (portada, encabezado/pie «Página X de Y», cajas) |
| `p4.tex` | Práctica 4 — Altímetro barométrico BMP180 + análisis de señales |
| `p5.tex` | Práctica 5 — PWM y servomotores + análisis de señales |
| `Makefile` | compilación (2 pasadas para TOC y `\pageref`) |
