import os
import logging
from flask import Flask, request
import flask
import geopandas as gpd
import pandas as pd
import s2sphere
import xarray as xr
import rioxarray as rxr
# from vectorize import xr_vectorize
import uuid, json, copy
import numpy as np
import gc
from utils.dataset import get_resolution
import math

logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)

def gpd_read_parquet(path):
    data = pd.read_parquet(path)
    gdf = gpd.GeoDataFrame(data, geometry=gpd.GeoSeries.from_wkb(data["geometry"]))
    return gdf

gpd.read_parquet = gpd_read_parquet
sample_geojson = json.load(open('geojson_base.json'))

def vector_points(da):
    da = da.to_dict()
    gj = sample_geojson
    print(da['coords']['point'].keys())
    coords = da['coords']['point']['data']
    data = {
        k: da['data_vars'][k]['data'] for k in da['data_vars'].keys()
    }
    features_buff = []
    for idx, coord in enumerate(coords):
        properties = {k: data[k][idx] for k in data.keys()}
        features_buff.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": coord
            },
            "properties": properties
        })
    gj['features'] = features_buff
    return gj


@app.route("/cog2pt/", methods=["POST"])
def to_extent():
    """Handle tile requests."""
    logging.info(request.get_json())
    logging.info(type(request.get_json()))
    data = request.get_json()
    raster = xr.open_dataarray(os.path.join(os.environ["MNT_BASE"], data["raster"])).isel(band=0)
    output = os.path.join(os.environ["MNT_BASE"], data["output"])
    # output = data['output']
    for p in range(1, len(output.split('/'))):
        p = '/' + '/'.join(output.split('/')[1:p+1])
        print(p)
        if not os.path.exists(p):
            os.makedirs(p)
    xmin, xmax = np.min(raster.x).values, np.max(raster.x).values
    ymin, ymax = np.min(raster.y).values, np.max(raster.y).values
    print(xmin, xmax, ymin, ymax)
    xstep, ystep = [math.ceil(i * 1000) for i in get_resolution(raster)]
    for x in np.arange(xmin, xmax, xstep):
        for y in np.arange(ymin, ymax, ystep):
            with raster.rio.clip_box(
                minx=x,
                miny=y,
                maxx=x+xstep,
                maxy=y+ystep,
            ).stack(point=('x', 'y')).dropna("point") as ds:
                if len(ds.point) > 0:
                    print(x, y)
                    gdf = gpd.read_file(json.dumps(vector_points(ds)), driver='GeoJSON')
                    gdf = gdf.set_crs(raster.rio.crs, allow_override=True)
                    gdf = gdf.to_crs("EPSG:4326")
                    fname = f'{str(x)[0:7].replace("-", "W")}_{str(y)[0:7].replace("-", "S")}_{xstep}.parquet'
                    gdf.to_parquet(os.path.join(output, fname))
                    del gdf
            gc.collect()

    return ("Completed", 200)


@app.route("/zarr2pt/", methods=["POST"])
def zarr2pt():
    """Handle tile requests."""
    data = request.get_json()
    raster = xr.open_zarr(data['data'])
    print(raster.attrs)
    print(raster.rio.crs)
    try: 
        raster.rio.write_crs(raster.rio.crs, inplace=True)
    except rxr.exceptions.MissingCRS:
        raster.rio.write_crs(data['crs'], inplace=True)
    print(raster)
    output = data["output"]
    # output = data['output']
    for p in range(1, len(output.split('/'))):
        p = '/' + '/'.join(output.split('/')[1:p+1])
        print(p)
        if not os.path.exists(p):
            os.makedirs(p)
            
    xmin, xmax = np.min(raster.x).values, np.max(raster.x).values
    ymin, ymax = np.min(raster.y).values, np.max(raster.y).values
    print(xmin, xmax, ymin, ymax)
    xstep, ystep = [math.ceil(i * 1000) for i in get_resolution(raster)]
    for x in np.arange(xmin, xmax, xstep):
        for y in np.arange(ymin, ymax, ystep):
            with raster.rio.clip_box(
                minx=x,
                miny=y,
                maxx=x+xstep,
                maxy=y+ystep,
            ).stack(point=('x', 'y')) as ds:
                if np.any([ds[i].max().values > 0 for i in ds]):
                    print(x, y)
                    ds = ds.compute()
                    ds = ds.where(ds > 0, drop=True)
                    gdf = gpd.read_file(json.dumps(vector_points(ds)), driver='GeoJSON')
                    gdf = gdf.set_crs(raster.rio.crs, allow_override=True)
                    gdf = gdf.to_crs("EPSG:4326")
                    print(gdf)
                    fname = f'{str(x)[0:7].replace("-", "W")}_{str(y)[0:7].replace("-", "S")}_{xstep}.parquet'
                    gdf.to_parquet(os.path.join(output, fname))
                    del gdf
                else:
                    print("skipping")
            gc.collect()

    return ("Completed", 200)


@app.get("/")
def test():
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
