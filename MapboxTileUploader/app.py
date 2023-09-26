import os
import logging
import uuid
import threading
import requests
from cloudevents.http import from_http
from flask import Flask, request
from google.cloud import storage
import geopandas as gpd

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


@app.route("/mapbox_upload/", methods=["POST"])
def upload_to_map():
    """Handle tile requests."""
    logging.info(request.get_json())
    logging.info(type(request.get_json()))
    data = request.get_json()
    tmp_id = str(uuid.uuid1())
    _, extension = os.path.splitext(data['name'])
    tmp_parquet = f'/tmp/{tmp_id}.{extension[1:]}'
    download_blob(data['bucket'], data['name'], tmp_parquet)
    try:
        # Convert to GeoJSON
        logging.info('Converting to GeoJSON')
        gdf = gpd.read_parquet(tmp_parquet)
        tmp_geojson = f'/tmp/{tmp_id}.geojson'
        gdf.to_json(tmp_geojson)
        
        
        # Create a Mapbox tileset source 
        logging.info('Creating a Mapbox tileset source')
        tileset_source_id = f'{data["bucket"]}.{data["name"]}'
        tileset_source_url = f'https://api.mapbox.com/tilesets/v1/sources/{tileset_source_id}?access_token={os.environ["MAPBOX_ACCESS_TOKEN"]}'
        with open(tmp_geojson, "rb") as file:
            files = {"file": file}
        r = requests.post(tileset_source_url, headers=headers, files=files)
        
        # save id from response body
        tileset_source_id = r.json()["id"]

        # Retrieve the tileset recipe
        logging.info('Retrieving the tileset recipe')
        tileset_recipe_url = f'https://api.mapbox.com/tilesets/v1/{tileset_source_id}?access_token={os.environ["MAPBOX_ACCESS_TOKEN"]}'
        r = requests.get(tileset_recipe_url)
        # save id from response body
        tileset_recipe = r.json()["recipe"]
        
        # Create a tileset
        logging.info('Creating a tileset')
        tileset_id = f'{username}.{id}'
        tileset_url = f'https://api.mapbox.com/tilesets/v1/{tileset_id}?access_token={os.environ["MAPBOX_ACCESS_TOKEN"]}'
        tileset_json = {
            "name": tileset_id,
            "recipe": tileset_recipe,
        }
        r = requests.post(tileset_url, json=tileset_json, headers={ "Content-Type": "application/json" })


        logging.info('Done')
        return ("Completed", 200)

    except Exception as e:
        logging.error(f"Error encountered: {str(e)}")
        return f"Error: {str(e)}", 500

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
    except Exception as e:
        logging.error(f"Error encountered: {str(e)}")
        return (
            "Something went wrong, but returning 200 to prevent PubSub infinite retries",
            200,
        )

@app.get('/')
def test():
    return 'OK'


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
