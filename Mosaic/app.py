import os
import logging
import flask
from flask import Flask, request
import xarray as xr
import rioxarray as rxr
import geopandas as gpd
from glob import glob
import numpy as np
from utils.geo import idw_mosaic
from utils.dataset import compressRaster

logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)


@app.route('/mosaic/', methods=["POST"])
def api_mosaic():
    '''Combine two rasters into one using a merge method'''
    ds1 = xr.open_zarr(os.path.join(os.getenv("MOUNT_PATH"), request.form['zarr1']))
    ds2 = xr.open_zarr(os.path.join(os.getenv("MOUNT_PATH"), request.form['zarr2']))
    var = request.form['var']
    logging.info(var)
    
    ds1.rio.write_crs(ds1.attrs['crs'], inplace=True)
    ds2.rio.write_crs(ds2.attrs['crs'], inplace=True)
    if ds1.rio.crs != ds2.rio.crs:
        ds2 = ds2.rio.reproject(ds1.rio.crs)

    output_dir = os.path.join(os.getenv("MOUNT_PATH"), request.form["output_dir"])
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    _vars = list(ds1.data_vars)
    ds = idw_mosaic(ds1[var], ds2[var])
    compressRaster(ds, os.path.join(output_dir, f'{var}.tif'))
    
    return ("complete", 200)


@app.get("/")
def test():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
