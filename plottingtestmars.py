import numpy as np
import matplotlib.pyplot as plt

# read gridded MOLA topo data
topo = np.loadtxt('megt90n000cb.txt',dtype='float',unpack=True)
dpp = 4 # four degrees per pixel for this gridded dataset
topo = np.roll(topo.reshape(dpp*180,dpp*360),dpp*180,axis=1)

# create array of lat and lon values, spaced to be centered on quarter degree pixels
dx = 1./dpp # grid spacing
dx2 = dx/2.
xx = np.arange(-180+dx2,180,dx)
yy = np.arange(90.-dx2,-90,-dx)
lon,lat = np.meshgrid(xx,yy,indexing='xy')
elon = lon+180.

plt.imshow(topo)
plt.show()
