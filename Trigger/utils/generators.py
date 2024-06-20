import os, requests
import numpy as np
from glob import glob

import asyncio
import requests
import concurrent

from utils.redis import r
import time

import logging
logging.basicConfig()
logging.root.setLevel(logging.INFO)

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
    return np.all(x)


def dummy_return_true():
    return 200


async def async_runner(generator, id, task, pass_assertion, tries=3, workers=10, incremental_retry=True):

    data = [i for i in generator()]
    idxs = [False for i in data]
    r.hset(id, mapping={task: "STARTED"})
    async def do_work(data):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            tasks = []
            for i in data:
                tasks.append(loop.run_in_executor(executor, *i))
            responses = await asyncio.gather(*tasks)
        return responses

    failures = 0
    for _ in range(tries):
        if failures > 0:
            r.hset(id, mapping={task: f"RETRYING: {failures}"})
            time.sleep(2)
        
        data = [i for idx, i in enumerate(data) if not idxs[idx]]
        logging.info(data)
        responses = await do_work(data)
        logging.info(responses)
        idxs = [idx == 200 for i, idx in enumerate(responses)]
        logging.info(idxs)
        if pass_assertion(idxs):
            r.hset(id, mapping={task: "COMPLETE"})
            break
        
        failures += 1
        if failures >= tries:
            r.hset(id, mapping={task: "FAILED"})
            break


def cog_generator(paths):

    def f():
        url=f'{os.getenv("HOST")}/build_COG/'        
        for f in glob(os.path.join(paths['init'], "*.tif")):
            files = {'data': open(f, 'rb')}
            fname = f.split('/')[-1]
            data = {
                "output": os.path.join(paths['flooding'], fname)
            }
            yield (post, url, data, files)
    
    return f



def damages_generator(paths, params={"window_size": 100, "population_min": 1}):

    def f():
        url=f'{os.getenv("HOST")}/damage/dlr_guf/'      
        for f in glob(os.path.join(paths['flooding'], '*.tif')):
            files = {'flooding': open(os.path.join(paths['flooding'], f), 'rb')}
            output = os.path.join(paths['damages'], f.split('/')[-1])
            url=f'{os.getenv("HOST")}/damage/dlr_guf/'
            yield (post, url, params, files, output)
    
    return f


def exposure_generator(paths):

    def f():
        url=f'{os.getenv("HOST")}/damage/dlr_guf/exposure'   
        for f in glob(os.path.join(paths['flooding'], '*.tif')):
            # files = {'flooding': open(os.path.join(paths['flooding'], f), 'rb')}
            output = os.path.join(paths['exposure'], f.split('/')[-1])
            data = dict(flooding=os.path.join(paths['flooding'], f))
            yield (post, url, data, None, output)
    
    return f


def population_generator(paths, params={"threshold": 0.1}):

    def f():
        url=f'{os.getenv("HOST")}/population/GHSL_2020_100m/'   
        for f in glob(os.path.join(paths['flooding'], '*.tif')):
            files = {'flooding': open(os.path.join(paths['flooding'], f), 'rb')}
            output = os.path.join(paths['population'], f.split('/')[-1])
            data = dict(flooding=os.path.join(paths['flooding'], f))
            yield (post, url, {**params, **data}, None, output)
    
    return f


def zarr_build_generator(to_run, paths):

    def f():
        url=f'{os.getenv("HOST")}/build_zarr/'
        for i in to_run:
            data = {
                "local_directory": paths[i],
                "output": f"{i}.zarr",
            }
            yield (post, url, data, None)
    
    return f


def aev_generator(template, id_prefix, rps, paths, data_type):

    from string import Template
    import itertools
    _template = Template(template)
    url=f'{os.getenv("HOST")}/aev/'

    def f():
        scenario_parse = [i.split('/')[-1].split('.')[0].split('_') for i in glob(os.path.join(paths['damages'], '*.tif'))]
        scenarios = dict()
        for idx, k in enumerate(template.split('_')):
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
            formatter = _template.safe_substitute(values)
            logging.info(formatter)

            id = id_prefix + '_' + '_'.join(values.values())
            data = {
                "formatter": formatter,
                "damages": paths[data_type],
                "output": paths[data_type],
                "id": id,
                "rps": rps
            }
            yield (post, url, data, None)
    
    return f


