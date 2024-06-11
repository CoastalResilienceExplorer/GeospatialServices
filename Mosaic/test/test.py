import requests, os


ENDPOINT=f'{os.getenv("HOST")}/mosaic/'
print(ENDPOINT)
PROJECT="NBS_ADAPTS"
KEY1="DOM_01"
KEY2="DOM_02"
OUTPUT="DOM"
data_type="flooding"

requests.post(ENDPOINT, data={
    "zarr1": os.path.join(PROJECT, KEY1, data_type, f"{data_type}.zarr"),
    "zarr2": os.path.join(PROJECT, KEY2, data_type, f"{data_type}.zarr"),
    "output_dir": os.path.join(PROJECT, OUTPUT, data_type),
    "var": "WaterDepth_Historic_S3_Tr100_t33"
})