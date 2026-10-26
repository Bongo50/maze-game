import random

TILES = [
[[1,1], [1,0]],
[[1,1], [0,0]],
[[1,0], [1,0]],
[[1,0], [0,0]]]

def generateBlankMazeTiles(dimension):
    maze = [] # define the maze as a blank array
    for y in range(0, dimension): # loop through the length of the eventual maze...
        maze.append([]) # ...and add a blank array each iteration. These will be the rows of the maze
        for x in range(0, dimension): # loop through the length of the eventual maze again..
            maze[y].append(0) # ...and append a 0 to the current row each time.
                              # These 0s are placeholders for actual tiles
    return maze # return the finished blank maze tiles

def generateMazeTiles(wipMaze):
    for y in range(0, len(wipMaze)): # iterate through each row of the maze
        for x in range(0, len(wipMaze)): # iterate through each cell in that row
            if x == len(wipMaze) - 1 and y == len(wipMaze) - 1: # if the current cell is in the bottom right corner
                                                                # (where the exit will go)...
                wipMaze[y][x] = 0 # ...make sure it is tile 0
            else: # otherwise...
                ranNum = random.randint(0, 100) # ...pick a random integer between 0 and 100.
                if ranNum < 5: # if the random number is less than 5...
                    wipMaze[y][x] = 3 # ...add tile 3
                elif ranNum < 25: # otherwise, if less than 25...
                    wipMaze[y][x] = 2 # ...add tile 2
                elif ranNum < 50: # otherwise, if less than 50...
                    wipMaze[y][x] = 1 # ...add tile 1
                else: # otherwise...
                    wipMaze[y][x] = 0 # ...add tile 0
    return wipMaze # return the finished tiles

def generateMazeFromTiles(mazeTiles):
    maze = [] # define maze as a blank array. This array will hold the finished maze of individual cells
    tileDimension = len(mazeTiles)  # tileDimension is the dimension of the mazeTiles array
    for y in range(0, tileDimension): # iterate through the index of each row of tiles
        for layer in range(0, 2): # iterate through the index for each layer of cells
            maze.append([]) # append a blank array for each layer of cells in each row of tiles
            for x in range(0, tileDimension): # iterate through the index of each tile in the current row
                for cell in range(0, 2): # iterate through each cell in the current layer
                    maze[layer+y*2].append(TILES[mazeTiles[y][x]][layer][cell]) # append the value (1 or 0) for each of
                                                                                # these cells, taken from the TILES array
                    if maze[layer+y*2][cell+x*2] == 1 and maze[layer+y*2-1][cell+x*2] == 0 and maze[layer+y*2][cell+x*2-1] == 0:
                        # if the current cell is not a wall but the 2 adjacent cells to the left and top are walls...
                        ranNum = random.randint(0,1) # ...pick 1 or 0 randomly
                        if ranNum == 0: # on a 0 (50% of the time)...
                            maze[layer+y*2-1][cell+x*2] = 1 # ...replace the wall above with an empty cell
                        else: # otherwise (50% of the time)...
                            maze[layer+y*2][cell+x*2-1] = 1 # replace the wall to the right with an empty cell
    return maze # return the array containing the finished maze

# entry point from main program
def loadLevel(dimension):
    return generateMazeFromTiles(generateMazeTiles(generateBlankMazeTiles(dimension)))