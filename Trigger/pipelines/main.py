import flask
from flask import Flask, request
import json
import numpy as np
from utils.setup import setup
import inspect
import zipfile, io
import uuid
import os

import logging
logging.basicConfig()
logging.root.setLevel(logging.INFO)

from utils.generators import async_runner2, \
    cog_generator2, \
    zarr_build_generator2, \
    mosaic_generator, \
    summary_stats_generator


MOSAIC = [ 
    {
        "id": "MOSAIC",
        "runner": async_runner2,
        "generator": mosaic_generator,
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
]

SUMMARYSTATS = [
    {
        "id": "SUMMARYSTATS",
        "runner": async_runner2,
        "generator": summary_stats_generator,
        "runner_kwargs": {"tries": 2, "workers": 2}
    },
]
    
PIPES = {
    "INGEST": INGEST, 
    "MOSAIC": MOSAIC,
    "SUMMARYSTATS": SUMMARYSTATS
}

def pipeline_runner(app):
    
    @app.route('/pipeline', methods=["POST"])
    async def _run_pipeline():
        PROJECT = request.form['project']
        KEY = request.form['key']
        SUBMISSION_ID = f'{PROJECT}_{KEY}'
        TASKS = request.form['tasks'].split(',')
        logging.info(request.form)
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
            # logging.info(arg_names)
            new_args = {
                k: potential_runtime_args[k] for k in arg_names if k in potential_runtime_args
            }
            
            user_args = args[p['id']]
            
            files_to_add = None
            if "files" in user_args:
                files_to_add = {
                    k: request.files[k] for k in user_args.pop('files')
                }
                fid = str(uuid.uuid4())
                outpath = os.path.join('/tmp', fid)
                os.makedirs(outpath)
                
                files_to_add_buff = dict()
                for k, v in files_to_add.items():
                    path = os.path.join(outpath, v.filename.split('/')[-1])
                    with open(path, 'wb') as f:
                        f.write(v.read())
                    files_to_add_buff[k] = open(path, 'rb')
                files_to_add = files_to_add_buff
                
            # logging.info(user_args)
            new_args = {
                **user_args,
                **new_args
            }
            if files_to_add:
                new_args['files'] = files_to_add
            logging.info(new_args)
                
            # logging.info(files_to_add)
                
            new_pipe = p
            logging.info(new_pipe)
            
            new_pipe['kwargs'] = new_args
            new_pipeline.append(new_pipe)
            
        # logging.info(new_pipeline)
        # return ("complete", 200)
        
        for spec in new_pipeline:
            # logging.info(spec)
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
        
    
