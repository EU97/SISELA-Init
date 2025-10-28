# Minimal SSD1306 I2C driver (128x64)
# Works with MicroPython on ESP32. Uses framebuf for drawing primitives.
try:
    import framebuf
except ImportError:
    framebuf = None  # Only runs on MicroPython


class SSD1306_I2C:
    def __init__(self, width, height, i2c, addr=0x3C):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.buffer = bytearray(self.width * self.height // 8)
        if framebuf:
            self.fb = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        else:
            self.fb = None
        self._init_display()

    # Low-level helpers
    def _write_cmd(self, cmd):
        # Control byte 0x00 for commands
        self.i2c.writeto(self.addr, bytes([0x00, cmd]))

    def _write_data(self, buf):
        # Control byte 0x40 for data
        self.i2c.writeto(self.addr, bytes([0x40]) + buf)

    def _init_display(self):
        # Init sequence (typical)
        for cmd in (
            0xAE,       # Display OFF
            0xD5, 0x80, # Set display clock div
            0xA8, self.height - 1,  # Set multiplex
            0xD3, 0x00, # Display offset
            0x40,       # Start line at 0
            0x8D, 0x14, # Charge pump ON
            0x20, 0x00, # Memory mode Horizontal
            0xA1,       # Segment remap
            0xC8,       # COM scan dec
            0xDA, 0x12, # COM pins config (for 128x64)
            0x81, 0xCF, # Contrast
            0xD9, 0xF1, # Pre-charge
            0xDB, 0x40, # VCOM detect
            0xA4,       # Resume to RAM content
            0xA6,       # Normal display
            0xAF        # Display ON
        ):
            self._write_cmd(cmd)
        self.fill(0)
        self.show()

    # High-level API compatible with framebuf
    def fill(self, color):
        for i in range(len(self.buffer)):
            self.buffer[i] = 0xFF if color else 0x00

    def pixel(self, x, y, color=1):
        if self.fb:
            self.fb.pixel(x, y, color)

    def text(self, s, x, y, color=1):
        if self.fb:
            self.fb.text(s, x, y, color)

    def line(self, x0, y0, x1, y1, color=1):
        if self.fb:
            self.fb.line(x0, y0, x1, y1, color)

    def rect(self, x, y, w, h, color=1):
        if self.fb:
            self.fb.rect(x, y, w, h, color)

    def fill_rect(self, x, y, w, h, color=1):
        if self.fb:
            self.fb.fill_rect(x, y, w, h, color)

    def show(self):
        # Update full screen (pages)
        self._write_cmd(0x21)  # Column addr
        self._write_cmd(0)     # start
        self._write_cmd(self.width - 1)  # end
        self._write_cmd(0x22)  # Page addr
        self._write_cmd(0)
        self._write_cmd((self.height // 8) - 1)
        # Send in chunks to avoid large I2C transfers
        chunk = 16
        for i in range(0, len(self.buffer), chunk):
            self._write_data(self.buffer[i:i+chunk])
