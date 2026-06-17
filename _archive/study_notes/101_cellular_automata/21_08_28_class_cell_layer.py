import maya.cmds as cmds
import copy
import random

rule = []

## make code into binary 257 => 0100000001
def set_rules(code):
  tmp = format(code, "010b")
  rule.clear()
  for i in tmp:
    rule.append(int(i))

class Cell:
    life = False;
    neighbors = 0;

    def __init__(self):
        self.life = False
        self.neighbors = 0

    def is_live(self):
        return self.life

    def reset_neighbors(self):
        self.neighbors = 0;

class Layer:
    num_lev = 10
    cols = 10
    rows = 10
    cells_prev = [] 
    cells_current = []

## init
###################################################################

    def __init__(self, cols, rows, level):
        self.cols = cols
        self.rows = rows
        self.num_lev = level
        self.cells_prev = [] 
        self.cells_current = []

        ## fill cells with empty cell
        for j in range(0, cols):
            tmp = []
            for i in range(0, rows):
                tmp.append(Cell())
            self.cells_current.append(copy.copy(tmp))
            self.cells_prev.append(copy.copy(tmp))

        ## set first layer with random life
        for col in range(0, self.cols):
            for row in range(0, self.rows):
                self.cells_prev[col][row].life = False
                # if(col == int(self.cols/2) and row == int(self.rows/2)):
                if(col == int(self.cols/2) and row >= int(self.rows/3) and row <= 2*int(self.rows/3)):
                    self.cells_prev[col][row].life = True
##init end
###################################################################

    def print_life(self):
        for col in range(0, self.cols):
            tmp = []
            for row in range(0, self.rows):
                tmp.append(self.cells_prev[col][row].life)
            print(tmp)

    def print_ne(self):
        for col in range(0, self.cols):
            tmp = []
            for row in range(0, self.rows):
                tmp.append(self.cells_current[col][row].neighbors)
            print(tmp)

###################################################################

    def update(self):
        self.cells_prev = copy.copy(self.cells_current)

    def set_neighbor(self, col, row):
        if(self.cells_prev[col -1][row].is_live()):
            self.cells_current[col][row].neighbors += 1
        if(self.cells_prev[col + 1][row].is_live()):
            self.cells_current[col][row].neighbors += 1
        if(self.cells_prev[col][row - 1].is_live()):
            self.cells_current[col][row].neighbors += 1
        if(self.cells_prev[col][row + 1].is_live()):
            self.cells_current[col][row].neighbors += 1

    def set_neighbors(self):
        for col in range(1,self.cols):
            for row in range(1,self.rows):
                self.cells_current[col][row].reset_neighbors()           
        for col in range(1,self.cols-1):
            for row in range(1,self.rows-1):
                self.set_neighbor(col, row)


    def set_life(self, col, row):
      if(self.cells_current[col][row].neighbors == 4 and self.cells_prev[col][row].is_live()):
          self.cells_current[col][row].life = rule[0]
      elif(self.cells_current[col][row].neighbors == 4 and not self.cells_prev[col][row].is_live()):
          self.cells_current[col][row].life = rule[1]
      elif(self.cells_current[col][row].neighbors == 3 and self.cells_prev[col][row].is_live()):
          self.cells_current[col][row].life = rule[2]
      elif(self.cells_current[col][row].neighbors == 3 and not self.cells_prev[col][row].is_live()):
          self.cells_current[col][row].life = rule[3]
      elif(self.cells_current[col][row].neighbors == 2 and self.cells_prev[col][row].is_live()):
          self.cells_current[col][row].life = rule[4]
      elif(self.cells_current[col][row].neighbors == 2 and not self.cells_prev[col][row].is_live()):
          self.cells_current[col][row].life = rule[5]
      elif(self.cells_current[col][row].neighbors == 1 and self.cells_prev[col][row].is_live()):
          self.cells_current[col][row].life = rule[6]
      elif(self.cells_current[col][row].neighbors == 1 and not self.cells_prev[col][row].is_live()):
          self.cells_current[col][row].life = rule[7]
      elif(self.cells_current[col][row].neighbors == 0 and self.cells_prev[col][row].is_live()):
          self.cells_current[col][row].life = rule[8]
      elif(self.cells_current[col][row].neighbors == 0 and not self.cells_prev[col][row].is_live()):
          self.cells_current[col][row].life = rule[9]

    def set_lives(self):
        for col in range(0, self.cols):
            for row in range(0, self.rows):
                self.set_life(col, row)

    def draw_cube(self, col, row, lev):
        cube = cmds.polyCube(height = 1, width = 1, depth = 1)
        cmds.move(col, lev, row, cube[0])

    def draw_cells(self, lev):
        for col in range(0, self.cols):
            for row in range(0, self.rows):
                if(self.cells_current[col][row].is_live()):
                    self.draw_cube(col, row, lev)

    def __del__(self):
        self.cells_prev.clear()
        self.cells_current.clear()