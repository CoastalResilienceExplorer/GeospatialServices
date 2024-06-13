import flask
from flask import Flask, request
import json
import numpy as np
from utils.setup import setup
import inspect
import zipfile, io

import logging
logging.basicConfig()
logging.root.setLevel(logging.INFO)

from utils.generators import async_runner2, \
    cog_generator2, \
    zarr_build_generator2, \
    mosaic_generator


MOSAIC = [ 
    {
        "id": "MOSAIC",
        "runner": async_runner2,
        "generator": mosaic_generator,
        "runner_kwargs": {"tries": 2, "workers": 32}
    },
    {
        "id": "ZARR_BUILD",
        "runner": async_runner2,
        "generator": zarr_build_generator2,
        "runner_kwargs": {"tries": 2, "workers": 32}
    },
]
    
INGEST = [
    {
        "id": "INGEST",
        "runner": async_runner2,
        "generator": cog_generator2,
        "runner_kwargs": {"tries": 2, "workers": 32}
    },
    {
        "id": "ZARR_BUILD",
        "runner": async_runner2,
        "generator": zarr_build_generator2,
        "runner_kwargs": {"tries": 2, "workers": 32}
    }
]
    
PIPES = {
    "INGEST": INGEST, 
    "MOSAIC": MOSAIC
}

def pipeline_runner(app):
    
    @app.route('/pipeline', methods=["POST"])
    async def _run_pipeline():
        PROJECT = request.form['project']
        KEY = request.form['key']
        SUBMISSION_ID = f'{PROJECT}_{KEY}'
        TASKS = request.form['tasks'].split(',')
        args = json.loads(request.form['args'])
        logging.info(args)
        paths = setup(SUBMISSION_ID, PROJECT, KEY, TASKS)
        
        if 'data' in request.files:
            logging.info(request.files)
            with zipfile.ZipFile(io.BytesIO(request.files['data'].read()), 'r') as zip_ref:
                zip_ref.extractall(paths['init'])
        
        potential_runtime_args = {
            "paths": paths,
            "project": PROJECT,
            "key": KEY
        }
        
        pipeline = list(np.array([PIPES[i] for i in TASKS]).flatten())
        new_pipeline = []
        for p in pipeline:
            sig = inspect.signature(p['generator'])
            arg_names = [param.name for param in sig.parameters.values()]
            logging.info(arg_names)
            new_args = {
                k: potential_runtime_args[k] for k in arg_names if k in potential_runtime_args
            }
            new_args = {
                **args[p['id']],
                **new_args
            }
            new_pipe = p
            new_pipe['kwargs'] = new_args
            new_pipeline.append(new_pipe)
            
        logging.info(new_pipeline)
        # return ("complete", 200)
        
        for spec in new_pipeline:
            logging.info(spec)
            runner = spec['runner']
            if runner == async_runner2:
                await runner(
                    SUBMISSION_ID,
                    spec['id'],
                    spec['generator'],
                    spec['kwargs'],
                    **spec['runner_kwargs']
                )
        
        return ("complete", 200)
        
    
