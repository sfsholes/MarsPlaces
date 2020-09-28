import numpy  as np
import pandas as pd
import streamlit as st
import math
import geocoder
from scipy import spatial

st.write("""
# Find Where You Live on Mars

Type in your Lat/Lon Coordinates to find the nearest place on Mars

""")

st.sidebar.header('User Input Parameters')

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
        lat = st.sidebar.number_input('Latitude', min_value=-90., max_value=90., value=43.214408)
        lon = st.sidebar.number_input('Longitude', min_value=-360., max_value=360., value=-76.712236)
    elif input_type == 'City Name':
        city = st.sidebar.text_input('City Name:', 'Santa Barbara, CA')
        city_data = geocoder.osm(city)
        lat = city_data.lat
        lon = city_data.lng
    cartesian_coords = cartesian(lat, lon)
    data = {
            'latitude' : lat,
            'longitude' : lon,
            'cartesian' : cartesian_coords
    }
    return data

user_data = user_input_features()
user_point = (user_data['latitude'], user_data['longitude'])
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

st.subheader('User Input Coordinates')
st.write(user_point)

st.subheader('Closest Place on Mars')
st.write(closest_place)

st.subheader('Located Within')
st.write(located_df)
