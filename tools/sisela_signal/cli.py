"""
cli — interfaz de línea de comandos de sisela_signal.

    python -m sisela_signal <comando> [opciones]

Comandos:
  capture       captura un bloque CSV del microcontrolador por puerto serie
  live          vista en vivo (gráfica actualizándose) del stream CSV por serie
  spectrum      FFT / PSD de una captura o export de osciloscopio
  alias         análisis de muestreo y aliasing (diagrama de plegado / barrido)
  filter        aplica un filtro digital y compara antes/después
  characterize  ENOB/SINAD/THD (modo adc) o rise/settling/overshoot (modo step)
  bode          diagrama de Bode a partir de capturas de barrido senoidal
  scope         inspecciona un CSV de osciloscopio (info + gráfica)
"""

from __future__ import annotations

import argparse
import sys

import numpy as np


def _load(path: str, fs: float | None, is_scope: bool):
    from .dataio import load_csv
    from .scopeio import load_scope_csv
    if is_scope:
        return load_scope_csv(path, fs_hint=fs)
    return load_csv(path, fs_nominal=fs)


def _maybe_show(args):
    import matplotlib.pyplot as plt
    if getattr(args, "save", None):
        plt.savefig(args.save, dpi=130, bbox_inches="tight")
        print(f"[guardado] {args.save}")
    else:
        plt.show()


# ---------------------------------------------------------------------------
def cmd_capture(args):
    from .capture import capture_serial
    from .dataio import save_npz
    cap = capture_serial(port=args.port, baud=args.baud, menu=args.menu,
                         seconds=args.seconds, max_lines=args.max_lines,
                         fs_nominal=args.fs, no_reset=args.no_reset)
    print(cap.summary())
    if args.out:
        if args.out.endswith(".npz"):
            save_npz(cap, args.out)
        else:
            with open(args.out, "w", encoding="utf-8") as fh:
                cols = list(cap.channels)
                fh.write("t_us," + ",".join(cols) + "\n")
                for i in range(cap.n):
                    fh.write(f"{cap.t[i]*1e6:.1f}," +
                             ",".join(f"{cap.channels[c][i]:g}" for c in cols) + "\n")
        print(f"[guardado] {args.out}")


def cmd_live(args):
    from .live import live_plot
    cols = [c.strip() for c in args.cols.split(",")] if args.cols else None
    live_plot(port=args.port, baud=args.baud, menu=args.menu, cols=cols,
              window=args.window, save=args.save_csv, no_reset=args.no_reset)


def cmd_spectrum(args):
    from .spectrum import amplitude_spectrum, welch_psd, plot_spectrum, plot_psd, tone_metrics
    cap = _load(args.file, args.fs, args.scope)
    x = cap.col(args.col)
    fs = args.fs or cap.fs
    print(cap.summary())
    print("-" * 40)
    if args.psd:
        f, p = welch_psd(x, fs)
        plot_psd(f, p, title=f"PSD — {args.file}")
    else:
        spec = amplitude_spectrum(x, fs, window=args.window)
        f0, a0 = spec.peak()
        print(f"pico espectral: {f0:.3f} Hz  (amplitud {a0:.4g})")
        plot_spectrum(spec, mark_harmonics=args.harmonics, title=f"Espectro — {args.file}")
    if args.metrics:
        m = tone_metrics(x, fs, full_scale=args.full_scale, window=args.window)
        print("-" * 40)
        print(m.report())
    _maybe_show(args)


def cmd_alias(args):
    from .sampling import alias_frequency, plot_folding, sweep_apparent
    from .spectrum import amplitude_spectrum
    if args.f is not None and args.fs:
        fa = alias_frequency(args.f, args.fs)
        zone = int(np.floor(args.f / (args.fs / 2)) + 1)
        print(f"f entrada = {args.f:g} Hz | Fs = {args.fs:g} Hz | Fs/2 = {args.fs/2:g} Hz")
        print(f"zona de Nyquist = {zone}")
        print(f"frecuencia aparente = {fa:g} Hz")
        if args.f > args.fs / 2:
            print("=> ALIASING: la señal viola el criterio de Nyquist.")
        plot_folding(max(args.f * 1.2, args.fs * 1.5), args.fs)
        _maybe_show(args)
        return
    if args.file:
        cap = _load(args.file, args.fs, args.scope)
        fs = args.fs or cap.fs
        spec = amplitude_spectrum(cap.col(args.col), fs, window=args.window)
        f0, _ = spec.peak()
        print(cap.summary())
        print(f"\npico aparente en el espectro: {f0:.3f} Hz  (Fs/2 = {fs/2:.1f} Hz)")
        if args.true_f:
            print(f"alias teórico de {args.true_f:g} Hz: {alias_frequency(args.true_f, fs):.3f} Hz")
        from .spectrum import plot_spectrum
        plot_spectrum(spec, title=f"Aliasing — {args.file}")
        _maybe_show(args)
        return
    print("Indica --f y --fs, o --file.", file=sys.stderr)
    sys.exit(2)


