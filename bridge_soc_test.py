#!/usr/bin/env python3
import time

import litex


UART_EV_TX = (1 << 0)
UART_EV_RX = (1 << 1)


def addr_lookup(wb, addr_type, reg_name):
    for entry in wb.items:
        if entry[0] == addr_type and entry[1] == reg_name:
            return int(entry[2], 16)
    raise KeyError(f'entry not found for {addr_type}:{reg_name}')


def uart_init(wb):
    wb.write(addr_lookup(wb, 'csr_register', 'uart_ev_pending'), UART_EV_TX | UART_EV_RX)


def display_wb_info(wb):
    # force the timer to update its register value
    wb.write(0x82003824, 1) # timer0_update_value
    # write a character to the uart bus
    wb.write(0x82001800, 67)
    wb.write(0x82001810, UART_EV_TX) # update uart_ev_pending

    for entry in wb.items:
        if entry[0] == 'csr_base':
            pass
        elif entry[0] == 'csr_register':
            res = wb.read(int(entry[2], 16), int(entry[3]))
            print("csr %30s  %10s  %8d  %s  =  %s" % 
                    (entry[1], entry[2], int(entry[3]), entry[4], res))
        elif entry[0] == 'constant':
            pass
        elif entry[0] == 'memory_region':
            print("mem %30s  %10s  %8d  %s" % (entry[1], entry[2], int(entry[3]), entry[4]))
            #res = wb.read(int(entry[3]), int(32))
            #print(" ".join("{:02x}".format(ord(c)) for c in str(res)))

def timer0_init(wb, timer_max):
    #timer_load = timer_max.to_bytes(4, 'little')
    timer_load = [ 0, 0, 255, 255 ]
    print(f'setting timer max to {timer_max} = {list(timer_load)}')
    wb.write(addr_lookup(wb, 'csr_register', 'timer0_load'), timer_load)
    wb.write(addr_lookup(wb, 'csr_register', 'timer0_reload'), timer_load)
    wb.write(addr_lookup(wb, 'csr_register', 'timer0_en'), 1)


def timer0_value(wb):
    wb.write(addr_lookup(wb, 'csr_register', 'timer0_update_value'), 1)
    value = wb.read(addr_lookup(wb, 'csr_register', 'timer0_value'))
    return value


def main():
    print("be sure you started the litex_server for bridging, e.g.")
    print("litex_server --uart --uart-port /dev/ttyUSB0  --uart-baudrate 1000000")
    print("---")

    wb = litex.RemoteClient()
    wb.open()
    print("resetting bus...")
    wb.write(0x82003000, 1) # reset the bus
    time.sleep(.100)
    print("configuring bus...")
    timer0_init(wb, 65536)
    #gpio_init()
    wb.write(0x82001004, 127) # gpio out
    uart_init(wb)

    display_wb_info(wb)
    print("loop starting...")

    i = 0
    dir = -1
    top = 100
    counter = 0
    while (1):
        bits = (1 << i) ^ 0xFF
        wb.write(0x82000000, bits)
        time.sleep(.150)
        if i == 7 or i == 0:
            dir *= -1
        i = i + dir

        if counter == top:
            counter = 0
            display_wb_info(wb)
        else:
            counter = counter + 1


if __name__ == "__main__":
    main()
