import os
import logging
import flask
from flask import Flask, request
import xarray as xr
import rioxarray as rxr
import geopandas as gpd
from glob import glob

logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)


def summary_stats(gdf: gpd.GeoDataFrame, ds: xr.DataArray | xr.Dataset):



@app.route('/summary_stats/', methods=["POST"])
def api_summary_stats():
    fname = os.path.join('/tmp', request.files['geographies'].filename.split('/')[-1])
    with open(fname, 'wb') as f:
        f.write(request.files['data'].read())
    gdf = gpd.read_file(
        fname, engine='pyogrio', use_arrow=True
    )

    glob(os.path.join(os.getenv('MOUNT_PATH'), request.form['project'], request.form['key'], request.form['data']), '*.tif')
    rasters = {
        d.split('/')[-1].split('.')[0]: rxr.open_rasterio(d) for d in rasters
    }
    CRS = list(rasters.values())[0].rio.crs
    ds = xr.open_zarr(os.path.join(os.getenv('MOUNT_PATH'), request.form['project'], request.form['key'], request.form['type']))
    logging.info(ds)

    return ("complete", 200)



@app.get("/")
def test():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
