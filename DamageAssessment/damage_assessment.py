import rioxarray as rxr
import xarray as xr
import pandas as pd
from rasterio.errors import NotGeoreferencedWarning
import warnings
from utils.dataset import get_resolution, degrees_to_meters
from utils.damages import apply_ddf
import subprocess
import numpy as np
import math


BUILDING_AREA = 'gs://supporting-data2/WSF3d_v02_BuildingArea.tif'
DDF = './data/damage/DDF_Americas.csv'
MAXDAMAGE = './data/damage/MaxDamage_per_m2.csv'
COUNTRY = "Belize"


def main(flooding: xr.Dataset | xr.DataArray, window=0, population_min=5):
    init_crs = flooding.rio.crs
    flooding = flooding.rio.reproject("EPSG:4326")
    buildings = rxr.open_rasterio(
        BUILDING_AREA
    ).isel(band=0)
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            category=NotGeoreferencedWarning,
            module="rasterio",
        )
        flooding_res = get_resolution(flooding)
        minx, miny, maxx, maxy = flooding.rio.bounds()
        buildings = buildings.rio.clip_box(
            minx=minx, miny=miny, maxx=maxx, maxy=maxy, auto_expand=True
        )
        flooding = xr.where(flooding == flooding.rio.nodata, 0, flooding).rio.write_crs('EPSG:4326')
        buildings = xr.where(buildings == buildings.rio.nodata, 0, buildings)
        buildings_res = get_resolution(buildings)

        res_modifier = (
            (flooding_res[0] * flooding_res[1]) /
            (buildings_res[0] * buildings_res[1])
        )

        buildings = buildings.reindex_like(flooding, method="nearest")
        buildings = buildings * res_modifier
        damage_percents = apply_ddf(flooding)
        max_damage_df = pd.read_csv(MAXDAMAGE)
        max_damage = max_damage_df[max_damage_df["Country"] == COUNTRY]["Total"].values[0]
        damage_totals = damage_percents * max_damage
        if window:
            print('windowing')
            from population_assessment import POPULATION
            population = rxr.open_rasterio(
                POPULATION
            ).isel(band=0)
            population = population.rio.clip_box(
                minx=minx, miny=miny, maxx=maxx, maxy=maxy, auto_expand=True
            )
            population_res = get_resolution(population)
            population_res = degrees_to_meters(population_res[0], population.rio.bounds()[3])
            window_size = math.ceil(window / population_res)
            population = population.rolling(x=window_size, y=window_size, center=True).sum()
            population = xr.where(population > population_min, 1, 0)
            population = population.reindex_like(damage_totals, method="nearest")
            damage_totals = damage_totals * population

        return (damage_totals * buildings).rio.reproject(init_crs)
