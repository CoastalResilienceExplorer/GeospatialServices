import flask
from flask import Flask, request
import zipfile
import os, io
import numpy as np
import shutil
from glob import glob
import uuid
import time
import json
import requests


import logging
logging.basicConfig()
logging.root.setLevel(logging.INFO)


from utils.redis import r
from utils.generators import assert_done, \
    async_runner, \
    cog_generator, \
    exposure_generator, \
    damages_generator, \
    population_generator, \
    zarr_build_generator, \
    aev_generator, \
    zarr2pt_generator, \
    pmtiles_generator

app = Flask(__name__)

CLEAN_SLATE = True
TASKS = [
    "SUBMITTED",
    "COG",
    "DAMAGES",
    "EXPOSURE",
    "POPULATION",
    "ZARR_BUILD",
    "AEV_DAMAGES",
    "AEV_POPULATION",
    "ZARR2PT",
    "PMTILES",
]

if CLEAN_SLATE:
    TASKS = [
        "SUBMITTED",
        "COG",
        "DAMAGES",
        "EXPOSURE",
        "POPULATION",
        "ZARR_BUILD",
        "AEV_DAMAGES",
        "AEV_POPULATION",
        "ZARR2PT",
        "PMTILES",
    ]

DATA_OUTPUTS = [
    'flooding',
    'damages',
    'exposure',
    'population'
]


def get_paths(project, key):
    paths_to_create = ["init", "flooding", "damages", "exposure", "population", "downloads"]
    base = os.path.join(os.getenv("MOUNT_PATH"), project, key)
    paths = {i: os.path.join(base, i) for i in paths_to_create}
    paths['BASE'] = base
    return paths


def save_submission(data, submission_id):
    SUBMISSION_DIR = f"{os.getenv('MOUNT_PATH')}/submissions"
    if os.path.exists(os.path.join(SUBMISSION_DIR, submission_id)):
        os.remove(os.path.join(SUBMISSION_DIR, submission_id))
    with open(os.path.join(SUBMISSION_DIR, submission_id), 'wb') as f:
        f.write(data)


def initialize_paths(paths):
    for v in paths.values():
        if not os.path.exists(v):
            os.makedirs(v)


def get_data_output_urls(project, key):
    return {
        k: f'{os.getenv("HOST")}/get_data?type={k}&project={project}&key=${key}&format=tif' for k in DATA_OUTPUTS
    }


@app.route('/trigger', methods=["POST"])
async def trigger():
    PROJECT = request.form['project']
    KEY = request.form['key']
    SUBMISSION_ID = f'{PROJECT}_{KEY}'
    DATA = request.files['data'].read()
    paths = get_paths(PROJECT, KEY)

    r.delete(SUBMISSION_ID)

    r.hset(SUBMISSION_ID, mapping={
        "status": "STARTED",
        "tasks": ','.join(TASKS),
        "project": PROJECT,
        "key": KEY,
        "template": request.form['template']
    })

    save_submission(DATA, f'{SUBMISSION_ID}.zip')

    if CLEAN_SLATE:
        if os.path.exists(paths['BASE']):
            shutil.rmtree(paths['BASE'])

    initialize_paths(paths)

    with zipfile.ZipFile(io.BytesIO(DATA), 'r') as zip_ref:
        zip_ref.extractall(paths['init'])

    logging.info(paths)
    
    # Build COGs
    PIPELINE = {
        "COG": {
            "runner": async_runner,
            "args": (cog_generator(paths), SUBMISSION_ID, "COG", assert_done),
            "kwargs": {"tries": 2, "workers": 32}
        },

        "DAMAGES": {
            "runner": async_runner,
            "args": (damages_generator(paths), SUBMISSION_ID, "DAMAGES", assert_done),
            "kwargs": {"tries": 4, "workers": 16}
        },

        "EXPOSURE": {
            "runner": async_runner,
            "args": (exposure_generator(paths), SUBMISSION_ID, "EXPOSURE", assert_done),
            "kwargs": {"tries": 4, "workers": 16}
        },

        "POPULATION": {
            "runner": async_runner,
            "args": (population_generator(paths), SUBMISSION_ID, "POPULATION", assert_done),
            "kwargs": {"tries": 4, "workers": 16}
        },

        "ZARR_BUILD": {
            "runner": async_runner,
            "args": (zarr_build_generator(DATA_OUTPUTS, paths), SUBMISSION_ID, "ZARR_BUILD", assert_done),
            "kwargs": {"tries": 4, "workers": 4}
        },

        "AEV_DAMAGES": {
            "runner": async_runner,
            "args": (aev_generator(request.form['template'], 'AEV-Econ', request.form['rps'], paths, 'damages'), SUBMISSION_ID, "AEV_DAMAGES", assert_done),
            "kwargs": {"tries": 6, "workers": 4}
        },

        "AEV_POPULATION": {
            "runner": async_runner,
            "args": (aev_generator(request.form['template'], 'AEV-Pop', request.form['rps'], paths, 'population'), SUBMISSION_ID, "AEV_POPULATION", assert_done),
            "kwargs": {"tries": 6, "workers": 4}
        },

        "ZARR2PT": {
            "runner": async_runner,
            "args": (zarr2pt_generator(paths, DATA_OUTPUTS), SUBMISSION_ID, "ZARR2PT", assert_done),
            "kwargs": {"tries": 3, "workers": 4}
        },

        "PMTILES": {
            "runner": async_runner,
            "args": (pmtiles_generator(paths, DATA_OUTPUTS, os.path.join(PROJECT, KEY)), SUBMISSION_ID, "PMTILES", assert_done),
            "kwargs": {"tries": 2, "workers": 4}
        },
    }

    PIPELINE = {
        k: v for k, v in PIPELINE.items() if k in TASKS
    }

    for task, spec in PIPELINE.items():
        runner = spec['runner']
        if runner == async_runner:
            await runner(
                *spec['args'],
                **spec['kwargs']
            )

    r.hset(SUBMISSION_ID, mapping={
        "downloads": json.dumps(get_data_output_urls(PROJECT, KEY))
    })

    return ("Complete", 200)


