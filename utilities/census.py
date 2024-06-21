import requests
import geopandas as gpd
from io import BytesIO
from zipfile import ZipFile


# def get_blockgroups_by_county(state_fips='06', county_fips='037'):
#     # Download the shapefile for block groups
#     shapefile_url = f'https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_{state_fips}_{county_fips}_bg_500k.zip'
#     shapefile_response = requests.get(shapefile_url)

#     # Read the shapefile using geopandas
#     print(shapefile_response.content)
#     with ZipFile(BytesIO(shapefile_response.content)) as zip_file:
#         with zip_file.open(f'cb_2021_{state_fips}_{county_fips}_bg_500k.shp') as shp_file:
#             gdf = gpd.read_file(shp_file)
#             return gdf

# def get_blockgroups_by_county(state_fips='06', county_fips='037'):
#     # Replace 'YOUR_API_KEY' with the actual API key you obtained
#     api_key = '70eab5db3811f21671bcdae92354b152288cea74'

#     # API endpoint for block group boundaries
#     url = f'https://api.census.gov/data/2010/dec/sf1?get=GEO_ID,NAME&for=block%20group:*&in=state:{state_fips}+county:{county_fips}&key={api_key}'

#     # Make the request
#     response = requests.get(url)

#     # Parse the JSON response
#     data = response.json()
#     return data