import os
import logging
import uuid
import threading
import requests
from cloudevents.http import from_http
from flask import Flask, request
from google.cloud import storage
import geopandas as gpd
import subprocess

logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)

def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The ID of your GCS object
    # source_blob_name = "storage-object-name"

    # The path to which the file should be downloaded
    # destination_file_name = "local/path/to/file"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    # Construct a client side representation of a blob.
    # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
    # any content from Google Cloud Storage. As we don't need additional data,
    # using `Bucket.blob` is preferred here.
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    logging.info(
        "Downloaded storage object %s from bucket %s to local file %s.", 
        source_blob_name, bucket_name, destination_file_name
    )


def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"
    # The path to your file to upload
    # source_file_name = "local/path/to/file"
    # The ID of your GCS object
    # destination_blob_name = "storage-object-name"

    logging.info(
        "Uploading file %s to bucket %s as %s.",
        source_file_name, bucket_name, destination_blob_name
    )

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Optional: set a generation-match precondition to avoid potential race conditions
    # and data corruptions. The request to upload is aborted if the object's
    # generation number does not match your precondition. For a destination
    # object that does not yet exist, set the if_generation_match precondition to 0.
    # If the destination object already exists in your bucket, set instead a
    # generation-match precondition using its generation number.
    # generation_match_precondition = 0
    logging.info("Uploading.")
    blob.upload_from_filename(
        source_file_name,
        # if_generation_match=generation_match_precondition
    )

    logging.info(
        "File %s uploaded to %s.",
        source_file_name, destination_blob_name
    )


@app.route("/", methods=["POST"])
def geoparquet_to_mbtiles():
    """Handle tile requests."""
    logging.info(request.get_json())
    data = request.get_json()
    file = f"gs://{data['bucket']}/{data['name']}"
    x = gpd.read_parquet(file)
    # tmp_id = str(uuid.uuid1())
    tmp_id = data["name"].split('/')[-1].split('.')[0]
    tmp_file = f'/tmp/{tmp_id}.geojson'
    tmp_pmtiles = f'/tmp/{tmp_id}.pmtiles'
    logging.info(x)
    x.to_file(tmp_file)

    tippecanoe_command = f"tippecanoe -o {tmp_pmtiles} --drop-rate=0.1 --no-feature-limit --no-tile-size-limit {tmp_file}"
    process = subprocess.Popen(tippecanoe_command.split(' '), stdout=subprocess.PIPE)
    logging.info('Running tippecanoe')
    while True:
        line = process.stdout.readline()
        if not line: break
        print(line, flush=True)
    upload_blob(os.environ['OUTPUT_BUCKET'], tmp_pmtiles, os.path.splitext(data['name'])[0] + '.pmtiles')
    return ("Completed", 200)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
