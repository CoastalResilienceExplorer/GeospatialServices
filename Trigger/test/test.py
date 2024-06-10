import requests, os
import logging
import json

ENDPOINT=f"{os.getenv('HOST')}/pipeline"

def test_ingest():
    PROJECT="NBS_ADAPTS"
    KEY="DOM_01_test"
    args = json.dumps({
        "INGEST": dict(),
        "ZARR_BUILD": dict(to_run=["flooding"])
    })
    data = os.path.join(
        os.getenv("DATA_FOLDER"),
        "submissions", 
        "NBS_ADAPTS_DOM_01.zip"
    )
    
    files = {'data': open(data, 'rb')}
    response = requests.post(
        ENDPOINT, data={
            'project': PROJECT,
            'key': KEY,
            'args': args, 
            'tasks': "INGEST"
        },
        files=files
    )
    logging.info(response)
    
    
def test_mosaic():
    PROJECT="NBS_ADAPTS"
    KEY="DOM"
    args = json.dumps({
        "MOSAIC": {
            "project1": "NBS_ADAPTS",
            "project2": "NBS_ADAPTS",
            "key1": "DOM_01_test",
            "key2": "DOM_02_test",
            "data_type": "flooding",
            "key2": "DOM_02_test",
        },
        "ZARR_BUILD": dict(to_run=["flooding"])
    })
    response = requests.post(
        ENDPOINT, data={
            'project': PROJECT,
            'key': KEY,
            'args': args, 
            'tasks': "MOSAIC"
        }
    )
    logging.info(response)


test_mosaic()
# test_ingest()