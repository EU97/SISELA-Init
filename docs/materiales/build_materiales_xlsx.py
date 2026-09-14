#!/usr/bin/env python3
"""Genera SISELA_Materiales.xlsx — materiales por práctica, clasificación y
repetición entre prácticas P1-P8 (incluye módulo opcional de dron P8)."""

import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.formatting.rule import CellIsRule

import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SISELA_Materiales.xlsx")

PRACTICAS = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]
PRACT_NOMBRE = {
    "P1": "Fundamentos GPIO", "P2": "ADC + ARINC429", "P3": "NTC / LM35",
    "P4": "Altímetro BMP180", "P5": "Servo PWM", "P6": "Conmutación PWM",
    "P7": "Motor a pasos", "P8": "Integración + Dron (2212, opcional)",
}

# ---------------------------------------------------------------------------
# Catálogo maestro. Cada fila: (componente, categoria, especificacion, unidad,
# tipo, {practica: cantidad}, notas)
# tipo: "Kit fijo" | "Fungible" | "Instrumento" | "Opcional (dron)"
# ---------------------------------------------------------------------------
CATALOGO = [
    ("Microcontrolador (ESP32 DevKit v1 o Raspberry Pi Pico RP2040)", "Microcontrolador",
     "WROOM-32 USB-UART, o RP2040 con MicroPython/Arduino", "pza", "Kit fijo",
     {p: 1 for p in PRACTICAS},
     "Elegir UNA plataforma para todo el curso; el repositorio soporta ambas. P8 opcionalmente usa 2 MCU (arquitectura distribuida)."),
    ("Cable USB (Micro-USB o USB-C según placa)", "Conector/Cableado",
     "Datos + alimentación, ≥1 m", "pza", "Kit fijo", {p: 1 for p in PRACTICAS}, "Reutilizable en todas las prácticas."),
    ("Protoboard 830 puntos", "Prototipado", "Doble riel de alimentación", "pza", "Kit fijo",
     {p: 1 for p in PRACTICAS}, "Una por estación; se reutiliza."),
    ("Cables Dupont (juego M-M, M-H, H-H)", "Conector/Cableado", "20 cm, surtido ≥40 pzas", "juego",
     "Kit fijo", {p: 1 for p in PRACTICAS}, "P4 requiere mínimo 4 M-H para I2C."),
    ("Multímetro digital", "Instrumento de laboratorio", "Voltaje/corriente/continuidad", "pza",
     "Instrumento", {p: 1 for p in PRACTICAS}, "Compartido por estación, no por estudiante."),

    ("LED difuso 5 mm (rojo/verde/ámbar)", "Actuador/Indicador", "20 mA típico", "pza", "Fungible",
     {"P1": 2}, "LED1 suele ser el onboard del MCU; LED2/LED3 externos."),
    ("Resistencia 220–330 Ω 1/4 W", "Pasivo", "Limitadora de corriente LED", "pza", "Fungible",
     {"P1": 2}, ""),
    ("Pulsador táctil (push button, 4 pines)", "Sensor/Entrada", "6x6 mm THT", "pza", "Fungible",
     {"P1": 2}, "Usa pull-up interno del MCU (BTN1/BTN2)."),

    ("Potenciómetro lineal 10 kΩ", "Sensor", "Eje simple, montaje THT", "pza", "Fungible",
     {"P2": 1, "P5": 2, "P6": 1, "P8": 3},
     "P5: 1 para control (modo 4) + 1 opcional de realimentación (modo 7, escalón). "
     "P8: altitud/velocidad/actitud (3 potenciómetros simulan sensores)."),
    ("Resistencia 10 kΩ 1/4 W (serie divisor)", "Pasivo", "Divisor de tensión NTC", "pza", "Fungible",
     {"P3": 1}, ""),
    ("Termistor NTC 10 kΩ @25 °C (β≈3950)", "Sensor", "Coeficiente Beta 3950 típico", "pza",
     "Fungible", {"P3": 1}, ""),
    ("Sensor de temperatura LM35 (TO-92)", "Sensor", "10 mV/°C, salida lineal", "pza", "Fungible",
     {"P3": 1}, "Sensor alternativo/comparativo de la misma práctica."),

    ("Módulo sensor BMP180 (GY-68)", "Sensor", "I2C 0x77, regulador y pull-ups integrados", "pza",
     "Fungible", {"P4": 1}, ""),

    ("Servomotor R/C (SG90 / MG90S)", "Actuador", "PWM 50 Hz, 500–2400 µs, ≤300 mA", "pza",
     "Fungible", {"P5": 1, "P8": 2}, "P8: superficies alerón + elevador. MG996R como alternativa de mayor torque."),
    ("Fuente de alimentación externa 5 V (1–2 A)", "Alimentación", "Dedicada al servo, GND común con el MCU",
     "pza", "Instrumento", {"P5": 1, "P8": 1}, "Nunca alimentar el servo desde el riel del MCU."),
    ("Capacitor electrolítico 470–1000 µF / 10–16 V", "Pasivo", "Desacoplo de alimentación del servo",
     "pza", "Fungible", {"P5": 1}, ""),
    ("Generador de funciones", "Instrumento de laboratorio",
     "Seno, ≥10 kHz, amplitud y offset ajustables", "pza", "Instrumento",
     {"P5": 1, "P8": 1}, "P5 modo 6 (aliasing); P8 modo 9 (muestreo multicanal, opcional)."),
    ("Osciloscopio (2 canales)", "Instrumento de laboratorio",
     "Con función Measure (Pulse Width, StdDev)", "pza", "Instrumento",
     {"P4": 1, "P5": 1, "P6": 1, "P7": 1, "P8": 1},
     "P4: opcional (bus I2C). P7: opcional (jitter STEP)."),

    ("Transistor NPN 2N2222A (TO-92)", "Semiconductor", "Señal / driver de baja potencia", "pza",
     "Fungible", {"P6": 1}, "Caso 1 (buzzer) y driver de Casos 2–3; reutilizable entre casos."),
    ("Transistor NPN de potencia TIP31C (TO-220)", "Semiconductor", "Conmutación low-side, ≤3 A",
     "pza", "Fungible", {"P6": 1}, "Caso 2: motor DC low-side."),
    ("Transistor PNP de potencia TIP32C (TO-220)", "Semiconductor", "Conmutación high-side, ≤3 A",
     "pza", "Fungible", {"P6": 1}, "Caso 3: motor DC high-side (preferido en aviónica)."),
    ("MOSFET canal N (IRF540N o similar)", "Semiconductor", "Conmutación de potencia, Vgs lógico",
     "pza", "Fungible", {"P8": 1}, "Etapa de potencia del motor/hélice de P8."),
    ("Buzzer activo 5 V", "Actuador/Indicador", "20 mA típico", "pza", "Fungible", {"P6": 1}, ""),
    ("Motor DC 12 V con hélice/rueda dummy", "Actuador", "0.5 A nominal / 1.5 A stall", "pza",
     "Fungible", {"P6": 1, "P8": 1}, "Simula bomba/hélice."),
    ("Kit de resistencias de base/pull-up (100 Ω–1.2 kΩ 1/4 W; 22–33 Ω 5 W)", "Pasivo",
     "Ver cálculos de RB y RPU del manual P6", "juego", "Fungible", {"P6": 1}, ""),
    ("Diodo rectificador 1N4001/1N4007", "Semiconductor", "Flyback de carga resistiva/ligera",
     "pza", "Fungible", {"P6": 1, "P8": 1}, "Buzzer (P6) y motor (P8)."),
    ("Diodo Schottky 1N5817/1N5819", "Semiconductor", "Flyback de motor DC, recuperación rápida",
     "pza", "Fungible", {"P6": 1}, ""),
    ("Disipador de calor TO-220", "Estructura/Térmico", "Para TIP31C/TIP32C si Tj excede el límite",
     "pza", "Fungible", {"P6": 1}, "Opcional según análisis térmico."),
    ("Fuente de alimentación DC variable/dual", "Instrumento de laboratorio",
     "3.3/5/12 V, ≥2 A, con límite de corriente", "pza", "Instrumento", {"P6": 1}, ""),
    ("Alambre AWG22 (surtido de colores)", "Conector/Cableado", "Para conexiones de potencia",
     "rollo", "Kit fijo", {"P6": 1}, ""),

    ("Driver de motor a pasos A4988/DRV8825", "Semiconductor/Módulo", "Bipolar, microstepping",
     "pza", "Fungible", {"P7": 1, "P8": 1}, "Alternativa a ULN2003."),
    ("Driver de motor a pasos ULN2003 (módulo)", "Semiconductor/Módulo", "Unipolar, Darlington",
     "pza", "Fungible", {"P7": 1, "P8": 1}, "Alternativa a A4988; conflicto de pines con ADC en RP2040 (ver PINES.md)."),
    ("Motor a pasos NEMA17 (bipolar)", "Actuador", "200 pasos/rev, 12 V", "pza", "Fungible",
     {"P7": 1, "P8": 1}, "Usar con A4988/DRV8825."),
    ("Motor a pasos 28BYJ-48 (unipolar)", "Actuador", "2048 pasos/rev (full-step), 5 V", "pza",
     "Fungible", {"P7": 1, "P8": 1}, "Usar con ULN2003; alternativa económica a NEMA17."),
    ("Microswitch fin de carrera (endstop)", "Sensor", "Normalmente abierto (NO)", "pza",
     "Fungible", {"P7": 1, "P8": 1}, ""),
    ("Fuente de alimentación 12 V (motor a pasos)", "Alimentación", "1–2 A según motor", "pza",
     "Instrumento", {"P7": 1}, "Puede compartirse con la fuente variable de P6."),

    ("LDR (fotorresistencia) + resistencia 10 kΩ", "Sensor", "Divisor de tensión, sensor de luz",
     "pza", "Fungible", {"P8": 1}, "Cuarto canal analógico de P8 (luminosidad)."),

    ("Motor brushless 2212 (900–1400 KV)", "Actuador", "15–20 A continuos, ~50–60 g", "pza",
     "Opcional (dron)", {"P8": 4}, "Módulo opcional de dron — ver docs/dron_2212.md. NO instalar hélice en banco."),
    ("ESC 20–30 A (BLHeli/SimonK, entrada PWM 50 Hz)", "Semiconductor/Módulo", "Con o sin BEC",
     "pza", "Opcional (dron)", {"P8": 4}, "Uno por motor 2212."),
    ("Hélice a juego con el motor (par CW/CCW)", "Estructura/Dron", "9–10\" típico, según motor",
     "juego", "Opcional (dron)", {"P8": 4}, "⚠️ Retirar SIEMPRE durante pruebas de banco."),
    ("Batería LiPo 3S 11.1 V (≥4000 mAh, ≥30C)", "Alimentación", "Con conector XT60 y balanceo",
     "pza", "Opcional (dron)", {"P8": 1}, "Alimentación dedicada de los ESC; nunca el riel del MCU."),
    ("Cargador balanceador LiPo", "Instrumento de laboratorio", "Compatible 2S–4S", "pza",
     "Opcional (dron)", {"P8": 1}, "Uso compartido del laboratorio."),
    ("Frame de dron clase 250–450 (configuración X)", "Estructura/Dron", "Fibra de vidrio/carbono",
     "pza", "Opcional (dron)", {"P8": 1}, ""),
    ("PDB (power distribution board)", "Estructura/Dron", "Reparto de potencia a los 4 ESC",
     "pza", "Opcional (dron)", {"P8": 1}, ""),
    ("Fusible/breaker de potencia", "Alimentación", "Según corriente pico de los 4 motores",
     "pza", "Opcional (dron)", {"P8": 1}, ""),
    ("Conector XT60 (par macho/hembra)", "Conector/Cableado", "Batería ↔ PDB", "par",
     "Opcional (dron)", {"P8": 2}, ""),
    ("Conector bullet 3.5 mm (juego de 3, por motor)", "Conector/Cableado",
     "Permite invertir 2 fases para cambiar el sentido de giro", "juego", "Opcional (dron)",
     {"P8": 4}, "Un juego de 3 conectores por motor (12 en total)."),
]

