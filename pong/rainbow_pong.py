#!/usr/bin/python
"""
  Rainbow Pong example game on Raspberry Pi using pygame, gpiozero

  Uses joystick to maneuver paddle
  Joystick is connected to a Raspberry Pi via SPI to an ADC and to a GPIO as a button
  Incorporates a simple state machine to handle game play 
  
  arnie.larson@gmail.com

"""

import pygame
import random
import math
from gpiozero import Button, MCP3008
pygame.init()

WIDTH, HEIGHT = 700,500
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hello Pong")


# throttle with FPS 
FPS = 60


# Some colors 
WHITE = (255,255,255)
BLACK = (0,0,0)

# Other params
PADDING = 5
RADIUS = 10


class Joystick:
  MAX_DV = 7  ## corresponds to 7 pixels per frame, ~ 400 pixels per second 
 
  ## Just needs to read the adc and convert to screen coordinates
  def __init__(self, button_gpio=22, chanvx=0, chanvy=1):
    self.Vx = MCP3008(channel = chanvx)
    self.Vy = MCP3008(channel = chanvy)
    self.button = Button(button_gpio)

  def get_pressed(self):
    return self.button.is_pressed
  
  """
    get_dv:     returns (dvx, dvy) in world coordinates, (x: left to right, y: top to bottom)

    Note, my configuration returns:
        value in x: 1 to 0 left to right => -MAX_DV to +MAX_DV
        value in y: 0 to 1 top to bottom => -MAX_DV to +MAX_DV
  """
  def get_dv(self):

    dvx = int(-1*(self.Vx.value*2 -1)*self.MAX_DV)
    dvy = int((self.Vy.value*2 - 1)*self.MAX_DV)
    return (dvx,dvy)

class Ball:
  COLOR = WHITE
  vx=0
  vy=0

  def __init__(self, x, y, radius):
    self.x = x
    self.y = y
    self.set_v()
    self.radius = radius

  def set_v(self):
    self.vx = random.randint(3,6)
    self.vy = random.randint(0,5)
    if random.randint(1,3)%3 == 0:
      self.vx*=1

  def reset(self):
    self.x = WIDTH//2
    self.y = HEIGHT//2
    self.set_v()

  def update(self):
    self.x += self.vx
    self.y += self.vy

    # Collision with boundary checking
    if self.x <=0:
      self.vx = -self.vx
    elif self.x >=WIDTH:
      self.vx = -self.vx
    if self.y <=0:
      self.vy = -self.vy
    elif self.y >=HEIGHT:
      self.vy = -self.vy

    if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
      self.reset()


  def draw(self, win):
    pygame.draw.circle(win, self.COLOR, (self.x, self.y), self.radius)
    
  
class Paddle:
  COLOR = WHITE

  def __init__(self, x, y, width, height, vx=0, vy=0):
    self.x = x
    self.y = y
    self.width = width
    self.height = height
    
  def update(self, dx, dy):
    
    # check for collision with boundaries, 
    if (dx > 0) and (self.x + self.width < WIDTH):
      self.x += dx
      if (self.x + self.width > WIDTH):
        self.x = WIDTH - self.width
    if (dx < 0) and (self.x > 0):
      self.x += dx
      if self.x < 0:
        self.x = 0
    if (dy > 0) and (self.y + self.height < HEIGHT):
      self.y += dy
      if (self.y + self.height > HEIGHT):
        self.y = HEIGHT - self.height
    if (dy < 0) and (self.y > 0):
      self.y += dy
      if (self.y < 0):
        self.y = 0

  def draw(self, win):
    pygame.draw.rect(win, self.COLOR, (self.x, self.y, self.width, self.height))

# Collisions - if ball is moving right and hits left side of paddle
def check_collision(ball, paddle):
  
  # check left side
  if ( ball.x <= paddle.x ) and (ball.x + ball.radius >= paddle.x ):
    if (ball.y > paddle.y) and (ball.y < paddle.y + paddle.height):
      # Left side collision
      if ball.vx > 0:
        ball.vx= -ball.vx      
  
  # need right side now
  if ( ball.x >= paddle.x + paddle.width ) and (ball.x - ball.radius <= paddle.x + paddle.width):
    if (ball.y > paddle.y) and (ball.y < paddle.y + paddle.height):
      # Right side collision
      if ball.vx < 0:
        ball.vx= -ball.vx 

  # check top and bottom
  if (ball.x >= paddle.x) and (ball.x <= paddle.x+paddle.width):
    # vertical side
    if (ball.y <= paddle.y) and (ball.y >= paddle.y - ball.radius):
      if ball.vy == 0:
        ball.vy = -2
      elif ball.vy > 0:
        ball.vy = -ball.vy
    # bottom side
    if (ball.y >= paddle.y + paddle.height) and (ball.y <= paddle.y + paddle.height + ball.radius):
      if ball.vy == 0:
        ball.vy = 2
      elif ball.vy < 0:
        ball.vy = -ball.vy



# Here update the canvas
def draw(win, objs):
  
  # Draw any canvas details
  win.fill(BLACK)
  # draw a mid line
  start_y, len_y = 20, 20
  while(start_y < HEIGHT):
    pygame.draw.line(win, WHITE, (WIDTH//2-5, start_y), (WIDTH//2-5, start_y + len_y), 10)
    start_y += 2*len_y
  
  # Draw game objects
  for obj in objs:
    obj.draw(win)

  pygame.display.update()


  # main program control loop
def main():
  run = True
  clock = pygame.time.Clock()

  paddle = Paddle(WIDTH - 20, HEIGHT - 200, 15, 150)
  ball = Ball(WIDTH//2, HEIGHT//2, RADIUS)
  joystick = Joystick()

  balls = [ball]
  objs = [paddle,ball]
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

    (dx, dy) = joystick.get_dv()
    paddle.update(dx,dy)
    for b in balls:
      b.update()
    for b in balls:
      check_collision(b, paddle)

    # check collisions
    # ball.left_col(paddle.x, paddle.y, paddle.height)

    ## Update canvas
    draw(WIN, objs)



  pygame.quit()


if __name__=="__main__":
  main()
