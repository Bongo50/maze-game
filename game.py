# setup imports
import pygame
import random
import pickle
from os import path
from levelGen import loadLevel as genLevel

# get image and sound folders
imgDir = path.join(path.dirname('__file__'), 'img')
sndDir = path.join(path.dirname('__file__'), 'snd')

# level size
LEVELSIZE = 14

# set dimensions
WIDTH = LEVELSIZE * 50 + 100
HEIGHT = LEVELSIZE * 50 + 100

FPS = 60 # controls the number of times the game will update every second

# define colours using RGB that will be used later
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# control schemes
ARROWKEYS = {
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "up": pygame.K_UP,
    "down": pygame.K_DOWN
}
WASD = {
    "left": pygame.K_a,
    "right": pygame.K_d,
    "up": pygame.K_w,
    "down": pygame.K_s
}
# set the initial control scheme to arrow keys
controls = ARROWKEYS
controlScheme = "arrow keys"

pygame.init() # required to use Pygame
screen = pygame.display.set_mode((WIDTH, HEIGHT)) # setup the screen with the dimensions
                                                  # defined earlier
pygame.display.set_caption("Maze Game") # set the titlebar of the window
clock = pygame.time.Clock() # setup Pygame's clock to ensure that the framerate is constant

# import required images
screencoverImg = pygame.image.load(path.join(imgDir, "cover.png")).convert()
titleImg = pygame.image.load(path.join(imgDir, "title.png")).convert()

# GameObject class
class GameObject(pygame.sprite.Sprite):
    def __init__(self, posX, posY, width, height, colour):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((width, height)) # set the object's dimensions
        self.image.fill(colour) # set the object's colour
        self.rect = self.image.get_rect() # the object's rect controls its hitbox and position
        # set the objects position to the given coordinates
        self.rect.centerx = posX
        self.rect.centery = posY

# MovingObject class
class MovingObject(GameObject):
    def __init__(self, posX, posY, width, height, colour, speed):
        GameObject.__init__(self, posX, posY, width, height, colour)
        self.speed = speed # the number of pixels the object can move each frame in each direction

# Player class
class Player(MovingObject):
    def __init__(self):
        MovingObject.__init__(self, 75  , 25  , 10   , 10    , RED   , 3    )
        #                           posX, posY, width, height, colour, speed
        self.levelOver = False # allows the player's collisions with the goal to be detected in the game loop
        self.gameOver = False # allows the player's collisions with the enemy to be detected in the game loop

    def update(self):
        global score
        keystates = pygame.key.get_pressed()
        if keystates[controls["left"]]: # movement left
            self.rect.x -= self.speed
        if keystates[controls["right"]]: # movement right
            self.rect.x += self.speed

        # stop the player moving horizontally off the screen
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH

        if keystates[controls["up"]]: # movement up
            self.rect.y -= self.speed
        if keystates[controls["down"]]: # movement down
            self.rect.y += self.speed

        # stop the player moving vertically off the screen
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT

        # collisions with walls
        collisions = pygame.sprite.groupcollide(playerGroup, walls, False, False) # check for collisions between walls and the player
        if len(collisions) > 0: # if there are any collisions...
            collisionObstacles = collisions[self] # ...extract the involved obstacles
            for obstacle in collisionObstacles: # iterate through each obstacle involved in a collision
                # check collisions with the player's...
                if self.rect.top < obstacle.rect.bottom and self.rect.top+4 > obstacle.rect.bottom and not (abs(self.rect.left - obstacle.rect.right) < 4 or abs(self.rect.right - obstacle.rect.left) < 4): # ...top
                    self.rect.top = obstacle.rect.bottom
                if self.rect.bottom > obstacle.rect.top and self.rect.bottom-4 < obstacle.rect.top and not (abs(self.rect.left - obstacle.rect.right) < 4 or abs(self.rect.right - obstacle.rect.left) < 4): # ...bottom
                    self.rect.bottom = obstacle.rect.top
                if self.rect.left < obstacle.rect.right and self.rect.left+4 > obstacle.rect.right and not (abs(self.rect.top - obstacle.rect.bottom) < 4 or abs(self.rect.bottom - obstacle.rect.top) < 4): # ...left
                    self.rect.left = obstacle.rect.right
                if self.rect.right > obstacle.rect.left and self.rect.right-4 < obstacle.rect.left and not (abs(self.rect.top - obstacle.rect.bottom) < 4 or abs(self.rect.bottom - obstacle.rect.top) < 4): # ...right
                    self.rect.right = obstacle.rect.left
        # collisions with collectables
        collisions = pygame.sprite.groupcollide(playerGroup, collectables, False, True) # check for collisions between collectables and the player
        if len(collisions) > 0: # if there are any collisions...
            collectable = collisions[self][0] # ...extract the involved collectable
            score += collectable.scoreToGive # increase the score
        # collisions with the goal
        collisions = pygame.sprite.groupcollide(playerGroup, goalGroup, False, False) # check for collisions between the goal and the player
        if len(collisions) > 0: # if there are any collisions...
            goal = collisions[self][0] # ...extract the involved goal
            score += goal.scoreToGive # increase the score
            self.levelOver = True # the level is over
        # collisions with the enemy
        collisions = pygame.sprite.groupcollide(playerGroup, enemyGroup, False, False) # check for collisions between the enemy and the player
        if len(collisions) > 0: # if there are any collisions...
            self.gameOver = True # ...the game is over