SOFTWARE = [
    ("Firmware MicroPython (ESP32 / RP2040)", "Firmware", "v1.23+ (ESP32) / v1.24+ (RP2040)", "Todas"),
    ("Thonny IDE, o VS Code + extensión Pymakr", "IDE", "Carga y REPL de MicroPython", "Todas"),
    ("PlatformIO Core + framework Arduino", "IDE/Build", "Compilación de C++/SISELA-CPP", "Todas (variante C++)"),
    ("Python 3.10+ con pyserial, numpy, scipy, matplotlib", "Toolkit PC", "tools/sisela_signal/", "P4–P8"),
    ("pytest", "Toolkit PC", "Pruebas de tools/sisela_signal (sin hardware)", "P4–P8"),
    ("TeX Live / MiKTeX + latexmk", "Documentación", "Compila docs/manuales/*.tex", "P4, P5 (manuales)"),
    ("mermaid-cli (@mermaid-js/mermaid-cli)", "Documentación", "Genera assets/wiring.svg desde .mmd", "Todas"),
]

# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
NAVY = "1F3864"
BLUE = "2E5395"
LIGHT = "DCE6F1"
GOLD = "BF8F00"
GREEN = "375623"
GREEN_L = "E2EFDA"
GREY_L = "F2F2F2"

