#!/usr/bin/python
"""
  Looking into using pygame to play sounds

  arnie.larson@gmail.com+ ball.radius 

"""

import pygame
pygame.init()

# lets just try the default arguments
pygame.mixer.init()

WAV="wav/imperial_march.wav"
FPS=60


def main():
  run = True
  clock = pygame.time.Clock()
  s = pygame.mixer.Sound(WAV)
  s.play()
  while run:

    clock.tick(FPS)
    

    # process events
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        run = False
        break
    
    keys = pygame.key.get_pressed()
    if (keys[pygame.K_q]):
      run = False
      break 

if __name__=='__main__':
  main()                  