import os, io
from cloudevents.http import from_http
from flask import Flask, request
from google.events.cloud.storage import StorageObjectData
import logging
from google.cloud import storage
import uuid
import subprocess
import requests
import threading
import rioxarray as rxr
import xarray as xr
from utils.datastore import add_entity, get_managed_assets
from utils.gcs import download_blob, upload_blob, list_blobs
from utils.dataset import compressRaster

import json
import zarr
from glob import glob

import asyncio, concurrent

from rioxarray.merge import merge_arrays, merge_datasets


logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)


def to_cog(inpath, outpath):
    bashCommand = f"gdalwarp {inpath} {outpath} -of COG"
    process = subprocess.Popen(bashCommand.split(' '), stdout=subprocess.PIPE)
    logging.info('Preparing COG')
    while True:
        line = process.stdout.readline()
        if not line: break
        print(line, flush=True)
    return outpath


@app.route("/build_COG/from_gcs/", methods=["POST"])
def build_cog_managed():
    """Handle tile requests."""
    # event = from_http(request.headers, request.get_data())
    logging.info(request.form)
    # logging.info(request.get_json())
    # logging.info(type(request.get_json()))
    # logging.info(request.get_json().decode())
    # logging.info(type(request.get_data().decode()))
    data = request.get_json()
    id = str(uuid.uuid1())
    tmp = f'/tmp/{id}.tif'
    tmp_cog = f'/tmp/{id}_cog.tif'
    download_blob(data['bucket'], data['name'], tmp)
    to_cog(tmp, tmp_cog)
    upload_blob(os.environ['OUTPUT_BUCKET'], tmp_cog, data['name'])
    logging.info('Done')
    return (
        f"Completed",
        200,
    )


@app.route("/build_COG/", methods=["POST"])
def build_cog():
    id = str(uuid.uuid1())
    tmp = f'/tmp/{id}.tif'
    tmp_cog = f'/tmp/{id}_cog.tif'
    data = rxr.open_rasterio(
        io.BytesIO(request.files['data'].read())
    ).isel(band=0)
    compressRaster(data, request.form['output'])
    
    return (
        f"Completed",
        200,
    )


def jsonKeys2int(x):
    if isinstance(x, dict):
        return {int(k):v for k,v in x.items()}
    return x


def create_dimensions(ds, id):
    return ds.rename(id)


@app.route("/build_zarr/", methods=["POST"])
def build_zarr():
    id = str(uuid.uuid1())
    tmp = f'/tmp/{id}.tif'
    tmp_cog = f'/tmp/{id}_cog.tif'

    is_gcs = "gcs_directory" in request.form
    if is_gcs:
        path = request.form['gcs_directory'].replace('gs://', '').split('/')
        bucket = path[0]
        prefix = '/'.join(path[1:])
        blobs = list_blobs(bucket, prefix)
        blobs = [b for b in blobs if len(b.split('/')) == len(path[1:]) + 1 if ".tif" in b]
        print(blobs)

        rasters = [
            {
                'ds': rxr.open_rasterio(
                    f'gs://{bucket}/{b}'
                ).isel(band=0), 
                'id': b.split('/')[-1].split('.')[0]
            } for b in blobs
        ]
        data = [
            create_dimensions(d['ds'], d['id'])
            for d in rasters
        ]
        data = xr.merge(data).chunk(500).assign_attrs(crs=str(rasters[0]['ds'].rio.crs))
        data.to_zarr(f'gs://{bucket}/{prefix}/{request.form["output"]}')
        return ("complete", 200)
    
    else:
        blobs = glob(os.path.join(request.form['local_directory'], "*.tif"))
        logging.info(blobs)

        rasters = [
            {
                'ds': rxr.open_rasterio(b).isel(band=0), 
                'id': b.split('/')[-1].split('.')[0]
            } for b in blobs
        ]
        data = [
            create_dimensions(d['ds'], d['id'])
            for d in rasters
        ]
        data = xr.merge(data).chunk(500).assign_attrs(crs=str(rasters[0]['ds'].rio.crs))
        data.to_zarr(os.path.join(request.form['local_directory'], request.form["output"]))
        return ("complete", 200)


@app.route("/zarr_to_netcdf/", methods=["POST"])
def zarr_to_netcdf():
    zarr_dataset = xr.open_zarr(request.form['zarr'])
    compression_settings = {
        var: {
            'zlib': True,
            'complevel': 5  # Compression level (1-9)
        } for var in zarr_dataset.data_vars
    }
    logging.info(zarr_dataset.rio)
    zarr_dataset.sortby(["y", "x"])
    zarr_dataset.rio.write_grid_mapping(inplace=True)
    zarr_dataset.rio.write_crs(zarr_dataset.rio.crs, inplace=True)
    zarr_dataset.to_netcdf(request.form['output'], encoding=compression_settings, engine='h5netcdf')
    return ("complete", 200)


@app.route("/zarr_to_tiff/", methods=["POST"])
async def zarr_to_tiff():
    zarr_dataset = xr.open_zarr(request.form['zarr'])
    logging.info(zarr_dataset.data_vars)

    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:

        tasks = []
        for var in zarr_dataset.data_vars:
            if var in ["spatial_ref"]:
                continue
            ds = zarr_dataset[var]
            try: 
                del ds.attrs['grid_mapping']
            except:
                pass
            ds.rio.write_grid_mapping(inplace=True)
            ds.rio.write_crs(zarr_dataset.rio.crs, inplace=True)
            tasks.append(loop.run_in_executor(executor, compressRaster, ds, os.path.join(request.form['output'], f'{var}.tif')))
        responses = await asyncio.gather(*tasks)
        
    return ("complete", 200)



@app.route("/", methods=["POST"])
def index():
    """Handle tile requests."""
    def request_task(url, json):
        requests.post(url, json=json)

    def fire_and_forget(url, json):
        threading.Thread(target=request_task, args=(url, json)).start()

    try:
        event = from_http(request.headers, request.get_data())
        logging.info(request.get_data())
        logging.info(event.data['id'])

        # Gets the GCS bucket name from the CloudEvent data
        # Example: "storage.googleapis.com/projects/_/buckets/my-bucket"
        # try:
        gcs_object = os.path.join(event.data['bucket'], event.data['name'])
        logging.info(gcs_object)
        logging.info(os.environ['FORWARD_SERVICE'])
        fire_and_forget(
            f"{os.environ['FORWARD_SERVICE']}/{os.environ['FORWARD_PATH']}", 
            json={
                'bucket':event.data['bucket'],
                'name': event.data['name']
            }
        )

        return (
            f"Forwarded to {os.environ['FORWARD_SERVICE']}",
            200,
        )
    except:
        return (
            f"Something went wrong, but returning 200 to prevent PubSub infinite retries",
            200,
        )

@app.get('/')
def test():
    return 'OK'


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
