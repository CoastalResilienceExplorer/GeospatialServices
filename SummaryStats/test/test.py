import os, requests, logging


logging.basicConfig()
logging.root.setLevel(logging.INFO)

HOST = os.getenv("HOST")
GEOGS = '/users/chlowrie/TestData/dom_subunits.gpkg'

def test_summary_stats():
    files = {
        "geographies": open(GEOGS, 'rb')
    }
    data = {
        'project': 'NBS_ADAPTS',
        'key': 'DOM_merged_test',
        'data_type': 'flooding'
    }
    x = requests.post(f'{HOST}/summary_stats/', data=data, files=files)
    logging.info(x)