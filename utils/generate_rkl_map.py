"""Module to generate the RKL map."""

import pandas as pd
import folium
import io
from PIL import Image
import pathlib

from selenium import webdriver
# browser = webdriver.Firefox()


world = folium.Map(
    zoom_start=2.5,
    location=[13.133932434766733, 16.103938729508073]
)

assets_dir = pathlib.Path(__file__).parent.parent.absolute().joinpath('assets')
kongs_dir = assets_dir.joinpath('kongs')

kong_df = pd.read_csv(assets_dir.joinpath('map_kongs.csv'), index_col=0)

for kong in kong_df.reset_index().itertuples():
    size_width = 100 * kong.scaling_factor * kong.image_ratio_width / kong.image_ratio_height
    size_height = 100 * kong.scaling_factor * kong.image_ratio_height / kong.image_ratio_width
    kong_icon = folium.features.CustomIcon(str(kongs_dir.joinpath(kong.kong_image_name)), icon_size=(size_width, size_height))
    kong_popup = f'<strong>{kong.kong_name}</strong><br>{kong.kong_text}'
    folium.Marker(
        location=[kong.longitude, kong.latitude],
        popup=kong.kong_name,
        tooltip=kong.kong_name,
        icon=kong_icon,
    ).add_to(world)

# img_data = world._to_png(5)
# img = Image.open(io.BytesIO(img_data))
# img.save('ckc_map.png')

world.save('ckc_map.html')
