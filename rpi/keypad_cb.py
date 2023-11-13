#!/usr/bin/python
"""
    Implementing a keypad from a salvaged MS keypad.
    On this device there are 4 columns and 6 rows.
    
    C1 = GPIO9 
    C2 = GPIO10
    C3 = GPIO11
    C4 = GPIO12
    R1 = GPIO13
    R2 = GPIO14
    R3 = GPIO15
    R4 = GPIO16
    R5 = GPIO17
    R6 = GPIO18

    This keypad seems to have some mechanical bounce mitigation, 
    so we will not deal with bounce here.

    The goal is to implement the keypad, the columns as outputs, the 
    rows as inputs, using callbacks.

    Implementation is quick and fun, but using callbacks with the 
    matrix of switches has several drawbacks vs a polling solution.
    These problems occur if you want to handle multiple presses 
    simultaneously.  If a row is pressed, a subsequent row press will
    not activate the event, since the gpio is already pulled high.
    If you press a second row key while one is being held, the scan
    will re-register the button press

    arnie.larson@gmail.com
"""
import sys, time
from threading import Lock
from gpiozero import DigitalOutputDevice, DigitalInputDevice


## 
# Setup
# Columns, Rows, Char map, global lock
##
CHARS = [
  ['NL', 'Calc','null','BP'],
  ['Clear', '/', '*', '-'],
  ['7', '8', '9', '+'],
  ['4', '5', '6', 'null'],
  ['1', '2', '3', 'Enter'],
  ['null', '0', '.', 'null'], 
]

COLS = [
  DigitalOutputDevice(pin=9, initial_value=True),
  DigitalOutputDevice(pin=10, initial_value=True),
  DigitalOutputDevice(pin=11, initial_value=True),
  DigitalOutputDevice(pin=12, initial_value=True)
]
ROWS = [
  DigitalInputDevice(pin=13, pull_up = False, bounce_time=None),
  DigitalInputDevice(pin=14, pull_up = False, bounce_time=None),
  DigitalInputDevice(pin=15, pull_up = False, bounce_time=None),
  DigitalInputDevice(pin=16, pull_up = False, bounce_time=None),
  DigitalInputDevice(pin=17, pull_up = False, bounce_time=None),
  DigitalInputDevice(pin=18, pull_up = False, bounce_time=None)
]

lock = Lock()

## 
# key scanner routine
##
def pressed():
  lock.acquire()
  
  for col in COLS:
    col.off()
  for col in range(len(COLS)):
    COLS[col].on()
    for row in range(len(ROWS)):
      if ROWS[row].is_active:
        print(f"key: '{CHARS[row][col]}' pressed")
    COLS[col].off()
  # reset state
  for col in COLS:
    col.on()

  lock.release()

  

def main(args):

  ## 
  # Initialization
  ##
  for row in ROWS:
    row.when_activated = pressed

  ## 
  # Main loop
  ##
  while True:
    line = input("Running keypad.py\n\nPress 'q' to quit\n\n")
    if line == 'q':
        break

if __name__=='__main__':
   main(sys.argv)