import os
import logging
import flask
from flask import Flask, request
import xarray as xr
import rioxarray as rxr
import copy, io
import uuid

from utils.api_requests import response_to_tiff
from utils.dataset import makeSafe_rio
from utils.gcs import upload_blob, compress_file
from damage_assessment import main as damage_assessment

logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)

GCS_BASE=os.environ['OUTPUT_BUCKET']

# @response_to_tiff MOVE ME DOWN FOR AUTOTIFF
@app.route('/damage/dlr_guf/', methods=["POST"])
def api_damage_assessment():
    flooding = rxr.open_rasterio(
        io.BytesIO(request.files['flooding'].read())
    ).isel(band=0)
    x = makeSafe_rio(flooding)
    damages = damage_assessment(x)
    id = str(uuid.uuid4())
    tmp_rast = f"/tmp/{id}.tiff"
    tmp_rast_compressed = f"/tmp/{id}.tiff.gz"
    damages.rio.to_raster(tmp_rast)
    upload_blob(GCS_BASE, tmp_rast, request.form['output'])
    compress_file(tmp_rast, tmp_rast_compressed)
    return flask.send_from_directory('/tmp', f'{id}.tiff.gz')


@app.get("/")
def test():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
