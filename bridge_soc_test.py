#!/usr/bin/env python3
import time

import litex

wb = litex.RemoteClient()
wb.open()

wb.read(0x82000000, 1)

i = 0
dir = -1
while (1):
    bits = (1 << i) ^ 0xFF
    wb.write(0x82000000, bits)
    time.sleep(.150)
    if i == 7 or i == 0:
        dir *= -1
    i = i + dir
    #print(f"{i} {dir}")
