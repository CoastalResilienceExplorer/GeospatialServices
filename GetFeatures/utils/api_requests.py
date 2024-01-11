from functools import wraps
import logging
from flask import request
import flask
import geopandas as gpd
import uuid, os

logging.basicConfig()
logging.root.setLevel(logging.INFO)

TMP_FOLDER='/tmp'

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