#!/usr/bin/python
"""
    Simple program being used to examine the properties of GPIOs 
    being used as a button.  Examining bounce as well as delay time 
    to transfer a button click to an output pin (running an LED)

    For the MS keypad I'm using there are 4 columns and 6 rows.
    I wired up the columns and rows in order from GPIO 9 to GPIO18
    C1
    C2
    C3
    C4 = GPIO12
    R1
    R2
    R3
    R4
    R5 = GPIO17
    R6

    The DigitalIO classes from gpiozero have a default of no 
    software bounce implemented, so this code is basically to investigate
    and demonstrate bounce and to help measure bounce effects on the scope

    DigitalIO classes implement and expose event callbacks for:
    when_activated
    when_deactivated

    Tests:
    1. the MS keypad does not bounce in software and has a pretty smooth 
    tranistion on my scope (50 ns)
    2. the delay between pressing a button and toggling another GPIO was
    a little over 400 us, which I may need to investigate further
    3. A old school 3x4 telephone type keypad also didn't show much bounce, 
    but transitioned to 'On' much slower, 100x about 5us

    arnie.larson@gmail.com
"""
import sys, time
from gpiozero import DigitalOutputDevice, DigitalInputDevice

count = 0
led = 0

def pressed():
  global count
  global led
  global LED
  count +=1
  if led:
    led = 0
    LED.off()
  else:
    led = 1
    LED.on()
  print(f"Pressed {count}")

#def released():
#   print("Released")

# Setup Digital Button, "Enter Key" connecting C4 and R5
C4 = DigitalOutputDevice(pin=12, initial_value=True)
R5 = DigitalInputDevice(pin=17, pull_up = False, bounce_time=None)
LED = DigitalOutputDevice(pin=26, initial_value=False)

R5.when_activated = pressed
#R5.when_deactivated = released

def main(args):
  while True:
    line = input("Enter hex number: ")
    if line == 'quit':
        break

if __name__=='__main__':
   main(sys.argv)