"""
report — ensambla tablas y figuras de una sesión de análisis en un paquete
Markdown + PNG bajo reports/pN/ para pegar en el reporte AIAA.

    from sisela_signal.report import ReportBuilder
    rb = ReportBuilder("P5", outdir="reports/p5")
    rb.add_text("Fs medida", cap.summary())
    rb.add_figure("espectro", fig)
    rb.add_table("Métricas ADC", {"ENOB": 9.8, "SINAD_dB": 60.3})
    rb.write()
"""

from __future__ import annotations

import os
import time


class ReportBuilder:
    def __init__(self, practice: str, outdir: str | None = None, title: str | None = None):
        self.practice = practice
        self.outdir = outdir or os.path.join("reports", practice.lower())
        self.title = title or f"Análisis de señales — Práctica {practice}"
        self.blocks: list[tuple[str, str]] = []
        os.makedirs(self.outdir, exist_ok=True)

    def add_text(self, heading: str, text: str) -> None:
        self.blocks.append(("text", f"### {heading}\n\n```\n{text}\n```\n"))

    def add_note(self, text: str) -> None:
        self.blocks.append(("note", text + "\n"))

    def add_table(self, heading: str, rows: dict) -> None:
        md = [f"### {heading}\n", "| Parámetro | Valor |", "|---|---|"]
        for k, v in rows.items():
            md.append(f"| {k} | {v} |")
        self.blocks.append(("table", "\n".join(md) + "\n"))

    def add_figure(self, name: str, fig, caption: str | None = None) -> str:
        path = os.path.join(self.outdir, f"{name}.png")
        fig.savefig(path, dpi=130, bbox_inches="tight")
        rel = os.path.basename(path)
        cap = f"\n\n*{caption}*" if caption else ""
        self.blocks.append(("fig", f"![{name}]({rel}){cap}\n"))
        return path

    def write(self, filename: str = "README.md") -> str:
        path = os.path.join(self.outdir, filename)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(f"# {self.title}\n\n")
            fh.write(f"_Generado {time.strftime('%Y-%m-%d %H:%M')} por `sisela_signal`_\n\n")
            for _, md in self.blocks:
                fh.write(md + "\n")
        return path
