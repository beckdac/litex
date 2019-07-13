#!/usr/bin/env python3
import time

import litex


def display_wb_info(wb):
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


def main():
    print("be sure you started the litex_server for bridging, e.g.")
    print("litex_server --uart --uart-port /dev/ttyUSB0  --uart-baudrate 115200")
    print("---")

    wb = litex.RemoteClient()
    wb.open()
    display_wb_info(wb)

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
