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

    Polling design keypad.  I needed to use diodes (1N4001 because
    that's was what I had, though they are slow) to maintain reasonable 
    voltages as I pulsed the Columns as outputs.
    
    This implementation still suffers from ghosting but seems to be 
    workable for my indended projects.  I use 330 Ohm on the columns

    arnie.larson@gmail.com
"""
import sys, time
import threading
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
##
# Keymap has nRows, each row has nCols
KEY_MAP = [
  [False,False,False,False],
  [False,False,False,False],
  [False,False,False,False],
  [False,False,False,False],
  [False,False,False,False],
  [False,False,False,False]
]

COLS = [
  DigitalOutputDevice(pin=9, initial_value=False),
  DigitalOutputDevice(pin=10, initial_value=False),
  DigitalOutputDevice(pin=11, initial_value=False),
  DigitalOutputDevice(pin=12, initial_value=False)
]
ROWS = [
  DigitalInputDevice(pin=13, pull_up = False, bounce_time=None),
  DigitalInputDevice(pin=14, pull_up = False, bounce_time=None),
  DigitalInputDevice(pin=15, pull_up = False, bounce_time=None),
  DigitalInputDevice(pin=16, pull_up = False, bounce_time=None),
  DigitalInputDevice(pin=17, pull_up = False, bounce_time=None),
  DigitalInputDevice(pin=18, pull_up = False, bounce_time=None)
]

  
## 
# key scanner routine
##
def scan():

  # State change variable - could be used to fire events
  UPDATE=False
  while True:
    keys = '['
    for col in range(len(COLS)):
      COLS[col].on()
      for row in range(len(ROWS)):
        if ROWS[row].is_active:
          # state changed to active
          if not KEY_MAP[row][col]:
            UPDATE=True
          KEY_MAP[row][col]=True
          keys+=f" {CHARS[row][col]}"
        else:
          # state changed to inacive
          if KEY_MAP[row][col]:
            UPDATE=True
          KEY_MAP[row][col]=False
      COLS[col].off()
    keys += ']'
    
    
    if UPDATE:
      print(f"detected: {keys}")
      UPDATE=False
    # Set to run ~ 50 times / sec
    time.sleep(0.02)



def main(args):

  ## 
  # Initialization
  ##
 
  ## 
  # Main loop
  ##
  while True:
    # Start scannning routine
    T = threading.Thread(target=scan)
    T.daemon = True
    T.start()
    
    # Exit program
    line = input("Running keypad.py\n\nPress 'q' to quit\n\n")
    if line == 'q':
      break

if __name__=='__main__':
   main(sys.argv)