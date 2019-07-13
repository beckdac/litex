#!/usr/bin/env python3

# This file is Copyright (c) 2015-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2019 Dave Beck <beck.dac@live.com>
# License: BSD

import argparse

from migen import *

from gateware import cas
from gateware import spi_flash

from litex.boards.platforms import cycloneIV_generic

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from litex.soc.cores.uart import UARTWishboneBridge


# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys_ps = ClockDomain()
        self.clock_domains.cd_por = ClockDomain(reset_less=True)

        # # #

        self.cd_sys.clk.attr.add("keep")
        self.cd_sys_ps.clk.attr.add("keep")
        self.cd_por.clk.attr.add("keep")

        # power on rst
        rst_n = Signal()
        self.sync.por += rst_n.eq(1)
        self.comb += [
            self.cd_por.clk.eq(self.cd_sys.clk),
            self.cd_sys.rst.eq(~rst_n),
            self.cd_sys_ps.rst.eq(~rst_n)
        ]

        # sys clk
        clk50 = platform.request("clk50")
        self.comb += self.cd_sys.clk.eq(clk50)
        self.specials += \
            Instance("ALTPLL",
                p_BANDWIDTH_TYPE="AUTO",
                p_CLK0_DIVIDE_BY=1,
                p_CLK0_DUTY_CYCLE=50,
                p_CLK0_MULTIPLY_BY=1,
                p_CLK0_PHASE_SHIFT="-3000",
                p_COMPENSATE_CLOCK="CLK0",
                p_INCLK0_INPUT_FREQUENCY=20000,
                p_OPERATION_MODE="ZERO_DELAY_BUFFER",
                i_INCLK=clk50,
                o_CLK=self.cd_sys_ps.clk,
                i_ARESET=~rst_n,
                i_CLKENA=0x3f,
                i_EXTCLKENA=0xf,
                i_FBIN=1,
                i_PFDENA=1,
                i_PLLENA=1,
            )

# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCCore):
    csr_peripherals = (
        #"spiflash",
        "cas",
    )
    csr_map_update(SoCCore.csr_map, csr_peripherals)
    
    mem_map = {
        #"spiflash": 0x20000000,  # (default shadow @0xa0000000)
    }
    mem_map.update(SoCCore.mem_map)


    def __init__(self, platform, sys_clk_freq=int(50e6), **kwargs):
        assert sys_clk_freq == int(50e6)

        if 'integrated_rom_size' not in kwargs:
            kwargs['integrated_rom_size'] = 0
        if 'integrated_sram_size' not in kwargs:
            kwargs['integrated_sram_size'] = 0

        clk_freq = sys_clk_freq

        self.submodules.crg = _CRG(platform)

        # no londer neaded?
        #platform = cycloneIV_generic.Platform()

        # spiflash not implemented
        #kwargs['cpu_reset_address']=self.mem_map["spiflash"]+platform.gateware_size
        SoCCore.__init__(self, platform, clk_freq, **kwargs)
        
        self.submodules.cas = cas.ControlAndStatus(platform, clk_freq)

        # SPI flash peripheral
        #self.submodules.spiflash = spi_flash.SpiFlashSingle(
        #    platform.request("spiflash"),
        #    dummy=platform.spiflash_read_dummy_bits,
        #    div=platform.spiflash_clock_div)
        #self.add_constant("SPIFLASH_PAGE_SIZE", platform.spiflash_page_size)
        #self.add_constant("SPIFLASH_SECTOR_SIZE", platform.spiflash_sector_size)
        #self.register_mem("spiflash", self.mem_map["spiflash"],
        #    self.spiflash.bus, size=platform.spiflash_total_size)

        #bios_size = 0x8000
        #self.add_constant("ROM_DISABLE", 1)
        #self.add_memory_region("rom", kwargs['cpu_reset_address'], bios_size)
        #self.flash_boot_address = self.mem_map["spiflash"]+platform.gateware_size+bios_size

        # We don't have a DRAM, so use the remaining SPI flash for user
        # program.
        #self.add_memory_region("user_flash", self.flash_boot_address,
            # Leave a grace area- possible one-by-off bug in add_memory_region?
            # Possible fix: addr < origin + length - 1
            #platform.spiflash_total_size - (self.flash_boot_address - self.mem_map["spiflash"]) - 0x100)

        
class BridgeSoC(BaseSoC):
    csr_peripherals = (
        "analyzer",
        "io",
    )
    csr_map_update(BaseSoC.csr_map, csr_peripherals)
    
    def __init__(self, platform=cycloneIV_generic.Platform(), *args, **kwargs):
        kwargs['cpu_type'] = None
        BaseSoC.__init__(self, platform, *args, with_uart=False, **kwargs)
        self.add_cpu_or_bridge(
                #UARTWishboneBridge(platform.request("serial", 0), self.clk_freq, baudrate=115200)
                UARTWishboneBridge(platform.request("serial", 0), self.clk_freq, baudrate=1000000)
            )
        self.add_wb_master(self.cpu_or_bridge.wishbone)




# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on Waveshare Cyclone IV board")
    builder_args(parser)
    soc_core_args(parser)
    args = parser.parse_args()

    soc = BridgeSoC(**soc_core_argdict(args))
    builder = Builder(soc, **builder_argdict(args))
    builder.build()


if __name__ == "__main__":
    main()