# Enemy class
class Enemy(MovingObject):
    def __init__(self):
        MovingObject.__init__(self, WIDTH-125, HEIGHT-50, 10   , 10    , BLUE  , 2 + (levelNumber - 1) * 0.2)
        #                           posX     , posY     , width, height, colour, speed
        # define the enemy's position, not using a rect, to allow for non-integer coordinates
        self.posX = float(WIDTH - 125)
        self.posY = float(HEIGHT - 50)

        self.pLastX = player.rect.x
        self.pLastY = player.rect.y

        # run the A* pathfinding algorithm before the main game starts so that self.path is not empty
        start = (self.rect.x // 50 - 1, self.rect.y // 50 -1) # the enemy's current position, as a maze array coordinate
        end = (player.rect.x // 50 - 1, player.rect.y // 50 - 1) # the player's current position, as a maze array coordinate
        self.path = AStar(start, end) # run the A* pathfinding algorithm

    def update(self):
        currentPos = (self.rect.x // 50 - 1, self.rect.y // 50 -1) # the enemy's current position, as a maze array coordinate
        if not(self.pLastX == player.rect.x and self.pLastY == player.rect.y): # check if the player has moved from their last position
            start = currentPos # where the A* pathfinding algorithm starts from (the enemy's position)
            end = (player.rect.x // 50 - 1, player.rect.y // 50 - 1) # the player's current position, as a maze array coordinate
            self.path = AStar(start, end) # run the A* pathfinding algorithm
        if self.path != False and len(self.path) > 0: # if there are still instructions in self.path to perform...
            tileToMoveTo = self.path[0] # ...set the first cell of path as the next to move to
            # get the coordinates of the cell in tileToMoveTo
            x = tileToMoveTo[0] * 50 + 75
            y = tileToMoveTo[1] * 50 + 75
        else: # otherwise, the enemy has reached the player's cell
            # get the player's coordinates
            x = player.rect.x
            y = player.rect.y
        # move towards the cell in tileToMoveTo, or the player
        if x < self.posX:
            self.posX -= self.speed
        elif x > self.posX:
            self.posX += self.speed
        if y < self.posY:
            self.posY -= self.speed
        elif y > self.posY:
            self.posY += self.speed
        if self.path != False and len(self.path) > 0: # check if there are any cells in self.path before (potentially) removing from it
            # check if the enemy has arrived at the cell it is traveling to
            if currentPos == (tileToMoveTo[0],tileToMoveTo[1]): # if it has
                self.path.remove(tileToMoveTo) # remove this from path
        # update the player's last position
        self.pLastX = player.rect.x
        self.pLastY = player.rect.y

        # update the rect with the new position:
        self.rect.x = self.posX
        self.rect.y = self.posY

        # stop the enemy moving horizontally off the screen
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > WIDTH:
            self.rect.right = WIDTH

        # stop the enemy moving vertically off the screen
        if self.rect.top < 0:
            self.rect.top = 0
        elif self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT

        # collisions with walls
        collisions = pygame.sprite.groupcollide(enemyGroup, walls, False, False) # check for collisions between walls and the enemy
        if len(collisions) > 0: # if there are any collisions...
            collisionObstacles = collisions[self] # ...extract the involved obstacles
            for obstacle in collisionObstacles: # iterate through each obstacle involved in a collision
                # check collisions with the enemy's...
                if self.rect.top < obstacle.rect.bottom and self.rect.top+4 > obstacle.rect.bottom and not (abs(self.rect.left - obstacle.rect.right) < 4 or abs(self.rect.right - obstacle.rect.left) < 4): # ...top
                    self.rect.top = obstacle.rect.bottom
                if self.rect.bottom > obstacle.rect.top and self.rect.bottom-4 < obstacle.rect.top and not (abs(self.rect.left - obstacle.rect.right) < 4 or abs(self.rect.right - obstacle.rect.left) < 4): # ...bottom
                    self.rect.bottom = obstacle.rect.top
                if self.rect.left < obstacle.rect.right and self.rect.left+4 > obstacle.rect.right and not (abs(self.rect.top - obstacle.rect.bottom) < 4 or abs(self.rect.bottom - obstacle.rect.top) < 4): # ...left
                    self.rect.left = obstacle.rect.right
                if self.rect.right > obstacle.rect.left and self.rect.right-4 < obstacle.rect.left and not (abs(self.rect.top - obstacle.rect.bottom) < 4 or abs(self.rect.bottom - obstacle.rect.top) < 4): # ...right
                    self.rect.right = obstacle.rect.left

# StationaryObject class
class StationaryObject(GameObject):
    def __init__(self, posX, posY, width, height, colour):
        GameObject.__init__(self, posX, posY, width, height, colour)

# Wall class - forms the walls of the level
class Wall(StationaryObject):
    def __init__(self, posX, posY, width, height):
        StationaryObject.__init__(self, posX+width/2, posY+height/2, width, height, RED    )
        #                               posX        , posY         , width, height, colour

# OuterWall class - forms the boundary of the level
class OuterWall(Wall):
    def __init__(self, posX, posY, width, height):
        Wall.__init__(self, posX, posY, width, height)

# InnerWall class - forms the interior of the level
class InnerWall(Wall):
    def __init__(self, posX, posY):
        Wall.__init__(self, posX, posY, 50, 50)

# Collectable class - give extra points
class Collectable(StationaryObject):
    def __init__(self, posX, posY):
        StationaryObject.__init__(self, posX+25, posY+25, 20, 20, YELLOW)
        self.scoreToGive = 20

# Goal class - the way levels are ended
class Goal(StationaryObject):
    def __init__(self):
        StationaryObject.__init__(self, WIDTH-125, HEIGHT-12.5, 50, 25, YELLOW)
        self.scoreToGive = 10

# Screencover class - for limited visibility
class Screencover(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(screencoverImg, (4000,4000)) # add the screencover's image to its sprite
        self.image.set_colorkey(WHITE) # make the colour white transparent
        self.rect = self.image.get_rect() # the rect controlls the hitbox and position
        # start the screencover on top of the player
        self.rect.centerx = player.rect.centerx
        self.rect.centery = player.rect.centery

    def update(self):
        # always be centred on the player
        self.rect.centerx = player.rect.centerx
        self.rect.centery = player.rect.centery

# heuristic for A* pathfinding algorithm - Manhattan distance
def h(node, end):
    return abs(node[0]-end[0]) + abs(node[1]-end[1])

# A* pathfinding algorithm
def AStar(start, end):
    dNodes = [] # array of discovered nodes
    gScore = {} # a dictionary of the distances from the start to any node
    fScore = {} # a dictionary of the estimated distance from the start to the end through any node
    dNodes.append(start) # the start node is already discovered
    # adds every cell of the maze to gScore and fScore with a value of infinity
    for x in range(0,len(LEVEL)):
        for y in range(0,len(LEVEL)):
            if LEVEL[y][x] == 1:
                gScore[(x,y)] = float("inf")
                fScore[(x,y)] = float("inf")
    # special cells outsie of the maze array
    gScore[(0,-1)] = float("inf")
    fScore[(0,-1)] = float("inf")
    gScore[(12,14)] = float("inf")
    fScore[(12,14)] = float("inf")
    # start
    gScore[start] = 0 # the start has a distance of 0 from the start
    fScore[start] = h(start, end) # this means that the estimated distance is just the heuristic

    cameFrom = {} # a dictionary of the shortest paths to reach any cell

    # main loop
    while len(dNodes) != 0:
        # get node with lowest fScore
        current = dNodes[0] # start with a node
        for node in dNodes: # loop through every other node
            if fScore[node] < fScore[current]: # if this node has a lower fScore than current...
                current = node # ...set it as current
        dNodes.remove(current) # remove the current node from dNodes - the algorithm shouldn't consider it further unless its rediscovered

        # output the final path, once it has been found
        if current == end: # if the end has been found
            path = [current] # start defining the path array with each node in the path
            while current in cameFrom.keys(): # keep looping until the whole route has been added to path
                current = cameFrom[current] # now consider the node that is used to reach the currently considered node
                path.append(current) # add it to path
            return list(reversed(path))[1:] # output the final path

        # extract the x and y of the currently considered cell for easy reference
        x = current[0]
        y = current[1]
        neighbours = [] # this array will contain the non-wall cells that connect to the current cell
        if x > 0 and y < LEVELSIZE: # if we're not on the left edge...
            if LEVEL[y][x-1] == 1: # ...and if the cell to the left is empty...
                neighbours.append((x-1,y)) # ...add it to neighbours
        if x < LEVELSIZE-1 and y < LEVELSIZE: # if we're not on the right edge...
            if LEVEL[y][x+1] == 1: # ...and if the cell to the right is empty...
                neighbours.append((x+1,y)) # ...add it to neighbours
        if y > 0 and x < LEVELSIZE: # if we're not on the top edge...
            if LEVEL[y-1][x] == 1: # ...and if the cell above is empty...
                neighbours.append((x,y-1)) # ...add it to neighbours
        if y < LEVELSIZE-1 and x < LEVELSIZE: # if we're not on the bottom edge...
            if LEVEL[y+1][x] == 1: # ...and if the cell bellow is empty...
                neighbours.append((x,y+1)) # ...add it to neighbours
        if y == 0 and x == 0:
            neighbours.append((x,y-1))
        if y == LEVELSIZE-1 and x == LEVELSIZE-2:
            neighbours.append((x,y+1))
        tgScore = gScore[current] + 1 # set the tentative gScore to the current cell's gScore + 1
        for n in neighbours: # loop through each neighbour
            if tgScore < gScore[n]: # if the tentative gScore is lower than the neigbour's actual current gScore...
                cameFrom[n] = current # ...a shorter path has been found so record it
                gScore[n] = tgScore # set the new gScore
                fScore[n] = tgScore + h(n, end) # calculate the new fScore
                if n not in dNodes: # if the neighbour hasn't been discovered yet...
                    dNodes.append(n) # ...it has now, so add it to dNodes.
    return False # this will only execute if a path has not been found

def text(surface, text, size, x, y, colour, centre=False):
    font = pygame.font.SysFont("Comic Sans MS", size)
    textSurface = font.render(text, True, colour)
    textRect = textSurface.get_rect()
    if centre:
        textRect.centerx = x
        textRect.top = y
    else:
        textRect.topleft = (x, y)
    surface.blit(textSurface, textRect)

def loadLevel():
    levelWalls = [] # this array will store all of the walls of the level

    # inner walls
    global LEVEL # LEVEL is global so that it can be accessed by other functions and methods
    LEVEL = genLevel(int(LEVELSIZE/2)) # produce the level's array via the functions in the separate Python file
    while AStar((0,0), (12,13)) == False: # check if the level is solvable
        LEVEL = genLevel(int(LEVELSIZE/2)) # produce the level's array via the functions in the separate Python file
    # start at (50, 50) to allow for the outer wall
    xPointer = 50
    yPointer = 50
    for layer in LEVEL: # for each layer of the maze...
        for cell in layer: # ...and for each cell in that layer...
            if cell == 0: # ...check if it is 0 (a wall). If so...
                levelWalls.append(InnerWall(xPointer, yPointer)) # ...instantiate an object of the obstacles class and add it to the levelWalls array
            xPointer += 50 # increment to the next position
        xPointer = 50 # go back to the start of the next layer
        yPointer += 50 # go to the next layer

    # outer walls
    levelWalls.append(OuterWall(0, 0, 50, (LEVELSIZE + 1) * 50))
    levelWalls.append(OuterWall(100, 0, (LEVELSIZE - 1) * 50, 50))
    levelWalls.append(OuterWall(WIDTH - 50, 0, 50, (LEVELSIZE + 1) * 50))
    levelWalls.append(OuterWall(WIDTH - 100, HEIGHT - 50, 100, 50))
    levelWalls.append(OuterWall(0, HEIGHT - 50, (LEVELSIZE - 1) * 50, 50))

    for wall in levelWalls: # add all of the walls to...
        allSprites.add(wall) # ..the allSprites group
        walls.add(wall) # ...the walls group

    # collectables
    collectablesArray = [] # this is the array that the collectables will be placed in
    while len(collectablesArray) < 5: # while there are less than 5 collectables succesfully placed...
        # ...pick the mazeArray coordinates of a random cell
        x = random.randint(0, LEVELSIZE-1)
        y = random.randint(0, LEVELSIZE-1)
        temp = Collectable(x*50,y*50) # instantiate a collectable at the actual coordinates of that cell
        collisions = pygame.sprite.spritecollide(temp, walls, False) # check if that collectable is touching a wall
        if len(collisions) == 0: # if it isn't...
            collectablesArray.append(temp) # add it to the array
    for collectable in collectablesArray: # add all of the collectables to...
        allSprites.add(collectable) # ...the allSprites group
        collectables.add(collectable) # ...the collectables group

def clearScreen():
    for sprite in allSprites: # for all sprites currently on the screen...
        sprite.kill() # ...kill that sprite


allSprites = pygame.sprite.Group() # setup a group so that I can update and draw all sprites, excluding the screen cover, at once
playerGroup = pygame.sprite.GroupSingle() # setup a group just to contain the player for collisions
enemyGroup = pygame.sprite.GroupSingle() # setup a group just to contain the enemy for collisions
walls = pygame.sprite.Group() # setup a group for walls for collisions
collectables = pygame.sprite.Group() # setup a group for collectables for collisions
goalGroup = pygame.sprite.GroupSingle() # setup a group just to contain the goal for collisions
coverGroup = pygame.sprite.GroupSingle() # setup a group just to contain the screencover to ensure it renders after everything else

player = Player() # instantiate an object of the Player class
allSprites.add(player) # add the player to the allSprites group
playerGroup.add(player) # add the player to the playerGroup group

screencover = Screencover() # instantiate an object of the Screencover class
coverGroup.add(screencover) # add the screencover to the allSprites group

global score
score = 0 # the player starts with no score
global levelNumber
levelNumber = 0 # this will be incremented to 1 when the first level initialises
running = True # the game starts running
inLevel = False # the game starts on the title screen, not in a level
levelNeedsInitialising = False # game starts on title screen so level does not need to be initialised
spaceDownPrev = False # whether the space key was pressed last frame - to start, it wasn't
while running:
    clock.tick(FPS) # limits the framerate to the value of FPS

    # check if the player closes the window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if levelNeedsInitialising:
        clearScreen()
        loadLevel()
        player = Player() # instantiate an object of the Player class
        allSprites.add(player) # add the player to the allSprites group
        playerGroup.add(player) # add the player to the playerGroup group
        enemy = Enemy() # instantiate an object of the Enemy class
        allSprites.add(enemy) # add the enemy to the allSprites group
        enemyGroup.add(enemy) # add the enemy to the enemyGroup group
        goal = Goal() # instantiate an object of the Goal class
        allSprites.add(goal) # add the goal to the allSprites group
        goalGroup.add(goal) # add the player to the goalGroup group
        levelNumber += 1 # increment the level counter
        levelNeedsInitialising = False # the level is now initialised

    allSprites.update() # runs every sprite's update method, except the screencover
    coverGroup.update() # runs the screencover's update method

    # detect if the level has been cleared
    if player.levelOver == True:
        levelNeedsInitialising = True

    # detect if the player has died
    if player.gameOver == True:
        HSFile = open('highscore.pickle', 'rb') # load the file with the last highscore for reading
        lastHS = pickle.load(HSFile) # load the highscore from the pickle file
        HSFile.close()
        if score > lastHS: # if current score is greater than current highscore...
            # ...new highscore!
            HSFile = open('highscore.pickle', 'wb') # load the file with the last highscore for writing
            pickle.dump(score, HSFile) # save the new highscore
            HSFile.close()

        score = 0 # the score resets to 0 upon death
        levelNumber = 0 # reset the level number upon death
        inLevel = False

    if inLevel:
        screen.fill(BLACK) # make the screen's background black
        allSprites.draw(screen) # draws all of the sprites to the screen, except the screencover
        coverGroup.draw(screen) # draws the screencover to the screen, only after all other sprites
        text(screen, "Score: {}".format(score), 22, WIDTH-120, 8, WHITE)
    else:
        screen.blit(titleImg, (0,0)) # add the title screen image to the screen
        # display local highscore
        HSFile = open('highscore.pickle', 'rb') # load the file with the highscore for reading
        HS = pickle.load(HSFile) # load the highscore from the pickle file
        HSFile.close() # close the highscore file
        text(screen, str(HS), 20, 425, 360, RED) # draw the highscore on the screen
        keystates = pygame.key.get_pressed() # get current keys
        if keystates[pygame.K_RETURN]: # check for the player pressing enter to start the game
            inLevel = True # start the level
            levelNeedsInitialising = True
        elif keystates[pygame.K_SPACE] and spaceDownPrev == False: # check for the player tapping space
            if controlScheme == "arrow keys": # if currently arrow keys...
                controls = WASD # ...switch to WASD
                controlScheme = "WASD"
            else: # otherwise,...
                controls = ARROWKEYS # switch to arrow keys
                controlScheme = "arrow keys"
        spaceDownPrev = keystates[pygame.K_SPACE] # for only detecting space once, not it being held
        text(screen, controlScheme, 18, 98, 685, RED, True) # draw to screen
    pygame.display.flip() # this means that the screen is drawn in advance of it being displayed

pygame.quit() # close the program when the game loop ends