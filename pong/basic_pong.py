#!/usr/bin/python
"""
  Basic "Hellow World" pong example using pygame

  Began with a pretty good tutorial by "Tech with Tim"
  youtube.com/watch?v=vVGTZlnnX3U
  
  Implements key commands
  [a], [d], [w], [s] for paddle movement
  [UP], [DOWN], [LEFT], [RIGHT] to give paddle a const velocity

  arnie.larson@gmail.com

"""

import pygame
import random
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


#
# Game objects, update(), draw()
# 
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

    # Collision checking
    if self.x <=0:
      self.vx = -self.vx
    elif self.x >=WIDTH:
      self.reset()
    if self.y <=0:
      self.vy = -self.vy
    elif self.y >=HEIGHT:
      self.vy = -self.vy

  # checks for left side colission with paddle 
  def left_col(self, x, y, height):
    pass

  def draw(self, win):
    pygame.draw.circle(win, self.COLOR, (self.x, self.y), self.radius)
    
  
class Paddle:
  COLOR = WHITE
  DX = DY = 1
  VX = 2; VY = 4
  DX_MAX = 5
  ivxp = ivxn = ivyp = ivyn = 0

  def __init__(self, x, y, width, height, vx=0, vy=0):
    self.x = x
    self.y = y
    self.width = width
    self.height = height
    self.vx = vx
    self.vy = vy


  # Idea here, update x y coords, then keep a velocity param as well, but only process ~ once per second
  def update(self, keys):

    # Movement Keys
    if(keys[pygame.K_w]): self.y -= self.VY  # UP, recall, y goes from 0 to HEIGHT top to bottom
    if(keys[pygame.K_a]): self.x -= self.VX  # LEFT
    if(keys[pygame.K_s]): self.y += self.VY  # DOWN
    if(keys[pygame.K_d]): self.x += self.VX  # RIGHT

    # Velocity movement keys
    # Since a key press will be registered every processing frame, I want to implement
    # a delay for the delta V commands
    if(keys[pygame.K_UP]): 
      if self.ivyn > FPS//2:
        self.vy -= self.DY if self.vy>-self.DX_MAX else 0
        self.ivyn = 0
    if(keys[pygame.K_DOWN]): 
      if self.ivyp > FPS//2:
        self.vy += self.DY if self.vy<self.DX_MAX else 0
        self.ivyp = 0
    if(keys[pygame.K_LEFT]): 
      if self.ivxn > FPS//2:
        self.vx -= self.DX if self.vx<self.DX_MAX else 0
        self.ivxn = 0
    if(keys[pygame.K_RIGHT]): 
      if self.ivxp > FPS//2:
        self.vx += self.DX if self.vy<self.DX_MAX else 0
        self.ivxp = 0
    self.x += self.vx
    self.y += self.vy
    self.ivyn+=1
    self.ivyp+=1
    self.ivxn+=1
    self.ivxp+=1

  def draw(self, win):
    pygame.draw.rect(win, self.COLOR, (self.x, self.y, self.width, self.height))

# Collisions - if ball is moving right and hits left side of paddle
def check_collision(ball, paddle):
  
  # check left side
  if ( ball.x - ball.radius//2 < paddle.x) and (ball.x + ball.radius//2 > paddle.x ):
    if (ball.y - ball.radius//2 > paddle.y - PADDING) and (ball.y + ball.radius//2 < paddle.y + paddle.height + PADDING):
      # Left side collision
      if ball.vx > 0:
        ball.vx= -ball.vx + paddle.vx # implement infinite mass momentum transfer
      else:
        ball.vx = ball.vx + paddle.vx

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
  objs = [paddle,ball]
  while run:
    clock.tick(FPS)

    # check for events
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        run = False
        break

    
    keys = pygame.key.get_pressed()
    paddle.update(keys)
    ball.update()
    check_collision(ball, paddle)

    # check collisions
    ball.left_col(paddle.x, paddle.y, paddle.height)

    ## Update canvas
    draw(WIN, objs)



  pygame.quit()


if __name__=="__main__":
  main()