def apply_dollar_weights_generator(paths, data_type):

    url=f'{os.getenv("HOST")}/damage/apply_dollar_weights/'

    def f():
        for i in glob(os.path.join(paths[data_type], f"*.tif")):
            fname = i.split('/')[-1]
            data = {
                "input": i,
                "output": os.path.join(paths['damages_scaled'], fname)
            }
            yield (post_json, url, data)
    
    return f


def zarr2pt_generator(paths, to_run):
    url=f'{os.getenv("HOST")}/zarr2pt/'

    def f():
        for i in to_run:
            data = {
                "data": paths[i],
                "output": os.path.join(paths[i], f"{i}.parquet")
            }
            yield (post_json, url, data)

    return f


def pmtiles_generator(paths, to_run, output_base):

    url=f'{os.getenv("HOST")}/create_pmtiles/'

    def f():
        for i in to_run:
            data = {
                "input": os.path.join(paths[i], f"{i}.parquet"),
                "output": os.path.join(output_base, f"{i}.pmtiles"),
                "use_id": "fid"
            }
            yield (post_json, url, data)
    
    return f

def mosaic_generator(project1, key1, project2, key2, data_type, project, key):
    url=f'{os.getenv("HOST")}/mosaic/'
    for i in os.listdir(os.path.join(os.getenv("MOUNT_PATH"), project1, key1, 'flooding')):
        fname = i.split('/')[-1].split('.')[0]
        if i.split('/')[-1].split('.')[-1] != 'tif':
            continue
        data = {
            "zarr1": os.path.join(project1, key1, data_type, f"{data_type}.zarr"),
            "zarr2": os.path.join(project2, key2, data_type, f"{data_type}.zarr"),
            "output_dir": os.path.join(project, key, data_type),
            "var": fname
        }
        yield (post, url, data, None)
    

def cog_generator2(paths):
    url=f'{os.getenv("HOST")}/build_COG/'        
    logging.info('paths')
    for f in glob(os.path.join(paths['init'], "*.tif")):
        files = {'data': open(f, 'rb')}
        fname = f.split('/')[-1]
        data = {
            "output": os.path.join(paths['flooding'], fname)
        }
        yield (post, url, data, files)

def zarr_build_generator2(paths, to_run=['flooding']):
    url=f'{os.getenv("HOST")}/build_zarr/'
    for i in to_run:
        data = {
            "local_directory": paths[i],
            "output": f"{i}.zarr",
        }
        yield (post, url, data, None)
        
# def summary_stats_generator(paths, files, project, key, to_run=['flooding', 'damages_scaled', 'population']):
def summary_stats_generator(paths, files, project, key, to_run=['flooding']):
    url=f'{os.getenv("HOST")}/summary_stats/'
    for i in to_run:
        data = {
            "input": paths[i],
            "project": project,
            "key": key
        }
        yield (post, url, data, files, None)


async def async_runner2(id, task, generator, kwargs, pass_assertion=assert_done, tries=3, workers=10, incremental_retry=True):

    data = [i for i in generator(**kwargs)]
    # logging.info(data)
    idxs = [False for i in data]
    r.hset(id, mapping={task: "STARTED"})
    async def do_work(data):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            tasks = []
            for i in data:
                tasks.append(loop.run_in_executor(executor, *i))
            responses = await asyncio.gather(*tasks)
        return responses

    failures = 0
    for _ in range(tries):
        if failures > 0:
            r.hset(id, mapping={task: "RETRYING"})

        if failures >= tries:
            r.hset(id, mapping={task: "FAILED"})
            break
        
        data = [i for idx, i in enumerate(data) if not idxs[idx]]
        responses = await do_work(data)
        idxs = [idx == 200 for i, idx in enumerate(responses)]
        if pass_assertion(idxs):
            r.hset(id, mapping={task: "COMPLETE"})
            break
        
        failures += 1