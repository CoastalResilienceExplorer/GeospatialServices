import os
import logging
from flask import Flask, request
import geopandas as gpd
import pandas as pd
import xarray as xr
import rioxarray as rxr
# from vectorize import xr_vectorize
import uuid, json, copy
import numpy as np
import gc
from utilities.dataset import get_resolution, open_as_ds
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

# GEOM_TYPE="SQUARES"
GEOM_TYPE="SQUIRCLE"
# GEOM_TYPE="POINTS"


def generate_squircle(X, Y, r, shrink=0.9, num_points=100):
    """
    Generate points of a squircle polygon with a specific border-radius.

    Parameters:
    r (float): Border-radius of the squircle.
    num_points (int): Number of points to generate for the polygon.

    Returns:
    List of tuples: Points of the squircle polygon.
    """
    theta = np.linspace(0, 2 * np.pi, num_points)
    points = []
    r = r * shrink * 0.5

    for angle in theta:
        x = r * np.sign(np.cos(angle)) * np.abs(np.cos(angle))**0.5 + X
        y = r * np.sign(np.sin(angle)) * np.abs(np.sin(angle))**0.5 + Y
        points.append((x, y))

    points.append(points[0])
    return [points]


def vector_points(da, res):
    da = da.to_dict()
    gj = sample_geojson
    coords = da['coords']['point']['data']
    data = {
        k: da['data_vars'][k]['data'] for k in da['data_vars'].keys()
    }
    features_buff = []
    if GEOM_TYPE == "POINTS":
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
    elif GEOM_TYPE == "SQUARES":
        for idx, coord in enumerate(coords):
            properties = {k: data[k][idx] for k in data.keys()}
            features_buff.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [coord[0] - res[0]/2., coord[1] + res[1]/2.],
                        [coord[0] + res[0]/2., coord[1] + res[1]/2.],
                        [coord[0] + res[0]/2., coord[1] - res[1]/2.],
                        [coord[0] - res[0]/2., coord[1] - res[1]/2.],
                        [coord[0] - res[0]/2., coord[1] + res[1]/2.]
                    ]]
                },
                "properties": properties
            })
        gj['features'] = features_buff
        return gj
    elif GEOM_TYPE == "SQUIRCLE":
        for idx, coord in enumerate(coords):
            properties = {k: data[k][idx] for k in data.keys()}
            features_buff.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": generate_squircle(coord[0], coord[1], res)
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
    raster = open_as_ds(data['data'])

    res = get_resolution(raster)
    try: 
        raster.rio.write_crs(raster.rio.crs, inplace=True)
    except rxr.exceptions.MissingCRS:
        raster.rio.write_crs(data['crs'], inplace=True)
    output = data["output"]
    # output = data['output']
    for p in range(1, len(output.split('/'))):
        p = '/' + '/'.join(output.split('/')[1:p+1])
        if not os.path.exists(p):
            os.makedirs(p)
            
    xmin, xmax = np.min(raster.x).values, np.max(raster.x).values
    ymin, ymax = np.min(raster.y).values, np.max(raster.y).values
    xstep, ystep = [math.ceil(i * 1000) for i in res]
    for x in np.arange(xmin, xmax, xstep):
        for y in np.arange(ymin, ymax, ystep):
            with raster.rio.clip_box(
                minx=x,
                miny=y,
                maxx=x+xstep,
                maxy=y+ystep,
            ).stack(point=('x', 'y')) as ds:
                if np.any([ds[i].max().values > 0 for i in ds]):
                    ds = ds.compute()
                    ds = ds.where(ds > 0, drop=True)
                    gdf = gpd.read_file(json.dumps(vector_points(ds, res[0])), driver='GeoJSON')
                    gdf = gdf.set_crs(raster.rio.crs, allow_override=True)
                    gdf = gdf.to_crs("EPSG:4326")
                    fname = f'{str(x)[0:7]}_{str(y)[0:7]}_{str(x+xstep)[0:7]}_{str(y+ystep)[0:7]}.parquet'
                    gdf.to_parquet(os.path.join(output, fname))
                    del gdf
                else:
                    logging.info("skipping")
            gc.collect()

    return ("Completed", 200)


@app.get("/")
def test():
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
