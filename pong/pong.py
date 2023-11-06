#!/usr/bin/python
"""
  Pong example game on Raspberry Pi using pygame, gpiozero

  Right player uses joystick to maneuver paddle
  Left player uses [w, a, s, d] to maneouver paddle

  Joystick is connected to a Raspberry Pi via SPI to an ADC and a GPIO as a button
  
  arnie.larson@gmail.com

"""

import pygame
import random
import time
from enum import Enum
from gpiozero import Button, MCP3008
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1400,800
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rainbow Pong")


# throttle the FPS 
FPS = 60


# Some colors 
WHITE   = (255,255,255)
BLACK   = (0,0,0)

 
# Other params
PADDING = 5
RADIUS = 15


class Joystick:
  MAX_DV = 6  ## corresponds to 6 pixels per frame, ~ 350 pixels per second 
 
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
    #pygame.draw.rect(win, self.COLOR, (self.x, self.y, RADIUS, RADIUS))
  
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
def check_collision(ball, lpaddle, rpaddle):
  score = 0

  # check left side, (right paddle)
  if ( ball.x <= rpaddle.x ) and (ball.x + ball.radius >= rpaddle.x ):
    if (ball.y > rpaddle.y) and (ball.y < rpaddle.y + rpaddle.height):
      # Left side collision
      if ball.vx > 0:
        ball.vx= -ball.vx      
  
  # right side, (left paddle)
  if ( ball.x >= lpaddle.x + lpaddle.width ) and (ball.x - ball.radius <= lpaddle.x + lpaddle.width):
    if (ball.y > lpaddle.y) and (ball.y < lpaddle.y + lpaddle.height):
      # Right side collision
      if ball.vx < 0:
        ball.vx= -ball.vx 

  # check top and bottom
  for paddle in [lpaddle, rpaddle]:
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


"""
  State Manager Class

  Manages state updates and transitions, and rendering
"""
class State:

  # background render color
  bg = BLACK
  
  # global counter
  time_ctx = 0
  
  
  # music
  music = music_btn_ctx = 0

  # Fonts used for text displays
  FPS_FONT = pygame.font.SysFont("NotoSansMono-Bold",35)
  BIG_FONT = pygame.font.SysFont("FreeMono",120)
  #GAME_OVER_FONT = pygame.font.SysFont("FreeMono",120)
  MEDIUM_FONT = pygame.font.SysFont("FreeMono",80)
  SCORE_FONT = pygame.font.SysFont("NotoSansMono-Bold",35)
  
  fps_text = None
  

  # Primary state
  class STATE(Enum):
    BEGIN = 1
    PLAY = 2
    BALL = 3
    END = 4

  def __init__(self):
    self.lpaddle = Paddle(20, HEIGHT//2 + 100, 30, 200)
    self.rpaddle = Paddle(WIDTH - 20 - 30, HEIGHT//2 + 100, 30, 200)
    self.ball = Ball(WIDTH//2, HEIGHT//2, RADIUS)
    self.joystick = Joystick()
    self.state = self.STATE.BEGIN
    self.score1 = 0
    self.score2 = 0
    self.seconds = time.time()

  """
    Manage Game
  """
  def update_state(self, keys):
    
    # Always do
    self.music_btn_ctx +=1
    self.time_ctx +=1

    # Update/calculate FPS every 60 frames
    if self.time_ctx % 60 == 0:
      t2 = time.time()
      dt = t2 - self.seconds
      self.seconds = t2
      fps = int(60/dt)
      self.fps_text = self.FPS_FONT.render(f"FPS: {fps}", 1, WHITE)


    # if init:
    if self.state == self.STATE.BEGIN:
      if (keys[pygame.K_SPACE]):
        self.state = self.STATE.PLAY
        # start music here potentially
      if (keys[pygame.K_m] and self.music_btn_ctx>12):
        self.music = not self.music
        self.music_btn_ctx = 0
      
      
    if self.state == self.STATE.PLAY:
      
      # Check user inputs
      (dx, dy) = self.joystick.get_dv()
      self.rpaddle.update(dx,dy)

      # check score/ state
      self.ball.update()
      check_collision(self.ball, self.lpaddle, self.rpaddle)

    
    # Add a reset function on spacebar key
    # pygame.K_SPACE
    if self.state == self.STATE.END:
      if (keys[pygame.K_space]):
        self.state = self.STATE.PLAY
        # reset game state...
        # self.reset_game()

    
    

  def draw(self, win):
    # Draw any canvas details
    win.fill(self.bg)
    
    # draw the fps
    if self.fps_text:
      win.blit(self.fps_text, (10, 50))
    # draw scores
    win.blit(self.SCORE_FONT.render(f"Player 1: {self.score1}", 1, WHITE), (10, 10))
    win.blit(self.SCORE_FONT.render(f"Player 2: {self.score2}", 1, WHITE), (WIDTH - 160, 10))
    
    # animate blinking blit for end game
    #if (self.state == self.STATE.END) and (self.end_state == self.END.FIRST):
    if (self.state == self.STATE.END):
      win.blit(self.BIG_FONT.render("GAME OVER", 1, WHITE), (WIDTH//3,HEIGHT//3))
      win.blit(self.MEDIUM_FONT.render("Press [spacebar] to Play Again", 1, WHITE), (WIDTH//3, (2*HEIGHT)//3))
      
      
    
  
    # Draw game objects
    
    start_y, len_y = 20, 20
    while(start_y < HEIGHT):
      pygame.draw.line(win, WHITE, (WIDTH//2-5, start_y), (WIDTH//2-5, start_y + len_y), 10)
      start_y += 2*len_y
      
    if self.state == self.STATE.PLAY:
        self.ball.draw(win)
        
    self.lpaddle.draw(win)
    self.rpaddle.draw(win)

    pygame.display.update()

# main program control loop
def main():
  run = True
  clock = pygame.time.Clock()
  state = State()
  
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

    # Update game states and redraw
    state.update_state(keys)
    state.draw(WIN)

  pygame.quit()


if __name__=="__main__":
  main()
