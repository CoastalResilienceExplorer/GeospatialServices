import rioxarray as rxr
import xarray as xr
import pandas as pd
from rasterio.errors import NotGeoreferencedWarning
import warnings
from utils.dataset import get_resolution, get_timestep_as_geo
from utils.damages import apply_ddf
import subprocess
import numpy as np
import logging


POPULATION = 'gs://supporting-data2/GHS_POP_E2020.tif'


def main(flooding: xr.Dataset | xr.DataArray, threshold: float):
    population = rxr.open_rasterio(
        POPULATION
    ).isel(band=0)
    flooding = flooding.rio.reproject("EPSG:4326")
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            category=NotGeoreferencedWarning,
            module="rasterio",
        )
        flooding_res = get_resolution(flooding)
        minx, miny, maxx, maxy = flooding.rio.bounds()
        population = population.rio.clip_box(
            minx=minx, miny=miny, maxx=maxx, maxy=maxy, auto_expand=True
        )
        population = xr.where(population == population.rio.nodata, 0, population).rio.write_crs("EPSG:4326")
        flooding = xr.where(flooding > threshold, 1.0, 0.0).rio.write_crs("EPSG:4326")
        population_res = get_resolution(population)

        res_modifier = (
            (flooding_res[0] * flooding_res[1]) /
            (population_res[0] * population_res[1])
        )

        population = population.reindex_like(flooding, method="nearest")
        population = population * res_modifier
        population = population * flooding
        return population


