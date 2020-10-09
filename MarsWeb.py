import numpy  as np
import pandas as pd
import streamlit as st
import math
import geocoder
import matplotlib.pyplot as plt
import PIL
from scipy import spatial

# Need to include this otherwise will think it's an attack
# i.e., I trust this image I'm analyzing
PIL.Image.MAX_IMAGE_PIXELS = 227687200

mola = plt.imread('data/Mars_MGS_colorhillshade_mola_1024.jpg')
viking = plt.imread('data/Mars_Viking_MDIM21_ClrMosaic_global_1024.jpg')
viking_zoom = PIL.Image.open('data/Mars_Viking_MDIM21_ClrMosaic_1km_lowres_half.jpg')
viking_zoom_width, viking_zoom_height = viking_zoom.size
earth = plt.imread('data/Earthmap1000x500.jpg')

@st.cache()
def find_nearest_elem(array, value):
    idx = (np.abs(array - value)).argmin()
    return idx

@st.cache()
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

@st.cache()
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

    if input_type == 'Coordinates':
        lat = st.sidebar.number_input('Latitude', min_value=-90., max_value=90., value=-4.59)
        lon = st.sidebar.number_input('Longitude', min_value=-360., max_value=360., value=137.44)
        # if using reverse_geocoder:
        #city_output = rg.search((lat_input,lon_input), mode=1)[0]['name']
        city_data = geocoder.osm((lat, lon), method="reverse")
        if city_data.city is None:
            if city_data.county is None:
                city = ''
            else:
                city = city_data.county
        else:
            city = city_data.city
    elif input_type == 'City Name':
        city = st.sidebar.text_input('City Name:', 'Pasadena, CA')
        city_data = geocoder.osm(city)
        lat, lon = city_data.lat, city_data.lng

    if city_data.state is None:
        state = ''
    else:
        state = city_data.state

    #st.sidebar.header('OR Find a Famous Place on Mars')
    #st.sidebar.selectbox('Mars Landmark', ('--Select--','Gale Crater', 'Face on Mars'))

    cartesian_coords = cartesian(lat, lon)
    data = {
            'latitude' : lat,
            'longitude' : lon,
            'cartesian' : cartesian_coords,
            'city' : city,
            'state' : state,
            'country' : city_data.country
    }
    return data

st.sidebar.header('User Input Parameters')
user_data = user_input_features()
user_point = (user_data['latitude'], user_data['longitude'])

# Data retrieved from https://planetarynames.wr.usgs.gov/
Mars_Places = pd.read_csv("data/MarsPlacesApproved.csv")

@st.cache()
def isInPolygon(row):
    #return point.within(row[11])
    if (user_point[0]>row[5] and user_point[0]<row[4] and user_point[1]<row[6] and user_point[1]>row[7]):
        return True
    else:
        return False

Mars_Places['Within'] = Mars_Places.apply(isInPolygon, axis=1)
located_df = Mars_Places.loc[Mars_Places['Within'] == True]

@st.cache()
def find_nearest_loc(lat, lon):
    places = []
    for index, row in Mars_Places.iterrows():
        coordinates = [row['Center_Latitude'], row['Center_Longitude']]
        cartesian_coord = cartesian(*coordinates)
        places.append(cartesian_coord)

    tree = spatial.KDTree(places)

    cartesian_coord = cartesian(lat, lon)
    closest = tree.query([cartesian_coord], p = 2)
    index = closest[1][0]
    return {
        'name' : Mars_Places.Feature_Name[index],
        'latitude' : Mars_Places.Center_Latitude[index],
        'longitude' : Mars_Places.Center_Longitude[index],
        'distance' : closest[0][0],
        'quad' : Mars_Places.Quad[index],
        'feature' : Mars_Places.Feature_Type[index]
    }

closest_place = find_nearest_loc(user_point[0], user_point[1])


### --- MAIN PAGE LAYOUT --- ###


st.write("""
# Find Where You Live on Mars

Type in your location in the left sidebar to find where you would live on Mars.

""")

st.subheader('Location on Earth')
st.write(np.round(user_point[0],2), np.round(user_point[1],2), user_data['city'], ',', user_data['state'], ',', user_data['country'])

if 'Crater' in closest_place['feature']:
    crater = ' Crater'
else:
    crater = ''

st.subheader('Closest Place on Mars: ')
st.write(int(closest_place['distance']), 'km from the center of ', closest_place['name'], crater)


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


#PIL wants left, top, right, bottom
zbbx = findBBox(user_point, viking_zoom_height, viking_zoom_width, 10)
vik_zoom_crop = viking_zoom.crop(zbbx[0])
viking_zoom.close()
fig2, ax2 = plt.subplots()
ax2.set_xlim(zbbx[1][0],zbbx[1][2])
ax2.set_ylim(zbbx[1][3],zbbx[1][1])
ax2.imshow(vik_zoom_crop, zorder=0, extent=(zbbx[1][0], zbbx[1][2], zbbx[1][3], zbbx[1][1]), aspect='equal')
plt.plot(user_point[1], user_point[0], marker="*", markersize=6, markerfacecolor='w', markeredgecolor='k', markeredgewidth=1)
if closest_place['longitude'] < zbbx[1][2] and closest_place['longitude'] > zbbx[1][0] and closest_place['latitude'] < zbbx[1][1] and closest_place['latitude'] > zbbx[1][3]:
    plt.text(closest_place['longitude'], closest_place['latitude'] + 0.35, closest_place['name']+crater, horizontalalignment='center', fontsize=8)
    plt.plot(closest_place['longitude'], closest_place['latitude'], marker="X", markersize=6, markerfacecolor='y', markeredgecolor='k', markeredgewidth=1)
st.pyplot(fig2)

st.subheader('This place may also be located within the following features:')
st.write(located_df[['Feature_Name', 'Center_Latitude', 'Center_Longitude']])
