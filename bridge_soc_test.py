#!/usr/bin/env python3
import time

import litex


UART_EV_TX = (1 << 0)
UART_EV_RX = (1 << 1)

uart = None


def addr_lookup(wb, addr_type, reg_name):
    for entry in wb.items:
        if entry[0] == addr_type and entry[1] == reg_name:
            return int(entry[2], 16)
    raise KeyError(f'entry not found for {addr_type}:{reg_name}')


class UART:
    def __init__(self, wb):
        self.wb = wb
        self.rxtx_addr = addr_lookup(wb, 'csr_register', 'uart_rxtx')
        self.txfull_addr = addr_lookup(wb, 'csr_register', 'uart_txfull')
        self.rxempty_addr = addr_lookup(wb, 'csr_register', 'uart_rxempty')
        self.ev_status_addr = addr_lookup(wb, 'csr_register', 'uart_ev_status')
        self.ev_pend_addr = addr_lookup(wb, 'csr_register', 'uart_ev_pending')
        self.ev_enable = addr_lookup(wb, 'csr_register', 'uart_ev_enable')
       
        wb.write(self.ev_pend_addr, UART_EV_TX | UART_EV_RX)

    def _rx_empty(self):
        return self.wb.read(self.rxempty_addr, 1)

    def _tx_full(self):
        return self.wb.read(self.txfull_addr, 1)
    
    def read(self, block=True):
        if block:
            while _rx_empty(self):
                pass
            c = self.wb.read(self.rxtx_addr, 1)
            _ev_pending(self, UART_EV_RX)
            return c
        else:
            if not _rx_empty(self):
                c = self.wb.read(self.rxtx_addr, 1)
                _ev_pending(self, UART_EV_RX)
                return c
            else:
                pass
        return None

    def write(self, c, block=True):
        if block:
            while self._tx_full():
                pass
            self.wb.write(self.rxtx_addr, c)
            _ev_pending(self, UART_EV_TX)
            return 1
        else:
            if not self._tx_full():
                self.wb.write(self.rxtx_addr, c)
                _ev_pending(self, UART_EV_TX)
                return 1
            else:
                pass
        return None


class TIMER:
    def __init__(self, wb, num, enable=False, top=0):
        self.wb = wb
        self.num = num
        self.top = 0
        self.width = 4
        self.top_bytes = [ 0, 0, 0, 0 ]
        self.en_addr = addr_lookup(wb, 'csr_register', f'timer{num}_en')
        self.load_addr = addr_lookup(wb, 'csr_register', f'timer{num}_load')
        self.reload_addr = addr_lookup(wb, 'csr_register', f'timer{num}_reload')
        self.update_value_addr = addr_lookup(wb, 'csr_register', f'timer{num}_update_value')
        self.value_addr = addr_lookup(wb, 'csr_register', f'timer{num}_value')
        self.ev_status_addr = addr_lookup(wb, 'csr_register', f'timer{num}_ev_status')
        self.ev_pending_addr = addr_lookup(wb, 'csr_register', f'timer{num}_ev_pending')
        self.ev_enable_addr = addr_lookup(wb, 'csr_register', f'timer{num}_ev_enable')
        if enable:
            self.enable(top)
        else:
            self.disable()

    def enable(self, top):
        self.en = True
        self.top = top
        self.top_bytes = list(top.to_bytes(self.width, 'big'))
        self.wb.write(self.load_addr, self.top_bytes)
        self.wb.write(self.reload_addr, self.top_bytes)
        self.wb.write(self.en_addr, 1)

    def disable(self):
        self.en = False
        self.wb.write(self.en_addr, 0)

    def _update_value(self):
        self.wb.write(self.update_value_addr, 1)

    def value(self):
        self._update_value()
        return self.wb.read(self.value_addr, self.width)


class GPIO:
    def __init__(self, wb, addr_type, reg_name, size=1):
        self.wb = wb
        self.addr = addr_lookup(wb, addr_type, reg_name)
        self.size = size

    def read(self):
        return self.wb.read(self.addr, self.size)

    def write(self, data):
        return self.wb.write(self.addr, data)


class BUS:
    def __init__(self, wb):
        self.wb = wb
        self.timer0 = TIMER(wb, 0)
        self.uart = UART(wb)
        self.cas = GPIO(wb, 'csr_register', 'cas_leds_out')
        self.gpio_in = GPIO(wb, 'csr_register', 'gpio_in')
        self.gpio_out = GPIO(wb, 'csr_register', 'gpio_out')


def display_wb_info(bus):
    # force the timer to update its register value so it
    # is up to date-ish when it is printed below
    bus.timer0._update_value()

    # write a character to the uart bus
    ret = bus.uart.write('A', block=False)
    if ret is None:
        print("UART tx buffer is full")

    # iterate over bus elements and show info
    for entry in bus.wb.items:
        if entry[0] == 'csr_base':
            pass
        elif entry[0] == 'csr_register':
            res = bus.wb.read(int(entry[2], 16), int(entry[3]))
            print("csr %30s  %10s  %8d  %s  =  %s" % 
                    (entry[1], entry[2], int(entry[3]), entry[4], res))
        elif entry[0] == 'constant':
            pass
        elif entry[0] == 'memory_region':
            print("mem %30s  %10s  %8d  %s" % (entry[1], entry[2], int(entry[3]), entry[4]))
            #res = bus.wb.read(int(entry[3]), int(32))
            #print(" ".join("{:02x}".format(ord(c)) for c in str(res)))

def main():
    print("be sure you started the litex_server for bridging, e.g.")
    print("litex_server --uart --uart-port /dev/ttyUSB0  --uart-baudrate 1000000")
    print("---")

    wb = litex.RemoteClient()
    wb.open()

    print("configuring bus...")
    bus = BUS(wb)
    bus.timer0.enable(65536*255)

    display_wb_info(bus)
    print("loop starting...")

    i = 0
    dir = -1
    top = 100
    counter = 0
    while (1):
        bits = (1 << i) ^ 0xFF
        bus.cas.write(bits)
        #wb.write(0x82000000, bits)
        time.sleep(.150)
        if i == 7 or i == 0:
            dir *= -1
        i = i + dir

        if counter == top:
            counter = 0
            display_wb_info(bus)
        else:
            counter = counter + 1


if __name__ == "__main__":
    main()
