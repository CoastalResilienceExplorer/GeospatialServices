from functools import wraps
import logging
from flask import request
import flask
import geopandas as gpd
import uuid, os
import xarray as xr
import subprocess
from utils.gcs import upload_blob
from utils.dataset import compressRaster

logging.basicConfig()
logging.root.setLevel(logging.INFO)

TMP_FOLDER='/tmp'
GCS_BASE=os.environ['OUTPUT_BUCKET']

def data_to_parameters_factory(app):
    def data_to_parameters(func):
        with app.test_request_context():
            @wraps(func)
            def wrapper(*args, **kwargs):
                """A wrapper function"""
                # Extend some capabilities of func
                data = request.get_json()
                logging.info(data)
                to_return = func(**data)
                return to_return
            return wrapper
    return data_to_parameters


def response_to_gpkg(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        """A wrapper function"""
        xid = str(uuid.uuid1())
        # Extend some capabilities of func
        gdf_to_return = func(*args, **kwargs)
        logging.info(gdf_to_return)
        assert isinstance(gdf_to_return, gpd.GeoDataFrame)
        fname=f'{xid}.gpkg'
        gdf_to_return.to_file(os.path.join(TMP_FOLDER, fname))
        return flask.send_from_directory(TMP_FOLDER, fname)

    return wrapper


def response_to_tiff_factory(app):
    def response_to_tiff(func):
        with app.test_request_context():
            @wraps(func)
            def wrapper(*args, **kwargs):
                id = str(uuid.uuid4())
                # Extend some capabilities of func
                xr_to_return = func(*args, **kwargs)
                logging.info(xr_to_return)
                assert isinstance(xr_to_return, xr.DataArray) | isinstance(xr_to_return, xr.Dataset)
                fname = f"{id}.tiff"
                tmp_rast_compressed = os.path.join(TMP_FOLDER, fname)
                compressRaster(xr_to_return, tmp_rast_compressed)
                data = request.form
                if "output_to_gcs" in data.keys():
                    upload_blob(GCS_BASE, tmp_rast_compressed, request.form['output_to_gcs'])
                return flask.send_from_directory(TMP_FOLDER, fname)
        return wrapper
    return response_to_tiff


def response_to_tiff(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        """A wrapper function"""
        id = str(uuid.uuid4())
        # Extend some capabilities of func
        xr_to_return = func(*args, **kwargs)
        logging.info(xr_to_return)
        assert isinstance(xr_to_return, xr.DataArray) | isinstance(xr_to_return, xr.Dataset)
        fname = f"{id}.tiff"
        tmp_rast_compressed = os.path.join(TMP_FOLDER, fname)
        compressRaster(xr_to_return, tmp_rast_compressed)
        return flask.send_from_directory(TMP_FOLDER, fname)
    
    return wrapper