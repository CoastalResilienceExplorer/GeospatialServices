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
    gj['features'] = [{
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": i[1]
        },
        "properties": {
            "value": i[0]
        }
    } for i in zip(da['data'], da['coords']['point']['data'])]
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
    xstep, ystep = 4,4
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
                    fname = f'{str(x)[0:7].replace("-", "W")}_{str(y)[0:7].replace("-", "S")}_{xstep}.parquet'
                    gdf.to_parquet(os.path.join(output, fname))
                    del gdf
            gc.collect()

    return ("Completed", 200)


@app.get("/")
def test():
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
