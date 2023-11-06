# Pong Example

Author: arnie.larson@gmail.com

## Introduction

I create a few quick versions of the classic Pong because 

- Explore the Pygame library and see how quickly I could spin up an interactive UI 
- Set up at least a little hardware, a simple joystick with a button 
- Ideally create something I could test out on with my kids

Coding up the game in Pygame endeded up being straightforward and fast.  I explored adding 
some basic animations and playing sounds.  Coding up the joystick was also pretty fast, 
using the GPIOZero library and MCP3008 ADC, two channels to a voltage divider and a single
button connected to a GPIO. 

## Results

- Game played well on a RPi 400 with Debian Bullseye
- Pong - 2 player game with one joystick is a facsimile of the arcade classic
- Basic Pong a POC looking into pygame
- Rainbow Pong added colors to the beat of the music from "Chipmunk at the Gaspump" by Laurie Berkner,
    this was fun but was a little jarring and harsh