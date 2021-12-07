"""Module to generate the RKL map."""

import pandas as pd
import folium

import pathlib


world = folium.Map(
    zoom_start=2,
    location=[13.133932434766733, 16.103938729508073]
)

assets_dir = pathlib.Path(__file__).parent.parent.absolute().joinpath('assets')
kongs_dir = assets_dir.joinpath('kongs')

kong_df = pd.read_csv(assets_dir.joinpath('map_kongs.csv'), index_col=0)

for kong in kong_df.reset_index().itertuples():
    kong_icon = folium.features.CustomIcon(str(kongs_dir.joinpath(kong.kong_image_name)), icon_size=(40, 40))
    kong_popup = f'<strong>{kong.kong_name}</strong><br>:{kong.kong_text}'
    folium.Marker(
        location=[kong.longitude, kong.latitude],
        popup=kong.kong_name,
        tooltip=kong.kong_name,
        icon=kong_icon,
    ).add_to(world)

world.save('test.html')
