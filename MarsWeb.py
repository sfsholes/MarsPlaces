import numpy  as np
import pandas as pd
import streamlit as st
import math
import geocoder
import reverse_geocoder as rg
import matplotlib.pyplot as plt
import PIL
from scipy import spatial

# Need to include this otherwise will think it's an attack
# i.e., I trust this image I'm analyzing
PIL.Image.MAX_IMAGE_PIXELS = 227687200

mola = plt.imread('data/Mars_MGS_colorhillshade_mola_1024.jpg')
viking = plt.imread('data/Mars_Viking_MDIM21_ClrMosaic_global_1024.jpg')
viking_zoom = PIL.Image.open('data/Mars_Viking_MDIM21_ClrMosaic_1km.jpg')
viking_zoom_width, viking_zoom_height = viking_zoom.size
earth = plt.imread('data/Earthmap1000x500.jpg')

def find_nearest_elem(array, value):
    idx = (np.abs(array - value)).argmin()
    return idx

def findBBox(point, height, width, buffer):
    """Takes the user input point and finds the bounding box to plot the zoomed image.
    tuple point: tuple of coordinates (latitude, longitude)
    int height: image pixel height
    int width: image pixel width
    float buffer: buffer in degrees lat/lon to display"""
    X = np.linspace(-180,180,width)
    Y = np.linspace(90,-90, height)
    lat, lon = point[0], point[1]
    # We want to find the pixel coordinates that correspond to the input point
    px_x = find_nearest_elem(X,lon)
    px_y = find_nearest_elem(Y,lat)

    x_min = find_nearest_elem(X,lon-buffer)
    x_max = find_nearest_elem(X,lon+buffer)
    y_min = find_nearest_elem(Y,lat-buffer)
    y_max = find_nearest_elem(Y,lat+buffer)

    #PIL wants left, top, right, bottom
    return [(x_min, y_max, x_max, y_min), (X[x_min], Y[y_max], X[x_max], Y[y_min])]

def cartesian(latitude, longitude, elevation=0):
    # Convert to radians
    latitude *= math.pi / 180
    if longitude < 0:
        longitude = 360 + longitude
    longitude *= math.pi / 180

    R = 3389.5 #km
    #R = 6371
    X = R * math.cos(latitude) * math.cos(longitude)
    Y = R * math.cos(latitude) * math.sin(longitude)
    Z = R * math.sin(latitude) + elevation

    return (X, Y, Z)

def user_input_features():
    input_type = st.sidebar.radio('Input Method', ('Coordinates', 'City Name'))

    lat_input = st.sidebar.number_input('Latitude', min_value=-90., max_value=90., value=43.214408)
    lon_input = st.sidebar.number_input('Longitude', min_value=-360., max_value=360., value=-76.712236)
    st.sidebar.write('-'*10)
    city = st.sidebar.text_input('City Name:', 'Red Creek, NY')

    if input_type == 'Coordinates':
        lat = lat_input
        lon = lon_input
        city_output = rg.search((lat_input,lon_input), mode=1)[0]['name']
    elif input_type == 'City Name':
        city_data = geocoder.osm(city)
        lat = city_data.lat
        lon = city_data.lng
        city_output = city
    cartesian_coords = cartesian(lat, lon)
    data = {
            'latitude' : lat,
            'longitude' : lon,
            'cartesian' : cartesian_coords,
            'city' : city_output
    }
    return data

st.sidebar.header('User Input Parameters')
user_data = user_input_features()
user_point = (user_data['latitude'], user_data['longitude'])
user_city = user_data['city']

# Data retrieved from https://planetarynames.wr.usgs.gov/
Mars_Places = pd.read_csv("data/MarsPlacesApproved.csv")

def isInPolygon(row):
    #return point.within(row[11])
    if (user_point[0]>row[5] and user_point[0]<row[4] and user_point[1]<row[6] and user_point[1]>row[7]):
        return True
    else:
        return False

Mars_Places['Within'] = Mars_Places.apply(isInPolygon, axis=1)
located_df = Mars_Places.loc[Mars_Places['Within'] == True]

places = []
for index, row in Mars_Places.iterrows():
    coordinates = [row['Center_Latitude'], row['Center_Longitude']]
    cartesian_coord = cartesian(*coordinates)
    places.append(cartesian_coord)

tree = spatial.KDTree(places)

def find_nearest_loc(lat, lon):
    cartesian_coord = cartesian(lat, lon)
    closest = tree.query([cartesian_coord], p = 2)
    index = closest[1][0]
    return {
        'name' : Mars_Places.Feature_Name[index],
        'latitude' : Mars_Places.Center_Latitude[index],
        'longitude' : Mars_Places.Center_Longitude[index],
        'distance' : closest[0][0],
        'quad' : Mars_Places.Quad[index]
    }

closest_place = find_nearest_loc(user_point[0], user_point[1])


### --- MAIN PAGE LAYOUT --- ###


st.write("""
# Find Where You Live on Mars

Type in your location in the sidebar (<) to find where you would live on Mars.

""")

map_type = st.radio('Type of Map', ('Mars Topography', 'Mars', 'Earth'))
if map_type == 'Mars':
    map_img = viking
elif map_type == 'Earth':
    map_img = earth
else:
    map_img = mola

BBox = (-180, 180, -90, 90)
fig, ax = plt.subplots()
ax.set_xlim(BBox[0],BBox[1])
ax.set_ylim(BBox[2],BBox[3])
ax.imshow(map_img, zorder=0, extent = BBox, aspect= 'equal')
plt.plot(user_point[1], user_point[0], marker="*", markersize=6, markerfacecolor='w', markeredgecolor='k', markeredgewidth=1)

st.pyplot(fig)

st.subheader('User Input Coordinates')
st.write(user_point, user_city)

st.subheader('Closest Place on Mars')
st.write(closest_place)

#PIL wants left, top, right, bottom
zbbx = findBBox(user_point, viking_zoom_height, viking_zoom_width, 10)
vik_zoom_crop = viking_zoom.crop(zbbx[0])
fig2, ax2 = plt.subplots()
ax2.set_xlim(zbbx[1][0],zbbx[1][2])
ax2.set_ylim(zbbx[1][3],zbbx[1][1])
ax2.imshow(vik_zoom_crop, zorder=0, extent=(zbbx[1][0], zbbx[1][2], zbbx[1][3], zbbx[1][1]), aspect='equal')
plt.plot(user_point[1], user_point[0], marker="*", markersize=6, markerfacecolor='w', markeredgecolor='k', markeredgewidth=1)
st.pyplot(fig2)

st.subheader('Located Within')
st.write(located_df)
