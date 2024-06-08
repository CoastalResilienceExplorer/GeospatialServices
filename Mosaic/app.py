import os
import logging
import flask
from flask import Flask, request
import xarray as xr
import rioxarray as rxr
import geopandas as gpd
from glob import glob
import numpy as np
from utils.geo import xr_vectorize, calculate_distances_to_multipolygon, mosaic_xarray
from utils.dataset import compressRaster

logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)


@app.route('/mosaic/', methods=["POST"])
def api_mosaic():
    '''Combine two rasters into one using a merge method'''
    METHOD="IDW"

    ds1 = xr.open_zarr(os.path.join(os.getenv("MOUNT_PATH"), request.form['zarr1']))
    ds2 = xr.open_zarr(os.path.join(os.getenv("MOUNT_PATH"), request.form['zarr2']))
    ds1.rio.write_crs(ds1.attrs['crs'], inplace=True)
    ds2.rio.write_crs(ds2.attrs['crs'], inplace=True)
    logging.info(ds1.attrs)
    if ds1.rio.crs != ds2.rio.crs:
        ds2 = ds2.rio.reproject(ds1.rio.crs)

    _vars = list(ds1.data_vars)
    # logging.info(ds_total)

    for var in _vars:
        mosaic_xarray(ds1[var], ds2[var])
        break
        
        raster1 = ds1[var]
        raster2 = ds2[var]
        raster1 = xr.where(raster1 > 0, raster1)
        ds1 = ds.where()
    return ("complete", 200)
    
    compressRaster(ds_total, 'test.tif')
    # logging.info(ds2)
    
    if METHOD == "IDW":

        def distance_to_edge(da):
            y, x = np.meshgrid(np.arange(da.shape[0]), np.arange(da.shape[1]), indexing='ij')
            y_dist = np.minimum(y, da.shape[0] - y - 1)
            x_dist = np.minimum(x, da.shape[1] - x - 1)
            return np.minimum(y_dist, x_dist)

        def idw_merge(raster1, raster2, dist1, dist2):
            idw1 = 1 / (dist1 + 1)
            idw2 = 1 / (dist2 + 1)
            idw_sum = idw1 + idw2
            weighted_values = (raster1 * idw1 + raster2 * idw2) / idw_sum
            return weighted_values

    xr_mask_1 = xr.where(ds1 > 0, 1, 0).compute()
    # xr_mask_2 = xr.where(ds2 > 0, 1, 0).compute()

    logging.info(xr_mask_1)
    # logging.info(xr_mask_2)

    return ("complete", 200)
    boundary = xr_vectorize()

    dist1 = distance_to_edge(ds1[list(ds1.data_vars)[0]])
    dist2 = distance_to_edge(ds2[list(ds2.data_vars)[0]])

    merged_ds = xr.Dataset()

    logging.info(dist1)
    logging.info(dist2)
    
    for var in ds1.data_vars:
        raster1 = ds1[var]
        raster2 = ds2[var]
        
        merged_var = xr.apply_ufunc(idw_merge, raster1.load(), raster2.load(), dist1, dist2,
                                    input_core_dims=[['y', 'x'], ['y', 'x'], ['y', 'x'], ['y', 'x']],
                                    vectorize=True)
        merged_ds[var] = merged_var
    
    return merged_raster

    return ("complete", 200)





@app.get("/")
def test():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
