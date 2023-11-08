#!/usr/bin/python
"""
    Simple program to show sending data to a serial shift register

    Sets 3 GPIOs as Digital pins to communicate with 74HC595

    arnie.larson@gmail.com
"""

import sys, time
from gpiozero import DigitalOutputDevice

latch = DigitalOutputDevice(pin=16, initial_value=True)
ser = DigitalOutputDevice(pin=20, initial_value=True)
clk = DigitalOutputDevice(pin=21, initial_value=True)

# clear pin did not clear the device data for me
clr = DigitalOutputDevice(pin=12, initial_value=True)

BITS = [128,64,32,16,8,4,2,1]

# sends 8 bits of data, first bit is MSB, last is LSB
def send(data):
    latch.off()
    for bit in BITS:
        clk.off()
        val = data & bit
        if val:
            ser.on()
        else:
            ser.off()
        clk.on()
    latch.on()

def clear():
    clr.off()
    time.sleep(0.5)
    clr.on()


def main(args):
  while True:
    line = input("Enter hex number: ")
    if line == 'quit':
        break
    if line == 'clear':
        clear()
        continue
    try:
      data = int(line, 16)
      print(f"Data: {data}")
      send(data)
    except Exception as e:
      print(f"Exception: {e}")
  print("Goodbye")




if __name__=='__main__':
    main(sys.argv)