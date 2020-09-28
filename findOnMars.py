import geocoder
import numpy  as np
import pandas as pd
import os
import math
from scipy import spatial

#### GET INPUT ###
cwd = os.path.dirname(os.path.realpath(__file__))
#point = Point(43.214408, -76.712236)  #Red Creek
point = (-5.353904, 137.770154)  #Gale Crater
point = (41.49008, -71.312796)

### CALCULATE DISTANCE ###
def cartesian(latitude, longitude, elevation=0):
    # Convert to radians
    latitude *= math.pi / 180
    if longitude < 0:
        longitude = 360 + longitude 
    longitude *= math.pi / 180

    #R = 3,389.5 #km
    R = 6371
    X = R * math.cos(latitude) * math.cos(longitude)
    Y = R * math.cos(latitude) * math.sin(longitude)
    Z = R * math.sin(latitude)

    return (X, Y, Z)

### DEAL WITH PANDAS ARRAY ###
MARS_LOC = pd.read_csv(os.path.join(cwd, "MarsPlacesApproved.csv"))
    # Here are the column labels
    # 0: Feature_Name
    # 1: Diameter
    # 2: Center_Latitude
    # 3: Center_Longitude
    # 4: Northern_Latitude
    # 5: Southern_Latitude
    # 6: Eastern_Longitude
    # 7: Western_Longitude
    # 8: Feauture_Type
    # 9: Quad
    # 10: Origin
MARS_LOC.info()

def isInPolygon(row):
    #return point.within(row[11])
    if (point[0]>row[5] and point[0]<row[4] and point[1]<row[6] and point[1]>row[7]):
        return True
    else:
        return False

MARS_LOC['Within'] = MARS_LOC.apply(isInPolygon, axis=1)

LOCATED_DF = MARS_LOC.loc[MARS_LOC['Within'] == True]
print(LOCATED_DF)

places = []
for index, row in MARS_LOC.iterrows():
    coordinates = [row['Center_Latitude'], row['Center_Longitude']]
    cartesian_coord = cartesian(*coordinates)
    places.append(cartesian_coord)

tree = spatial.KDTree(places)

def find_nearest_loc(lat, lon):
    cartesian_coord = cartesian(lat, lon)
    closest = tree.query([cartesian_coord], p = 2)
    index = closest[1][0]
    return {
        'name' : MARS_LOC.Feature_Name[index],
        'latitude' : MARS_LOC.Center_Latitude[index],
        'longitude' : MARS_LOC.Center_Longitude[index],
        'distance' : closest[0][0],
        'quad' : MARS_LOC.Quad[index]
    }

print(cartesian(*list(point)))
print(find_nearest_loc(point[0], point[1]))
### FIND MATCHING AREA ###


### RETURN RESULTS ###
