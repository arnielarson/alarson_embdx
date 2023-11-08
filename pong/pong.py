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

WIDTH, HEIGHT = 1200,600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong")


# throttle the FPS 
FPS = 60


# Some colors 
WHITE   = (255,255,255)
BLACK   = (0,0,0)

 
# Other params
PADDING = 5
RADIUS = 15


class Joystick:
 
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
  def get_dv(self, max_dv):

    dvx = int(-1*(self.Vx.value*2 -1)*max_dv)
    dvy = int((self.Vy.value*2 - 1)*max_dv)
    return (dvx,dvy)

class Ball:
  COLOR = WHITE
  vx=0
  vy=0
  vMAX = 14     # somewhat arbitrary, possibly can be adjusted during the game
  SCALE = 40    # arbitrary, used to implement the "pong" style momentum transfer
  PADDING = 10  #

  def __init__(self, x, y, radius):
    self.x = x
    self.y = y
    self.launch()
    self.radius = radius

  def launch(self, right=True):
    if right:
      self.vx = random.randint(3,6)
    else: 
      self.vx = random.randint(-6,-3)
    self.vy = random.randint(-6,6)
    

  def reset(self, right=True):
    self.x = WIDTH//2
    self.y = HEIGHT//2
    self.launch(right)

  def update(self):
    self.x += self.vx
    self.y += self.vy

    # Boundary collision checking
    # Left side, player 2 scores
    if self.x <= -self.PADDING:
      self.reset()
      return (0,1)
    # Right side, player 1 scores
    if self.x >= WIDTH + self.PADDING:
      self.reset()
      return (1,0)

    if self.y <= self.PADDING:
      self.vy = -self.vy
    elif self.y >= HEIGHT + self.PADDING:
      self.vy = -self.vy

    return None
  
  # Collisions - if ball is moving right and hits left side of paddle
  def check_collision(self, lpaddle, rpaddle):
    score = 0

    # check left side, (right paddle)
    if ( self.x <= rpaddle.x ) and (self.x + self.radius >= rpaddle.x ):
      if (self.y >= rpaddle.y) and (self.y <= rpaddle.y + rpaddle.height):
        # Left side collision, only implement when coming from left
        if self.vx > 0:
          self.vx= -self.vx
          # should be in range (-1,1)
          dy_ball = (self.y - (rpaddle.y + rpaddle.height//2))
          # ball is on upper part of paddle, dvy is negative, else positive
          dvy = self.SCALE * (dy_ball) / rpaddle.height//2        
          self.vy += dvy
          # boost speed
          if abs(self.vy) > self.vMAX:
            self.vx-=2

          # Now make sure that |vy| is not greater than |vMAX|
          if self.vy <= 0:
            self.vy = int(max(self.vy, -self.vMAX))
          else:
            self.vy = int(min(self.vy, self.vMAX))

    # Check right side, (left paddle)
    if ( self.x >= lpaddle.x + lpaddle.width ) and (self.x <= lpaddle.x + lpaddle.width + self.radius):
      if (self.y > lpaddle.y) and (self.y < lpaddle.y + lpaddle.height):
        # Right side collision, only implement when coming from right
        if self.vx < 0:
          self.vx= -self.vx
          # should be in range (-1,1)
          dy_ball = (self.y - (lpaddle.y + lpaddle.height//2))
          # ball is on upper part of paddle, dvy is negative, else positive
          dvy = self.SCALE * (dy_ball) / lpaddle.height//2        
          self.vy += dvy
          # boost speed
          if abs(self.vy) > self.vMAX:
            self.vx+=2

          # Now make sure that |vy| is not greater than |vMAX|
          if self.vy <= 0:
            self.vy = int(max(self.vy, -self.vMAX))
          else:
            self.vy = int(min(self.vy, self.vMAX))
    
    # check top and bottom
    for paddle in [lpaddle, rpaddle]:
      if (self.x >= paddle.x) and (self.x <= paddle.x+paddle.width):
        # vertical side
        if (self.y <= paddle.y) and (self.y >= paddle.y - self.radius):
          if self.vy == 0:
            self.vy = -2
          elif self.vy > 0:
            self.vy = -self.vy

        # bottom side
        if (self.y >= paddle.y + paddle.height) and (self.y <= paddle.y + paddle.height + self.radius):
          if self.vy == 0:
            self.vy = 2
          elif self.vy < 0:
            self.vy = -self.vy

    

  def draw(self, win):
    pygame.draw.circle(win, self.COLOR, (self.x, self.y), self.radius)
    #pygame.draw.rect(win, self.COLOR, (self.x, self.y, RADIUS, RADIUS))
  
class Paddle:
  COLOR = WHITE
  
  class TYPE(Enum):
    LEFT = 1
    RIGHT = 2


  def __init__(self, x, y, width, height, left = False):
    self.x = x
    self.y = y
    self.width = width
    self.height = height
    if left:
      self.type = self.TYPE.LEFT
    else: 
      self.type = self.TYPE.RIGHT
    
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

    # Implement mid-line boundaries
    if self.type == self.TYPE.RIGHT:
      if self.x < (WIDTH//2 + self.width//2):
        self.x = WIDTH//2 + self.width//2
    if self.type == self.TYPE.LEFT:
      if (self.x + self.width) > (WIDTH//2 - self.width//2):
        self.x = WIDTH//2 - self.width - self.width//2
  

  def draw(self, win):
    pygame.draw.rect(win, self.COLOR, (self.x, self.y, self.width, self.height))




"""
  State Manager Class

  Manages state updates and transitions, and rendering

  Note, this class has become a jumbled spaghetti code monster and if I cared
  about keeping and reusing this code baaase I'd refactor this monstrosity
"""
class State:

  # background render color
  bg = BLACK
  
  # global counter
  time_ctx = 0
  ball_ctx = 0
  btn_ctx = 0

  # Paddle max DX
  MAX_DV = 6  ## corresponds to 6 pixels per frame, ~ 350 pixels per second 

  # music / sound
  music = True
  sound = pygame.mixer.Sound("wav/smartguy.wav")
  
  # Fonts used for text displays
  BIG_FONT = pygame.font.SysFont("NotoSansMono-Bold",120)
  MEDIUM_FONT = pygame.font.SysFont("NotoSansMono-Bold",50)
  SMALL_FONT = pygame.font.SysFont("NotoSansMono-Bold",35)
  
  fps_text = None
  

  # Primary state
  class STATE(Enum):
    BEGIN = 1
    PLAY = 2
    WAIT = 3
    END = 4

  def __init__(self):
    self.lpaddle = Paddle(20, HEIGHT//2 - 100, 30, 200, True)
    self.rpaddle = Paddle(WIDTH - 20 - 30, HEIGHT//2 - 100, 30, 200, False)

    # This launches ball, but ball doesn't begin to move/render until PLAY state
    self.ball = Ball(WIDTH//2, HEIGHT//2, RADIUS)
    # Set direction of ball launch, initially to player 2
    self.launch_right = True
    self.joystick = Joystick()
    self.state = self.STATE.BEGIN
    self.score1 = 0
    self.score2 = 0
    self.animate = True
    self.practice = False
    self.seconds = time.time()
    

  """
    Manage Game States

    Begin -> Play <-> Wait (for new ball)
    Play -> End
  """
  def update_state(self, keys):
    
    # Always do
    self.btn_ctx +=1
    self.time_ctx +=1

    # Update/calculate FPS every 60 frames
    if self.time_ctx % 60 == 0:
      t2 = time.time()
      dt = t2 - self.seconds
      self.seconds = t2
      fps = int(60/dt)
      self.fps_text = self.SMALL_FONT.render(f"FPS: {fps}", 1, WHITE)


    # BEGIN State:
    if self.state == self.STATE.BEGIN:
      if (keys[pygame.K_p]):
        self.practice = True
      if self.practice:
        self.update_paddles(keys)
      if (keys[pygame.K_SPACE]):
        self.state = self.STATE.PLAY
        if self.music: 
          self.sound.play(loops=10)
        
        
    # toggle music
    if (keys[pygame.K_m] and self.btn_ctx>12):
      self.music = not self.music
      self.btn_ctx = 0
      if not self.music and (self.STATE.PLAY or self.STATE.WAIT):
        self.sound.stop()
      if self.music and (self.STATE.PLAY or self.STATE.WAIT):
        self.sound.play(loops=10)

    # PLAY state
    if self.state == self.STATE.PLAY:
      
      self.update_paddles(keys)
      
      # Update Score / State
      score = self.ball.update()
      if score:
        if score[0]:
          self.score1 += score[0]
          self.launch_right=True
        elif score[1]:
          self.score2 += score[1]
          self.launch_right=False
        
        if max(self.score1, self.score2) >= 10:
          self.state = self.STATE.END
          
        else: 
          self.state = self.STATE.WAIT
          self.ball_ctx=0
      else:
        self.ball.check_collision(self.lpaddle, self.rpaddle)

    # WAIT state, launch new ball towards previous scorer
    if self.state == self.STATE.WAIT:
      self.update_paddles(keys)
      self.ball_ctx+=1
      if self.ball_ctx % 60 == 0:
        self.state = self.STATE.PLAY
        self.ball.reset(self.launch_right)
      
    # END state
    if self.state == self.STATE.END:
      self.update_paddles(keys)
      if self.time_ctx % 40 == 0:
        self.animate = not self.animate
      if (keys[pygame.K_SPACE]):
        self.state = self.STATE.PLAY
        self.score0 = 0
        self.score1 = 0
        self.ball.reset()
        # reset game state...
        # self.reset_game()

  def update_paddles(self, keys):
    # Check user inputs
    (dx, dy) = self.joystick.get_dv(self.MAX_DV)
    self.rpaddle.update(dx,dy)

    # Check user inputs for player 1
    # Movement Keys - [w,a,s,d]
    if(keys[pygame.K_w]):   # UP
      self.lpaddle.update(0,-self.MAX_DV)
    if(keys[pygame.K_a]):   # LEFT
      self.lpaddle.update(-self.MAX_DV,0)
    if(keys[pygame.K_s]):   # DOWN 
      self.lpaddle.update(0,self.MAX_DV)
    if(keys[pygame.K_d]):   # RIGHT 
      self.lpaddle.update(self.MAX_DV,0)
  

  def draw(self, win):
    # Draw any canvas details
    win.fill(self.bg)
    
    # draw the fps
    if self.fps_text:
      win.blit(self.fps_text, (10, 50))
    # draw scores
    win.blit(self.SMALL_FONT.render(f"Player1    {self.score1}", 1, WHITE), (10, 10))
    win.blit(self.SMALL_FONT.render(f"Player2    {self.score2}", 1, WHITE), (WIDTH - 160, 10))
    
    if (self.state == self.STATE.BEGIN):
      win.blit(self.MEDIUM_FONT.render("Press [spacebar] to Start", 1, WHITE), (10, 90))
      
    # animate blinking blit for end game
    if (self.state == self.STATE.END):
      if self.animate:
        win.blit(self.BIG_FONT.render("GAME    OVER", 1, WHITE), (WIDTH//4,HEIGHT//3))
      win.blit(self.MEDIUM_FONT.render("Press [spacebar] to Play Again", 1, WHITE), (10, 90))
      
      
    
  
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
