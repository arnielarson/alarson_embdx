#!/usr/bin/python
"""
  Rainbow Pong example game on Raspberry Pi using pygame, gpiozero

  Uses joystick to maneuver paddle
  Joystick is connected to a Raspberry Pi via SPI to an ADC and a GPIO as a button
  Incorporates a simple hacky state machine to handle game play 

  Goal, if there is one, is to hit as many balls as possible.. 
  
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
PURPLE  = (151,39,245)
PINK    = (228,39,245)
LIME    = (187,245,39)
TANG    = (245,169,39)
BLUE    = (108, 199, 245)
 
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
  score = 0

  # check left side
  if ( ball.x <= paddle.x ) and (ball.x + ball.radius >= paddle.x ):
    if (ball.y > paddle.y) and (ball.y < paddle.y + paddle.height):
      # Left side collision
      if ball.vx > 0:
        ball.vx= -ball.vx      
        score+=1
  
  # need right side now
  if ( ball.x >= paddle.x + paddle.width ) and (ball.x - ball.radius <= paddle.x + paddle.width):
    if (ball.y > paddle.y) and (ball.y < paddle.y + paddle.height):
      # Right side collision
      if ball.vx < 0:
        ball.vx= -ball.vx 
        score+=1

  # check top and bottom
  if (ball.x >= paddle.x) and (ball.x <= paddle.x+paddle.width):
    # vertical side
    if (ball.y <= paddle.y) and (ball.y >= paddle.y - ball.radius):
      if ball.vy == 0:
        ball.vy = -2
      elif ball.vy > 0:
        ball.vy = -ball.vy
      score+=1

    # bottom side
    if (ball.y >= paddle.y + paddle.height) and (ball.y <= paddle.y + paddle.height + ball.radius):
      if ball.vy == 0:
        ball.vy = 2
      elif ball.vy < 0:
        ball.vy = -ball.vy
      score+=1
    
  return score




"""
  State Manager Class

  Manages state transitions, background animations, object transitions, and rendering

  Adding any more *stuff* to the game would want to make states their own classes
