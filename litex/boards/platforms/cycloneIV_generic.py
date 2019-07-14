# This file is Copyright (c) 2014-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2019 David Beck <beck.dac@live.com>
# License: BSD

from litex.build.generic_platform import *
from litex.build.altera import AlteraPlatform
from litex.build.altera.programmer import USBBlaster

# IOs ----------------------------------------------------------------------------------------------

_io = [
    ("clk50", 0, Pins("23"), IOStandard("3.3-V LVTTL")),            # pin 23

    ("user_led", 0, Pins("85"), IOStandard("3.3-V LVTTL")),         # status leds
    ("user_led", 1, Pins("84"), IOStandard("3.3-V LVTTL")),
    ("user_led", 2, Pins("83"), IOStandard("3.3-V LVTTL")),
    ("user_led", 3, Pins("77"), IOStandard("3.3-V LVTTL")),
    ("user_led", 4, Pins("76"), IOStandard("3.3-V LVTTL")),
    ("user_led", 5, Pins("75"), IOStandard("3.3-V LVTTL")),
    ("user_led", 6, Pins("74"), IOStandard("3.3-V LVTTL")),
    ("user_led", 7, Pins("73"), IOStandard("3.3-V LVTTL")),

    ("user_btn", 0, Pins("87"), IOStandard("3.3-V LVTTL")),              # pin 87, DEV_CLR
    ("user_btn", 1, Pins("86"), IOStandard("3.3-V LVTTL")),              # pin 86, DEV_OE

    ("serial", 0,
        Subsignal("tx", Pins("53"), IOStandard("3.3-V LVTTL")),    # 53
        Subsignal("rx", Pins("54"), IOStandard("3.3-V LVTTL"))     # 54
    ),
    ("serial", 1,
        Subsignal("tx", Pins("55"), IOStandard("3.3-V LVTTL")),    # 55
        Subsignal("rx", Pins("58"), IOStandard("3.3-V LVTTL"))     # 58
    ),

    #("spiflash", 0,
    #    Subsignal("cs_n", Pins("8"), IOStandard("LVCMOS33")),
    #    Subsignal("clk", Pins("12"), IOStandard("LVCMOS33")),
    #    Subsignal("mosi", Pins("6"), IOStandard("LVCMOS33")),
    #    Subsignal("miso", Pins("13"), IOStandard("LVCMOS33")), 
    #),

    ("i2c", 0,
        Subsignal("scl", Pins("133")),                             # 133
        Subsignal("sda", Pins("132")),                             # 132
        IOStandard("3.3-V LVTTL")
    ),

    ("gpio", 0,
        Pins("144 142 138 136",                                     # 144 142 138 136
            "143 141 137 135"),                                     # 143 141 137 135
        IOStandard("3.3-V LVTTL")
    ),
    ("gpio", 1,
        Pins("128 126 124 120",                                 # 128 126 124 120
            "129 127 125 121"),                                  # 129 127 125 121
        IOStandard("3.3-V LVTTL")
    )
]

# Platform -----------------------------------------------------------------------------------------

class Platform(AlteraPlatform):
    default_clk_name = "clk50"
    default_clk_period = 20

    #gateware_size = 0x28000
    
    #spiflash_model = "m25p16"
    #spiflash_read_dummy_bits = 8
    #spiflash_clock_div = 2
    #spiflash_total_size = int((16/8)*1024*1024) # 16Mbit
    #spiflash_page_size = 256
    #spiflash_sector_size = 0x10000

    def __init__(self):
        AlteraPlatform.__init__(self, "EP4CE6E22C8", _io)

    def create_programmer(self):
        return USBBlaster()
