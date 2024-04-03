import os
import logging
import flask
from flask import Flask, request
import xarray as xr
import rioxarray as rxr
import copy, io
import uuid

from utils.api_requests import response_to_tiff_factory
from utils.dataset import makeSafe_rio, compressRaster
from utils.gcs import upload_blob, compress_file
from utils.pystac_utils import get_landuse, download_and_compile_items
from damage_assessment import main as damage_assessment
from population_assessment import main as population_assessment

logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)

GCS_BASE=os.environ['OUTPUT_BUCKET']

@app.route('/damage/dlr_guf/', methods=["POST"])
@response_to_tiff_factory(app)
def api_damage_assessment():
    flooding = rxr.open_rasterio(
        io.BytesIO(request.files['flooding'].read())
    ).isel(band=0)
    x = makeSafe_rio(flooding)
    return damage_assessment(x)

@app.route('/population/GHSL_2020_100m/', methods=["POST"])
@response_to_tiff_factory(app)
def api_population_assessment():
    flooding = rxr.open_rasterio(
        io.BytesIO(request.files['flooding'].read())
    ).isel(band=0)
    x = makeSafe_rio(flooding)
    return population_assessment(x, float(request.form['threshold']))


@app.get("/")
def test():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
