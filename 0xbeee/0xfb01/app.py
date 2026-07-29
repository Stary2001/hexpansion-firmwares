import app
from machine import SPI, Pin
from events.input import Buttons, BUTTON_TYPES
from system.hexpansion.config import HexpansionConfig

class SX1262:
    def __init__(self, spi, ncs, busy):
        self.spi = spi
        self.ncs = ncs
        self.busy = busy

    def wait_not_busy(self):
        while self.busy() != 0:
            pass

    # Table 13-76: Status Bytes Definition
    class Mode:
        STBY_RC = 2
        STBY_XOSC = 3
        FS = 4
        RX = 5
        TX = 6
    class CommandStatus:
        DATA_AVAIL = 2
        TIMEOUT = 3
        ERROR = 4
        FAILURE = 5
        TX_DONE = 6

    def read_register(self, reg, data_len):
        txdata = bytearray(data_len + 3)
        txdata[0] = 0x1d
        txdata[1:2] = reg.to_bytes(2, 'big')
        rxdata = bytearray(len(txdata))

        self.ncs(0)
        self.spi.write_readinto(txdata, rxdata)
        self.ncs(1)

        # RX 3 status bytes then data
        return (rxdata[1], rxdata[3:])

    def write_register(self, reg, data):
        txdata = bytearray(len(data) + 3)
        txdata[0] = 0xd
        txdata[1:2] = reg.to_bytes(2, 'big')
        txdata[2:] = data

        rxdata = bytearray(len(txdata))

        self.ncs(0)
        self.spi.write_readinto(txdata, rxdata)
        self.ncs(1)

        return rxdata[1]


class LoraApp(app.App):
    def __init__(self, config=None):
        self.button_states = Buttons(self)

        if config is None:
            config = HexpansionConfig(2)

        self.n_reset = config.ls_pin[3]
        self.n_reset.init(mode=Pin.OUT)
        self.n_reset.value(1)

        self.irq = config.pin[0]
        self.irq.init(mode=Pin.IN)

        self.rxen = config.ls_pin[1]
        self.rxen.init(mode=Pin.OUT)
        self.rxen.value(0)

        self.busy = config.ls_pin[0]
        self.busy.init(mode=Pin.IN)

        self.ncs = config.ls_pin[2]
        self.ncs.init(mode=Pin.OUT)
        self.ncs.value(1)

        self.spi = SPI(1, baudrate=1 * 1000 * 1000,
            sck=config.pin[3], mosi=config.pin[1], miso=config.pin[2])

        self.sx = SX1262(self.spi, self.ncs, self.busy)

        self.testing = False

    def update(self, delta):
        if self.button_states.get(BUTTON_TYPES["CANCEL"]):
            self.button_states.clear()
            self.minimise()

        if self.button_states.get(BUTTON_TYPES["RIGHT"]):
            self.n_reset.value(0)
        else:
            self.n_reset.value(1)

        if self.button_states.get(BUTTON_TYPES["CONFIRM"]) and not self.testing:
            # Test - read 0x0320 version string (for 16 bytes, per radiolib)
            status, value = self.sx.read_register(0x320, 16)
            print((status >> 1) & 7, value)

            self.testing = True
        else:
            self.testing=False

    def draw(self, ctx):
        ctx.save()
        ctx.rgb(0, 0, 0).rectangle(-120, -120, 240, 240).fill()
        ctx.font_size = 16
        ctx.rgb(1,1,1)
        ctx.text_align = ctx.CENTER
        ctx.move_to(0, -50).text("B to reset")
        ctx.move_to(0, -35).text("C to test")
        if self.busy() == 1:
            ctx.move_to(0, 0).text("Busy")
        else:
            ctx.move_to(0, 0).text("Ready")
        ctx.restore()

__app_export__ = LoraApp