HDR_FONT = Font(color="FFFFFF", bold=True, size=11)
HDR_FILL = PatternFill("solid", fgColor=NAVY)
TITLE_FONT = Font(color=NAVY, bold=True, size=16)
SUB_FONT = Font(color="595959", italic=True, size=10)
SECTION_FONT = Font(color="FFFFFF", bold=True, size=12)
SECTION_FILL = PatternFill("solid", fgColor=BLUE)
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)


def style_header_row(ws, row, ncols, fill=HDR_FILL, font=HDR_FONT):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = fill
        cell.font = font
        cell.alignment = CENTER
        cell.border = BORDER


def autosize(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def add_table(ws, ref, name, style="TableStyleMedium9"):
    t = Table(displayName=name, ref=ref)
    t.tableStyleInfo = TableStyleInfo(name=style, showRowStripes=True, showFirstColumn=False)
    ws.add_table(t)


# ---------------------------------------------------------------------------
wb = Workbook()

# === Hoja 1: Resumen ========================================================
ws = wb.active
ws.title = "Resumen"
ws.sheet_view.showGridLines = False
ws["B2"] = "SISELA-Init — Materiales de Laboratorio"
ws["B2"].font = TITLE_FONT
ws["B3"] = "Desglose, clasificación y repetición de materiales — Prácticas P1–P8"
ws["B3"].font = SUB_FONT
ws["B4"] = f"Generado {datetime.date.today().isoformat()} · SISELA-Init (FIME/UANL)"
ws["B4"].font = SUB_FONT

rows = [
    ("Hoja", "Contenido"),
    ("Materiales por Práctica", "Lista detallada por práctica: categoría, componente, especificación, cantidad, tipo y notas."),
    ("Clasificación", "Componentes agrupados por categoría (sensores, actuadores, semiconductores, pasivos, etc.)."),
    ("Repetición entre Prácticas", "Matriz componente × práctica (P1–P8) con cantidades, nº de prácticas que lo usan y cantidad recomendada a comprar."),
    ("Lista de Compras Consolidada", "Lista de compra deduplicada (asumiendo un kit reutilizado en las 8 prácticas), separada de los instrumentos de laboratorio y del módulo opcional de dron."),
    ("Software y Herramientas", "Firmware, IDE y herramientas PC necesarias (no son material físico)."),
]
r0 = 6
for i, (a, b) in enumerate(rows):
    ws.cell(row=r0 + i, column=2, value=a)
    ws.cell(row=r0 + i, column=3, value=b)
    if i == 0:
        style_header_row(ws, r0 + i, 1)  # placeholder, fixed below
for c, w in ((2, 30), (3, 90)):
    ws.column_dimensions[get_column_letter(c)].width = w
for c in (2, 3):
    cell = ws.cell(row=r0, column=c)
    cell.fill = HDR_FILL
    cell.font = HDR_FONT
    cell.alignment = WRAP
for i in range(1, len(rows)):
    for c in (2, 3):
        cell = ws.cell(row=r0 + i, column=c)
        cell.alignment = WRAP
        cell.border = BORDER
        if i % 2 == 0:
            cell.fill = PatternFill("solid", fgColor=GREY_L)

leg_row = r0 + len(rows) + 2
ws.cell(row=leg_row, column=2, value="Leyenda de \"Tipo\"").font = Font(bold=True, color=NAVY)
leyenda = [
    ("Kit fijo", "Se compra una vez por estación y se reutiliza en las 8 prácticas (MCU, protoboard, cables, multímetro)."),
    ("Fungible", "Material propio de una práctica específica (sensores, transistores, motores, etc.)."),
    ("Instrumento", "Equipo de banco compartido por estación, no por estudiante (osciloscopio, generador, fuentes)."),
    ("Opcional (dron)", "Solo si se habilita el módulo de dron con motores 2212 en P8 (ENABLE_DRONE=True)."),
]
for i, (a, b) in enumerate(leyenda):
    ws.cell(row=leg_row + 1 + i, column=2, value=a).font = Font(bold=True)
    ws.cell(row=leg_row + 1 + i, column=3, value=b).alignment = WRAP

note_row = leg_row + len(leyenda) + 3
ws.cell(row=note_row, column=2, value="Metodología").font = Font(bold=True, color=NAVY)
ws.cell(row=note_row + 1, column=2,
        value=("Catálogo construido a partir de las secciones \"Equipo y Materiales\" de los manuales "
               "P1–P8, los archivos PINES.md de cada práctica y docs/dron_2212.md (módulo opcional). "
               "Las cantidades asumen UN kit por estación reutilizado secuencialmente a lo largo del "
               "curso — no una compra independiente por práctica.")).alignment = WRAP
ws.merge_cells(start_row=note_row + 1, start_column=2, end_row=note_row + 3, end_column=8)

# === Hoja 2: Materiales por Práctica ========================================
ws2 = wb.create_sheet("Materiales por Práctica")
headers = ["Práctica", "Tema", "Categoría", "Componente", "Especificación", "Cantidad", "Unidad", "Tipo", "Notas"]
ws2.append(headers)
style_header_row(ws2, 1, len(headers))
ws2.freeze_panes = "A2"

r = 2
for comp, cat, spec, unidad, tipo, pracs, notas in CATALOGO:
    for p in PRACTICAS:
        if p in pracs:
            ws2.append([p, PRACT_NOMBRE[p], cat, comp, spec, pracs[p], unidad, tipo, notas])
            r += 1

last_row = r - 1
for row in ws2.iter_rows(min_row=2, max_row=last_row, min_col=1, max_col=len(headers)):
    for cell in row:
        cell.border = BORDER
        cell.alignment = WRAP
    if row[0].row % 2 == 0:
        for cell in row:
            cell.fill = PatternFill("solid", fgColor=GREY_L)

add_table(ws2, f"A1:I{last_row}", "MaterialesPorPractica")
autosize(ws2, [9, 20, 22, 46, 42, 10, 9, 16, 60])
ws2.column_dimensions["F"].alignment = CENTER

# === Hoja 3: Clasificación ==================================================
ws3 = wb.create_sheet("Clasificación")
cat_stats = {}
for comp, cat, spec, unidad, tipo, pracs, notas in CATALOGO:
    d = cat_stats.setdefault(cat, {"n_items": 0, "n_usos": 0, "ejemplos": []})
    d["n_items"] += 1
    d["n_usos"] += sum(pracs.values())
    if len(d["ejemplos"]) < 3:
        d["ejemplos"].append(comp)

headers3 = ["Categoría", "Componentes distintos", "Usos totales (suma en las 8 prácticas)", "Ejemplos"]
ws3.append(headers3)
style_header_row(ws3, 1, len(headers3))
ws3.freeze_panes = "A2"
for i, (cat, d) in enumerate(sorted(cat_stats.items(), key=lambda kv: -kv[1]["n_items"]), start=2):
    ws3.append([cat, d["n_items"], d["n_usos"], "; ".join(d["ejemplos"]) + ("…" if d["n_items"] > 3 else "")])
last3 = 1 + len(cat_stats)
for row in ws3.iter_rows(min_row=2, max_row=last3, min_col=1, max_col=4):
    for cell in row:
        cell.border = BORDER
        cell.alignment = WRAP
    if row[0].row % 2 == 0:
        for cell in row:
            cell.fill = PatternFill("solid", fgColor=GREY_L)
add_table(ws3, f"A1:D{last3}", "Clasificacion")
autosize(ws3, [30, 20, 26, 70])

# Totales
trow = last3 + 3
ws3.cell(row=trow, column=1, value="Total de componentes distintos catalogados").font = Font(bold=True)
ws3.cell(row=trow, column=2, value=len(CATALOGO)).font = Font(bold=True)

# === Hoja 4: Repetición entre Prácticas ====================================
ws4 = wb.create_sheet("Repetición entre Prácticas")
headers4 = (["Componente", "Categoría", "Tipo"] + PRACTICAS +
            ["Nº prácticas", "Cant. máx. simultánea", "Cant. recomendada a comprar", "Cant. si se comprara por práctica"])
ws4.append(headers4)
style_header_row(ws4, 1, len(headers4))
ws4.freeze_panes = "D2"

ncol_p1 = 4  # column D
for comp, cat, spec, unidad, tipo, pracs, notas in CATALOGO:
    row = [comp, cat, tipo] + [pracs.get(p, None) for p in PRACTICAS]
    n_pract = len(pracs)
    cant_max = max(pracs.values())
    cant_sum = sum(pracs.values())
    recomendada = cant_max if tipo in ("Kit fijo", "Instrumento") else cant_sum
    row += [n_pract, cant_max, recomendada, cant_sum]
    ws4.append(row)

last4 = 1 + len(CATALOGO)
for row in ws4.iter_rows(min_row=2, max_row=last4, min_col=1, max_col=len(headers4)):
    for cell in row:
        cell.border = BORDER
    row[0].alignment = WRAP
    row[1].alignment = WRAP
    for cell in row[3:]:
        cell.alignment = CENTER
    if row[0].row % 2 == 0:
        for cell in row:
            cell.fill = PatternFill("solid", fgColor=GREY_L)

# resalta celdas usadas (num >0) en las columnas de prácticas
p_col_start = 4
p_col_end = 4 + len(PRACTICAS) - 1
rng = f"{get_column_letter(p_col_start)}2:{get_column_letter(p_col_end)}{last4}"
ws4.conditional_formatting.add(
    rng, CellIsRule(operator="greaterThan", formula=["0"], fill=PatternFill("solid", fgColor=LIGHT))
)
# resalta "reutilizado en >=4 prácticas" en la columna Nº prácticas
npr_col = get_column_letter(4 + len(PRACTICAS))
rng2 = f"{npr_col}2:{npr_col}{last4}"
ws4.conditional_formatting.add(
    rng2, CellIsRule(operator="greaterThanOrEqual", formula=["4"],
                     fill=PatternFill("solid", fgColor=GREEN_L), font=Font(bold=True, color=GREEN))
)

add_table(ws4, f"A1:{get_column_letter(len(headers4))}{last4}", "Repeticion")
widths4 = [46, 22, 16] + [5] * len(PRACTICAS) + [12, 14, 16, 16]
autosize(ws4, widths4)

note4 = last4 + 2
ws4.cell(row=note4, column=1,
         value=("\"Cant. recomendada a comprar\" = cantidad máxima simultánea para Kit fijo/Instrumento "
                "(se reutiliza de práctica en práctica); = suma para material Fungible/Opcional "
                "(se consume o queda instalado en su circuito).")).font = SUB_FONT
ws4.merge_cells(start_row=note4, start_column=1, end_row=note4, end_column=8)

# === Hoja 5: Lista de Compras Consolidada ===================================
ws5 = wb.create_sheet("Lista de Compras Consolidada")
ws5.sheet_view.showGridLines = False
ws5["B2"] = "Lista de Compras Consolidada (1 kit por estación)"
ws5["B2"].font = TITLE_FONT

sections = [
    ("A. Kit fijo del estudiante/estación (reutilizado en las 8 prácticas)", ["Kit fijo"]),
    ("B. Material fungible por práctica (sensores, actuadores, semiconductores, pasivos)", ["Fungible"]),
    ("C. Instrumentos de laboratorio (compartidos, no por estudiante)", ["Instrumento"]),
    ("D. Módulo opcional — Dron con motores 2212 (solo si se habilita en P8)", ["Opcional (dron)"]),
]

r = 4
headers5 = ["Componente", "Categoría", "Especificación", "Cantidad a comprar", "Unidad", "Prácticas donde se usa", "Notas"]
for title, tipos in sections:
    ws5.cell(row=r, column=2, value=title).font = SECTION_FONT
    ws5.cell(row=r, column=2).fill = SECTION_FILL
    ws5.merge_cells(start_row=r, start_column=2, end_row=r, end_column=8)
    for c in range(2, 9):
        ws5.cell(row=r, column=c).fill = SECTION_FILL
    r += 1
    hdr_row = r
    for i, h in enumerate(headers5):
        ws5.cell(row=r, column=2 + i, value=h)
    style_header_row(ws5, hdr_row, len(headers5), fill=PatternFill("solid", fgColor=BLUE),
                     font=Font(color="FFFFFF", bold=True, size=10))
    # ajustar rango de columnas 2..8
    for c in range(2, 2 + len(headers5)):
        ws5.cell(row=hdr_row, column=c).border = BORDER
    r += 1
    items = [row for row in CATALOGO if row[4] in tipos]
    for comp, cat, spec, unidad, tipo, pracs, notas in items:
        cant_max = max(pracs.values())
        cant_sum = sum(pracs.values())
        cantidad = cant_max if tipo in ("Kit fijo", "Instrumento") else cant_sum
        practicas_usa = ", ".join(pracs.keys())
        vals = [comp, cat, spec, cantidad, unidad, practicas_usa, notas]
        for i, v in enumerate(vals):
            cell = ws5.cell(row=r, column=2 + i, value=v)
            cell.border = BORDER
            cell.alignment = WRAP if i in (0, 2, 6) else CENTER
        if (r - hdr_row) % 2 == 0:
            for c in range(2, 2 + len(vals)):
                ws5.cell(row=r, column=c).fill = PatternFill("solid", fgColor=GREY_L)
        r += 1
    r += 2  # espacio entre secciones

autosize(ws5, [4, 42, 22, 34, 16, 10, 22, 46])

# === Hoja 6: Software y Herramientas ========================================
ws6 = wb.create_sheet("Software y Herramientas")
headers6 = ["Herramienta", "Tipo", "Detalle", "Prácticas"]
ws6.append(headers6)
style_header_row(ws6, 1, len(headers6))
for row in SOFTWARE:
    ws6.append(list(row))
last6 = 1 + len(SOFTWARE)
for row in ws6.iter_rows(min_row=2, max_row=last6, min_col=1, max_col=4):
    for cell in row:
        cell.border = BORDER
        cell.alignment = WRAP
    if row[0].row % 2 == 0:
        for cell in row:
            cell.fill = PatternFill("solid", fgColor=GREY_L)
add_table(ws6, f"A1:D{last6}", "Software")
autosize(ws6, [42, 16, 46, 20])

# reordenar hojas
wb._sheets = [wb["Resumen"], wb["Materiales por Práctica"], wb["Clasificación"],
              wb["Repetición entre Prácticas"], wb["Lista de Compras Consolidada"],
              wb["Software y Herramientas"]]

import os
os.makedirs(os.path.dirname(OUT), exist_ok=True)
wb.save(OUT)
print("Guardado:", OUT)
print("Componentes catalogados:", len(CATALOGO))
