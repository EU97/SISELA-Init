"""Pruebas de sisela_signal.live — sin hardware, con un puerto serie simulado."""

import sys
import types

import pytest

from sisela_signal import live


def test_parse_row_valid_and_invalid():
    assert live._parse_row("100,1.5,2.5", [1, 2]) == (100.0, [1.5, 2.5])
    assert live._parse_row("100,1.5,2.5", [1]) == (100.0, [1.5])
    # encabezado / comentario: no es una fila de datos
    assert live._parse_row("t_us,v", [1]) is None
    assert live._parse_row("# end n=10", [1]) is None
    # fila corta (índice de columna fuera de rango)
    assert live._parse_row("100,1.5", [1, 2]) is None
    # campo no numérico
    assert live._parse_row("100,abc", [1]) is None


class FakeSerial:
    """Sustituto mínimo de serial.Serial para pruebas: sirve líneas de una
    lista predefinida por readline(), ignora write()/flush()/dtr/rts."""

    def __init__(self, lines):
        self._lines = list(lines)
        self.dtr = True
        self.rts = True
        self.written = []

    def write(self, data):
        self.written.append(data)

    def flush(self):
        pass

    def reset_input_buffer(self):
        pass

    def readline(self):
        if self._lines:
            return (self._lines.pop(0) + "\n").encode()
        return b""

    def close(self):
        pass


def test_open_and_arm_detects_header(monkeypatch):
    lines = ["", "t_us,duty_pct,adc_raw", "0,0.0,0", "20000,5.0,120"]
    fake = FakeSerial(lines)
    monkeypatch.setattr(live, "serial", types.SimpleNamespace(Serial=lambda *a, **kw: fake))
    monkeypatch.setattr(live._time, "sleep", lambda *_a, **_kw: None)
    ser, header = live._open_and_arm("FAKE", 115200, "5", no_reset=True, header_timeout=2.0)
    assert header == ["t_us", "duty_pct", "adc_raw"]
    assert ser is fake
    # el menú "5" se envió como línea de comando
    assert any(b"5\r\n" in w for w in fake.written)


def test_open_and_arm_timeout_without_header(monkeypatch):
    fake = FakeSerial([])  # nunca llega un encabezado
    monkeypatch.setattr(live, "serial", types.SimpleNamespace(Serial=lambda *a, **kw: fake))
    monkeypatch.setattr(live._time, "sleep", lambda *_a, **_kw: None)
    # header_timeout pequeño pero > 0: con time.sleep parcheado a no-op,
    # el bucle de espera igual debe terminar por el límite de tiempo real.
    ser, header = live._open_and_arm("FAKE", 115200, None, no_reset=True, header_timeout=0.05)
    assert header is None


def test_live_plot_end_to_end(monkeypatch, tmp_path):
    """Simula una sesión completa: conectar, detectar encabezado, recibir N
    filas, graficarlas (con un FuncAnimation de prueba que corre síncrono) y
    guardar el CSV recibido — todo sin hardware ni ventana real."""
    rows = [f"{i*20000},{i % 100},{(i * 37) % 4096}" for i in range(1, 21)]
    lines = ["t_us,duty_pct,adc_raw"] + rows
    fake = FakeSerial(lines)

    monkeypatch.setattr(live, "serial", types.SimpleNamespace(Serial=lambda *a, **kw: fake))
    monkeypatch.setattr(live._time, "sleep", lambda *_a, **_kw: None)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    captured_update = {}

    class ImmediateAnimation:
        """Sustituto de FuncAnimation que corre `func` de inmediato varias
        veces en vez de depender de un bucle de eventos real (Agg no tiene)."""

        def __init__(self, fig, func, interval=100, cache_frame_data=False):
            captured_update["func"] = func
            for i in range(5):
                func(i)

    monkeypatch.setattr(live, "FuncAnimation", ImmediateAnimation)
    monkeypatch.setattr(plt, "show", lambda: None)

    out_csv = tmp_path / "live_capture.csv"
    live.live_plot(port="FAKE", menu="5", save=str(out_csv), no_reset=True)

    assert "func" in captured_update  # se llegó a construir la animación
    assert out_csv.exists()
    saved = out_csv.read_text().strip().splitlines()
    assert saved[0] == "t_us,duty_pct,adc_raw"
    assert len(saved) > 1  # se guardaron filas de datos reales
    plt.close("all")
