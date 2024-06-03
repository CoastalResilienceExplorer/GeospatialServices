import flask
from flask import Flask, request
import zipfile
import os, io
import aiohttp
import asyncio
import requests
import concurrent
import numpy as np
import shutil
from glob import glob

import logging
logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)

def post(url, data, files, write_content=False):
    with requests.post(url, data=data, files=files) as response:
        if write_content:
            with open(write_content, 'wb') as f:
                f.write(response.content)
        return response.status_code
    

def post_json(url, json, write_content=False):
    with requests.post(url, json=json, headers={"Content-Type": "application/json"}) as response:
        if write_content:
            with open(write_content, 'wb') as f:
                f.write(response.content)
        return response.status_code


def assert_done(x):
    return np.all([i == 200 for i in x])

CLEAN_SLATE = True
SKIP_TASKS = [
    "COG", 
    "DAMAGES",
    "ZARR_BUILD",
    "AEV",
    "ZARR2PT",
    # "PMTILES"
]

if CLEAN_SLATE:
    SKIP_TASKS = ["COG"]


@app.route('/trigger', methods=["POST"])
async def trigger():
    logging.info(request.form)

    PROJECT = request.form['project']
    KEY = request.form['key']

    if CLEAN_SLATE:
        if os.path.exists(os.path.join('/app/data', PROJECT, KEY)):
            shutil.rmtree(os.path.join('/app/data', PROJECT, KEY))

    init_path = os.path.join('/app/data', PROJECT, KEY, 'init')
    if not os.path.exists(init_path):
        os.makedirs(init_path)

    cogpath = os.path.join('/app/data', PROJECT, KEY, 'cog')
    if not os.path.exists(cogpath):
        os.makedirs(cogpath)
    remote_cogpath = os.path.join(PROJECT, KEY, "flooding")

    damagespath = os.path.join('/app/data', PROJECT, KEY, 'damages')
    if not os.path.exists(damagespath):
        os.makedirs(damagespath)
    remote_damagespath = os.path.join(PROJECT, KEY, "damages")
    
    with zipfile.ZipFile(io.BytesIO(request.files['data'].read()), 'r') as zip_ref:
        zip_ref.extractall(init_path)
    
    # Build COGs
    if "COG" not in SKIP_TASKS:
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
            tasks = []
            for f in os.listdir(init_path):
                files = {'data': open(os.path.join(init_path, f), 'rb')}
                data = {
                    "name": os.path.join(remote_cogpath, f)
                }
                url=f'{os.getenv("HOST")}/build_COG/'
                tasks.append(loop.run_in_executor(executor, post, url, data, files))
            responses = await asyncio.gather(*tasks)
        if not assert_done(responses):
            return ("Failure", 500)


    # Damages
    if "DAMAGES" not in SKIP_TASKS: 
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            tasks = []
            for f in os.listdir(init_path):
                files = {'flooding': open(os.path.join(init_path, f), 'rb')}
                data = {
                    "output_to_gcs": os.path.join(remote_damagespath, f)
                }
                url=f'{os.getenv("HOST")}/damage/dlr_guf/'
                tasks.append(loop.run_in_executor(executor, post, url, data, files, os.path.join(damagespath, f)))
            responses = await asyncio.gather(*tasks)
        logging.info(responses)
        if not assert_done(responses):
            return ("Failure", 500)

    # Damages Zarr
    if "ZARR_BUILD" not in SKIP_TASKS:
        data = {
            "local_directory": damagespath,
            "output": "damages.zarr",
        }
        url=f'{os.getenv("HOST")}/build_zarr/'
        res = requests.post(url, data=data)
        if res.status_code != 200:
            return ("Failure", 500)
        
        # Flooding Zarr
        data = {
            "local_directory": init_path,
            "output": "flooding.zarr",
        }
        url=f'{os.getenv("HOST")}/build_zarr/'
        res = requests.post(url, data=data)
        if res.status_code != 200:
            return ("Failure", 500)
        

    if "AEV" not in SKIP_TASKS:
        from string import Template
        import itertools
        # Damages AEV
        loop = asyncio.get_running_loop()
        template = Template(request.form['template'])
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            tasks = []
            scenario_parse = [i.split('/')[-1].split('_') for i in glob(os.path.join(damagespath, '*.tif*'))]
            scenarios = dict()
            for idx, k in enumerate(request.form['template'].split('_')):
                if "$" in k:
                    scenarios[k.replace("$", "").replace('{', '').replace('}', '')] = list(set([i[idx] for i in scenario_parse]))
            # Extract keys and values
            keys = scenarios.keys()
            values = scenarios.values()

            # Compute the Cartesian product of the values
            cross_product = itertools.product(*values)

            # Construct the list of dictionaries
            scenarios = [dict(zip(keys, items)) for items in cross_product]
            for values in scenarios:
                formatter = template.safe_substitute(values)
                logging.info(formatter)
                damages_zarr = os.path.join(damagespath, "damages.zarr")
                id = '_'.join(values.values()) + '_AEV_damages'
                data = {
                    "formatter": formatter,
                    "damages_zarr": damages_zarr,
                    "id": id,
                    "rps": request.form['rps']
                }
                url=f'{os.getenv("HOST")}/damage/dlr_guf/aev/'
                tasks.append(loop.run_in_executor(executor, post, url, data, None))
            responses = await asyncio.gather(*tasks)
        logging.info(responses)
        if not assert_done(responses):
            return ("Failure", 500)
        

    if "ZARR2PT" not in SKIP_TASKS:
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            tasks = []
            to_run = {
                'flooding': init_path,
                'damages': damagespath
            }
            for d in to_run.keys():
                url=f'{os.getenv("HOST")}/zarr2pt/'
                data = {
                    "data": os.path.join(to_run[d], f"{d}.zarr"),
                    "output": os.path.join(to_run[d], f"{d}.parquet")
                }
                tasks.append(loop.run_in_executor(executor, post_json, url, data))
            responses = await asyncio.gather(*tasks)
            if not assert_done(responses):
                return ("Failure", 500)
        
        
    if "PMTILES" not in SKIP_TASKS:
        # Flooding Zarr
        url=f'{os.getenv("HOST")}/create_pmtiles/'
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            to_run = {
                    'flooding': init_path,
                    'damages': damagespath
            }
            tasks = []
            for d in to_run.keys():
                data = {
                    "bucket": "geopmaker-output-staging",
                    "input": os.path.join(to_run[d], f"{d}.parquet"),
                    "output": os.path.join(PROJECT, KEY, f"{d}.pmtiles"),
                    "use_id": "fid"
                }
                tasks.append(loop.run_in_executor(executor, post_json, url, data))
            responses = await asyncio.gather(*tasks)
            if not assert_done(responses):
                return ("Failure", 500)
    
    return ("Complete", 200)
    


@app.get("/")
def test():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