def cmd_filter(args):
    from .filters import apply, response, plot_compare, plot_bode
    cap = _load(args.file, args.fs, args.scope)
    fs = args.fs or cap.fs
    x = cap.col(args.col)
    kw = {}
    if args.cutoff:
        kw["cutoff"] = args.cutoff if len(args.cutoff) > 1 else args.cutoff[0]
    if args.n:
        kw["N"] = args.n
        kw["numtaps"] = args.n
    if args.alpha:
        kw["alpha"] = args.alpha
    if args.order:
        kw["order"] = args.order
    if args.btype:
        kw["btype"] = args.btype
    y = apply(args.kind, x, fs, **kw)
    print(cap.summary())
    plot_compare(cap.t if cap.t.size == len(x) else np.arange(len(x)) / fs, x, y, fs,
                 title=f"Filtro {args.kind} — {args.file}")
    if args.bode:
        rk = {"butter-lp": "butter", "butter-hp": "butter", "movavg": "movavg",
              "ma": "movavg", "ema": "ema", "fir": "fir"}.get(args.kind, args.kind)
        fr = response(rk, fs, **kw)
        print(f"\nfiltro: {fr.label}")
        fc = fr.cutoff_3db()
        if fc:
            print(f"f₋₃dB ≈ {fc:.2f} Hz")
        plot_bode(fr)
    _maybe_show(args)


def cmd_characterize(args):
    from .characterize import adc_metrics, step_metrics, plot_step, effective_resolution_bits
    from .characterize import allan_deviation
    cap = _load(args.file, args.fs, args.scope)
    fs = args.fs or cap.fs
    x = cap.col(args.col)
    print(cap.summary())
    print("=" * 40)
    if args.mode == "adc":
        m = adc_metrics(x, fs, full_scale=args.full_scale)
        print(m.report())
        if args.full_scale:
            er = effective_resolution_bits(x - np.mean(x) + 0.0, args.full_scale) \
                if np.std(x) > 0 else float("inf")
    elif args.mode == "step":
        t = cap.t if cap.t.size == len(x) else np.arange(len(x)) / fs
        m = step_metrics(t, x)
        print(m.report())
        plot_step(t, x, m)
        _maybe_show(args)
    elif args.mode == "allan":
        import matplotlib.pyplot as plt
        taus, adev = allan_deviation(x, fs)
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.loglog(taus, adev, "o-")
        ax.set_xlabel("τ (tiempo de promediado) [s]")
        ax.set_ylabel("Desviación de Allan")
        ax.set_title(f"Estabilidad — {args.file}")
        ax.grid(True, which="both", alpha=0.3)
        _maybe_show(args)
    else:
        print("modo desconocido", file=sys.stderr)
        sys.exit(2)


def cmd_bode(args):
    from .bode import BodeResult, point_from_capture, point_from_output, plot_bode
    from .dataio import load_csv
    res = BodeResult()
    for spec in args.point:
        # formato: freq:archivo.csv   ó   freq:archivo.csv:col_in:col_out
        parts = spec.split(":")
        f = float(parts[0])
        cap = load_csv(parts[1])
        if len(parts) >= 4:
            res.points.append(point_from_capture(cap.t, cap.col(parts[2]), cap.col(parts[3]), f))
        else:
            res.points.append(point_from_output(cap.t, cap.col(args.col), f, args.amp_in))
    res.points.sort(key=lambda p: p.f)
    for p in res.points:
        print(f"  {p.f:10.2f} Hz  |  {p.gain_db:+7.2f} dB  |  {p.phase_deg:+7.1f}°")
    fc = res.cutoff_3db()
    if fc:
        print(f"\nf₋₃dB ≈ {fc:.2f} Hz")
    ro = res.rolloff_db_per_decade()
    if ro:
        print(f"pendiente ≈ {ro:.1f} dB/década")
    plot_bode(res)
    _maybe_show(args)


def cmd_scope(args):
    from .scopeio import load_scope_csv
    import matplotlib.pyplot as plt
    cap = load_scope_csv(args.file, fs_hint=args.fs)
    print(cap.summary())
    fig, ax = plt.subplots(figsize=(9, 4))
    for name, y in cap.channels.items():
        ax.plot(cap.t, y, lw=0.8, label=name)
    ax.set_xlabel("Tiempo [s]"); ax.set_ylabel("Voltaje [V]")
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
    ax.set_title(f"Osciloscopio — {args.file}")
    _maybe_show(args)


# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sisela_signal", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common_in(sp, scope_default=False):
        sp.add_argument("--file", help="CSV de captura o de osciloscopio")
        sp.add_argument("--col", default=None, help="canal a analizar (nombre o índice)")
        sp.add_argument("--fs", type=float, default=None, help="Fs [Hz] (si no hay columna de tiempo)")
        sp.add_argument("--scope", action="store_true", default=scope_default,
                        help="tratar --file como export de osciloscopio")
        sp.add_argument("--save", help="guardar la gráfica en un archivo en vez de mostrarla")

    c = sub.add_parser("capture", help="captura CSV del MCU por serie")
    c.add_argument("--port"); c.add_argument("--baud", type=int, default=115200)
    c.add_argument("--menu", help="opción(es) de menú, p.ej. '6' o '6\\n30000'")
    c.add_argument("--seconds", type=float, default=5.0)
    c.add_argument("--max-lines", type=int, default=None, dest="max_lines")
    c.add_argument("--fs", type=float, default=None, help="Fs nominal solicitada")
    c.add_argument("--no-reset", action="store_true")
    c.add_argument("--out", help="archivo de salida (.csv o .npz)")
    c.set_defaults(func=cmd_capture)

    lv = sub.add_parser("live", help="vista en vivo del stream CSV por serie")
    lv.add_argument("--port"); lv.add_argument("--baud", type=int, default=115200)
    lv.add_argument("--menu", help="opción(es) de menú, p.ej. '5' o '9\\n2'")
    lv.add_argument("--cols", default=None,
                    help="columnas a graficar, separadas por coma (p.ej. 'duty_pct,adc_raw'); "
                         "por defecto, todas las del encabezado recibido")
    lv.add_argument("--window", type=float, default=20.0, help="ventana visible [s]")
    lv.add_argument("--save-csv", dest="save_csv", default=None,
                    help="además, guardar el CSV recibido en este archivo")
    lv.add_argument("--no-reset", action="store_true")
    lv.set_defaults(func=cmd_live)

    s = sub.add_parser("spectrum", help="FFT / PSD")
    common_in(s)
    s.add_argument("--window", default="hann")
    s.add_argument("--harmonics", type=int, default=0, help="marcar N armónicos")
    s.add_argument("--psd", action="store_true", help="PSD de Welch en vez de FFT")
    s.add_argument("--metrics", action="store_true", help="además, THD/SNR/SINAD/ENOB")
    s.add_argument("--full-scale", type=float, default=None, dest="full_scale")
    s.set_defaults(func=cmd_spectrum)

    a = sub.add_parser("alias", help="muestreo y aliasing")
    common_in(a)
    a.add_argument("--f", type=float, default=None, help="frecuencia de entrada [Hz]")
    a.add_argument("--true-f", type=float, default=None, dest="true_f",
                   help="frecuencia real del generador (para comparar con el pico medido)")
    a.add_argument("--window", default="hann")
    a.set_defaults(func=cmd_alias)

    f = sub.add_parser("filter", help="filtrado digital")
    common_in(f)
    f.add_argument("--kind", required=True,
                   choices=["movavg", "ma", "median", "ema", "butter", "fir"])
    f.add_argument("--cutoff", type=float, nargs="+", default=None, help="frecuencia(s) de corte [Hz]")
    f.add_argument("--n", type=int, default=None, help="N (media móvil / mediana / taps FIR)")
    f.add_argument("--alpha", type=float, default=None, help="alpha (EMA)")
    f.add_argument("--order", type=int, default=None, help="orden (Butterworth)")
    f.add_argument("--btype", default=None, choices=["low", "high", "bandpass", "bandstop"])
    f.add_argument("--bode", action="store_true", help="además, respuesta en frecuencia")
    f.set_defaults(func=cmd_filter)

    ch = sub.add_parser("characterize", help="ENOB/SINAD/THD o respuesta escalón")
    common_in(ch)
    ch.add_argument("--mode", default="adc", choices=["adc", "step", "allan"])
    ch.add_argument("--full-scale", type=float, default=None, dest="full_scale")
    ch.set_defaults(func=cmd_characterize)

    b = sub.add_parser("bode", help="Bode por barrido senoidal")
    b.add_argument("--point", action="append", default=[], required=True,
                   help="freq:archivo.csv[:col_in:col_out]  (repetir por frecuencia)")
    b.add_argument("--col", default=None, help="canal de salida si solo hay 1")
    b.add_argument("--amp-in", type=float, default=1.0, dest="amp_in",
                   help="amplitud de la sinusoide del generador")
    b.add_argument("--save")
    b.set_defaults(func=cmd_bode)

    sc = sub.add_parser("scope", help="inspecciona un CSV de osciloscopio")
    sc.add_argument("--file", required=True)
    sc.add_argument("--fs", type=float, default=None)
    sc.add_argument("--save")
    sc.set_defaults(func=cmd_scope)

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