"""
class State:
  # Spawn new balls
  MAX_BALLS = 5
  # background render color
  bg = BLACK
  # counters used for state transitions, animations, IO
  button_ctx = time_ctx = 0
  # sounds
  s1 = pygame.mixer.Sound("wav/chipmunk.wav")
  s2 = pygame.mixer.Sound("wav/chipmunkend.wav")
  # state parameter
  animate = True

  FPS_FONT = pygame.font.SysFont("DejaVuSansMono",35)
  GAME_OVER_FONT = pygame.font.SysFont("FreeMono",120)
  SCORE_FONT = pygame.font.SysFont("NotoSansMono-Bold",35)
  fps_text = None
  score = 0

  # Primary state
  class STATE(Enum):
    BEGIN = 1
    HYPE = 2
    MIDDLE = 3
    HYPE2 = 4
    END = 5
  # Secondary "hyper" state
  class HYPE(Enum):
    FIRST = 1
    SECOND = 2
    THIRD = 3
    FOURTH = 4
  # Secondary end state
  class END(Enum):
    FIRST = 1
    SECOND = 2

  def __init__(self, paddle, ball):
    self.paddle = paddle
    self.balls = []
    self.balls.append(ball)
    self.state = self.STATE.BEGIN
    self.seconds = time.time()

  # Spawn up to MAX_BALLS 
  def add_ball(self):
    if self.button_ctx > 20:
      self.button_ctx = 0
      x = WIDTH//2 + random.randint(-WIDTH//4, WIDTH//4)
      y = HEIGHT//2 + random.randint(-HEIGHT//4, HEIGHT//4)
      r = RADIUS + random.randint(0, RADIUS)  
      ball = Ball(x, y, r )
      if len(self.balls) >= self.MAX_BALLS:
        self.balls[random.randint(0,self.MAX_BALLS-1)]=ball
      else:
        self.balls.append(ball)  

  """
    Setting states deterministically, just playing around with animating the game play
    States:
      BEGIN     Black and White Pong like
      HYPE      Music, update color schemes
      MIDDLE    Calm
      FINISH    Music, more extreme color scheme updates
      END       Game play off (show or offer play again option to transition to BEGIN?)
  """
  def update_state(self, keys):
    self.button_ctx += 1
    self.time_ctx += 1
    


    for b in self.balls:
      b.update()
    for b in self.balls:
      self.score += check_collision(b, self.paddle)


    # Calculate FPS
    if self.time_ctx % 60 == 0:
      t2 = time.time()
      dt = t2 - self.seconds
      self.seconds = t2
      fps = int(60/dt)
      self.fps_text = self.FPS_FONT.render(f"FPS: {fps}", 1, WHITE)

    self.score_text = self.SCORE_FONT.render(f"Score: {self.score}", 1, WHITE)  

    # State transition to HYPE state
    if self.time_ctx == FPS*8:  ## after 8 seconds
      #self.s1.play(fade_ms=100)
      self.state = self.STATE.HYPE
      self.hype = self.HYPE.FIRST
      self.bg = PURPLE

    # State transition to MIDDLE state
    if self.time_ctx == FPS*34:
      self.state = self.STATE.MIDDLE
      self.bg = BLUE
    
    # State transition to HYPE2 state
    if self.time_ctx == FPS*42:
      #self.s2.play(fade_ms=100)
      self.state = self.STATE.HYPE2
      self.hype = self.HYPE.FIRST
      self.bg = PURPLE

    # Transition to END state
    if self.time_ctx == FPS*74:
      self.state = self.STATE.END
      self.end_state = self.END.FIRST
      self.animate = False
    
    # Toggle HYPE state
    if (self.state == self.STATE.HYPE) and (self.time_ctx % 14 == 0):    
      if self.hype == self.HYPE.FIRST:
        self.hype = self.HYPE.SECOND
        self.bg = PINK
      else:
        self.hype = self.HYPE.FIRST
        self.bg = PURPLE

    # Toggle HYPE2 state, (changes background colors)
    if (self.state == self.STATE.HYPE2) and (self.time_ctx % 8 == 0):    
      if self.hype == self.HYPE.FIRST:
        self.hype = self.HYPE.SECOND
        self.bg = PINK
      elif self.hype == self.HYPE.SECOND:
        self.hype = self.HYPE.THIRD
        self.bg = LIME
      elif self.hype == self.HYPE.THIRD:
        self.hype = self.HYPE.FOURTH
        self.bg = TANG
      else:
        self.hype = self.HYPE.FIRST
        self.bg = PURPLE

    # Toggle END state
    if (self.state == self.STATE.END) and (self.time_ctx % 30 == 0):    
      if self.end_state == self.END.FIRST:
        self.end_state = self.END.SECOND
      else:
        self.end_state = self.END.FIRST

    # Animate BG in middle
    if (self.state == self.STATE.MIDDLE) and (self.time_ctx % 3 == 0):
      # rotate through colors
      r = (self.bg[0]+1)%255
      g = (self.bg[1]+1)%255
      b = (self.bg[2]+1)%255
      self.bg = (r,g,b)
  
    # Animage BG in END
    if (self.state == self.STATE.END) and (self.time_ctx % 3 == 0):
      # rotate through colors
      r = (self.bg[0]+1)%255
      g = (self.bg[1]+2)%255
      b = (self.bg[2]+3)%255
      self.bg = (r,g,b)

    # Add a reset function on spacebar key
    # pygame.K_SPACE

    
    

  def draw(self, win):
    # Draw any canvas details
    win.fill(self.bg)
    
    # draw the fps
    if self.fps_text:
      win.blit(self.fps_text, (10, 10))

    win.blit(self.score_text, (WIDTH - 200, 10))
    # animate blinking blit for end game
    if (self.state == self.STATE.END) and (self.end_state == self.END.FIRST):
      win.blit(self.GAME_OVER_FONT.render("GAME OVER", 1, WHITE), (WIDTH//3,HEIGHT//3))
      
      
    
  
    # Draw game objects
    if self.animate:
      start_y, len_y = 20, 20
      while(start_y < HEIGHT):
        pygame.draw.line(win, WHITE, (WIDTH//2-5, start_y), (WIDTH//2-5, start_y + len_y), 10)
        start_y += 2*len_y
      
      for ball in self.balls:
        ball.draw(win)
      self.paddle.draw(win)

    pygame.display.update()

# main program control loop
def main():
  run = True
  clock = pygame.time.Clock()

  paddle = Paddle(WIDTH - 20, HEIGHT - 200, 30, 200)
  ball = Ball(WIDTH//2, HEIGHT//2, RADIUS)
  joystick = Joystick()
  state = State(paddle, ball)
  #balls = [ball]
  #objs = [paddle,ball]
  
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

    # Check user inputs
    (dx, dy) = joystick.get_dv()
    paddle.update(dx,dy)

    if joystick.get_pressed():
      state.add_ball()

    # Update game states and redraw
    state.update_state(keys)
    state.draw(WIN)



  pygame.quit()


if __name__=="__main__":
  main()
