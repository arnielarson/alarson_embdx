#!/usr/bin/python
"""
  On a Raspberry Pi 400 
  Simple example of enabling the GPIOs to get input from a joystick.  

  Shows how to initialize and read values
  Reads the analog sensor values (x,y) position from a MPC3008 ADC
  This is connected via SPI to the RPi
  GPIO 22 is used as a button, pull up, so press connects to ground

  arnie.larson@gmail.com

"""
from gpiozero import MCP3008, Button
import time


def main():
  # initialize GPIOs and MCP3008 ADC
  # run loop, (use pygame just because it has some nice control/io features
  # Read data once per second..
  run = True
  n = 0
  
  b = Button(22)
  vx = MCP3008(channel = 0)
  vy = MCP3008(channel = 1)

  print("Hello")
  while(run):
    if n > 8:
      run = False
    
    # Note, in my configuration, Vx goes 1 to 0 left to right
    #                            Vy goes 0 to 1 top to bottom
    print("Value of Vx: {}".format(vx.value))
    print("Value of Vy: {}".format(vy.value))
    print("Value of button pressed: {}".format(b.is_pressed))
    time.sleep(1)
    n+=1
  print("Goodbye")
  

if __name__=="__main__":
  main()