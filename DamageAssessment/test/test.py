import os, requests, logging


logging.basicConfig()
logging.root.setLevel(logging.INFO)

HOST = os.getenv("HOST")
DATADIR = os.getenv("DATA_FOLDER")

def test_dollar_apply():
    data = f'/app/data/NBS_ADAPTS/test/damages'
    x = requests.post(f'{HOST}/damage/apply_dollar_weights/', 
        json = {
            "input": data,
            "output": f'/app/data/NBS_ADAPTS/test/damages_scaled'
        })
    logging.info(x)