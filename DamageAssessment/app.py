import os
import logging
import flask
from flask import Flask, request
import xarray as xr
import rioxarray as rxr
import copy, io
import uuid

from utils.api_requests import response_to_tiff_factory, response_to_gpkg_factory, nodata_to_zero
from utils.dataset import makeSafe_rio, compressRaster
from utils.gcs import upload_blob, compress_file
from damage_assessment import main as damage_assessment
from population_assessment import main as population_assessment
from nsi_assessment import get_nsi, get_nsi_damages

logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)

@app.route('/damage/dlr_guf/', methods=["POST"])
@response_to_tiff_factory(app)
@nodata_to_zero
def api_damage_assessment():
    flooding = rxr.open_rasterio(
        io.BytesIO(request.files['flooding'].read())
    ).isel(band=0)
    x = makeSafe_rio(flooding)
    if 'window_size' in request.form:
        return damage_assessment(
            x, 
            float(request.form['window_size']),
            float(request.form['population_min'])
        )
    return damage_assessment(x)

@app.route('/population/GHSL_2020_100m/', methods=["POST"])
@response_to_tiff_factory(app)
@nodata_to_zero
def api_population_assessment():
    flooding = rxr.open_rasterio(
        io.BytesIO(request.files['flooding'].read())
    ).isel(band=0)
    x = makeSafe_rio(flooding)
    return population_assessment(x, float(request.form['threshold']))


@app.route('/damage/nsi/', methods=["POST"])
@response_to_gpkg_factory(app)
def api_nsi_assessment():
    print(request.form)
    flooding = rxr.open_rasterio(
        io.BytesIO(request.files['flooding'].read())
    ).isel(band=0)
    x = makeSafe_rio(flooding)
    left, bottom, right, top = x.rio.bounds()
    print(left, bottom, right, top)
    nsi = get_nsi(left=left, bottom=bottom, right=right, top=top, state=request.form['nsi'], crs=flooding.rio.crs)
    damages = get_nsi_damages(flooding, nsi)
    return damages


@app.get("/")
def test():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
