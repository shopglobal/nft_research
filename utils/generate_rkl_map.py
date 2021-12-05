"""Module to generate the RKL map."""

import pandas as pd
import folium


world = folium.Map(
    zoom_start=2,
    location=[13.133932434766733, 16.103938729508073]
)

# Dictionary where key is Kong name and Value is list containing Latitude / Longitude
kong_locations = {'Roboklopp': [51.5085300, -0.1257400],
                  }

for ken in kong_locations.keys():
    folium.Marker(
        location=kong_locations[key],
        popup=key,
        tooltip=key,
        icon=folium.Icon(color='Yellow', prefix='fa', icon='circle'),
    ).add_to(world)

world.save('test.html')