@app.get('/mosaic')


@app.get('/backfill')
def backfill():
    import requests, os, argparse
    from requests_toolbelt import MultipartEncoder

    template = 'WaterDepth_${clim}_${scen}_Tr{rp}_t33'
    projects = [i for i in os.listdir(os.getenv("MOUNT_PATH")) if i != 'submissions']

    for p in projects:
        keys = ["DOM_01"]
        # keys = os.listdir(os.path.join(os.getenv("MOUNT_PATH"), p))
        for k in keys:
            files = {'data': open(os.path.join(os.getenv("MOUNT_PATH"), 'submissions', f'{p}_{k}.zip'), 'rb')}
            response = requests.post(
                f'{os.getenv("HOST")}/trigger', data={
                    'key': k,
                    'project': p,
                    'template': template,
                    'rps': "10,25,50,100",
                }, files=files
            )
            if response.status_code == 500:
                # return ("failed", 500)
                continue
    
    return ("complete", 200)


@app.route('/status', methods=["GET"])
def get_status():
    keys = r.keys()
    logging.info(keys)
    return {k: r.hgetall(k) for k in keys}


@app.route('/get_tasks', methods=['GET'])
def get_tasks():
    return TASKS


@app.route('/get_downloads', methods=['GET'])
def get_downloads():
    PROJECT = request.args.get('project')
    KEY = request.args.get('key')
    return get_data_output_urls(PROJECT, KEY)


@app.route('/get_data', methods=["GET"])
async def get_data():
    logging.info(request.args)

    data_type = request.args.get('type')
    PROJECT = request.args.get('project')
    KEY = request.args.get('key')
    FORMAT = request.args.get('format')
    
    paths = get_paths(PROJECT, KEY)
    download_dir = paths['downloads']
    input_path = paths[data_type]
    input_zarr = f'{data_type}.zarr'
    zarr = os.path.join(input_path, input_zarr)

    def is_file_being_written(filepath, interval=1):
        initial_size = os.path.getsize(filepath)
        time.sleep(interval)
        new_size = os.path.getsize(filepath)
        return initial_size != new_size

    def compute_and_cache(f, p, args):
        if os.path.exists(p):
            while is_file_being_written(p):
                continue 
                
        else:
            f(*args)
    
    if FORMAT == "nc":
        url = f'{os.getenv("HOST")}/zarr_to_netcdf/'
        output = os.path.join(download_dir, f'{data_type}.nc')

        def f( url, zarr, output): 
            requests.post(url, data={"zarr": zarr, "output": nc})
            return flask.send_from_directory(download_dir, f'{data_type}.nc')
        
        return return_with_cache(f, p, [url, zarr, output])

    elif FORMAT == "tif":
        url = f'{os.getenv("HOST")}/zarr_to_tiff/'
        archive_dir = os.path.join(download_dir, "tifs", data_type)
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)
        
        tiff_zip = os.path.join(download_dir, f"{data_type}.zip")

        def f(url, zarr, archive_dir):
            requests.post(url, data={"zarr": zarr, "output": archive_dir})
            shutil.make_archive(os.path.join(download_dir, data_type), 'zip', archive_dir, archive_dir)

        compute_and_cache(f, tiff_zip, [url, zarr, archive_dir])
        return flask.send_from_directory(download_dir, f"{data_type}.zip")
        
    else:
        shutil.make_archive(os.path.join(download_dir, data_type), 'zip', zarr, zarr)
        return flask.send_from_directory(download_dir, f'{data_type}.zip')


@app.get("/")
def test():
    return "OK"

from pipelines.main import pipeline_runner
pipeline_runner(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
