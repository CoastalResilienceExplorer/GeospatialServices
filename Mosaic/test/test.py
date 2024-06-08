import requests, os


ENDPOINT="http://localhost:4000/mosaic"
PROJECT="NBS_ADAPTS"
KEY1="DOM_01"
KEY2="DOM_02"
data_type="flooding"

requests.post(ENDPOINT, data={
    "zarr1": os.path.join(PROJECT, KEY1, data_type, f"{data_type}.zarr"),
    "zarr2": os.path.join(PROJECT, KEY2, data_type, f"{data_type}.zarr")
})