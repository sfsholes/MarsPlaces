import numpy as np
import matplotlib.pyplot as plt


mola = plt.imread('Mars_MGS_colorhillshade_mola_1024.jpg')
BBox = (-180, 180, -90, 90)

fig, ax = plt.subplots()
ax.set_xlim(BBox[0],BBox[1])
ax.set_ylim(BBox[2],BBox[3])
ax.imshow(mola, zorder=0, extent = BBox, aspect= 'equal')

plt.show()
