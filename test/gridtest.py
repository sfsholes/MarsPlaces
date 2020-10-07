import numpy as np

def createGrid(height, width):
    grid = np.empty((height,width), dtype=np.object)
    x = np.linspace(-180,180,width)
    y = np.linspace(-90,90,height)
    print('x', x)
    print('y', y)
    i, j = 0, 0
    while i < len(y):
        while j < len(x):
            grid[i,j] = (x[j], -y[i])
            print(i,j)
            j += 1
        j = 0
        i += 1
    print(grid)

createGrid(10,10)
