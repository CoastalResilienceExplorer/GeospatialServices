import os
import logging
import uuid
import threading
import requests
from cloudevents.http import from_http
from flask import Flask, request
import geopandas as gpd
import pandas as pd
from utilities.gcs import download_blob, delete_blob
from utilities.geoparquet_utils import is_polygon, partition_gdf

logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)


@app.route("/build_geoparquet/", methods=["POST"])
def build_geoparquet():
    """Handle tile requests."""
    logging.info(request.get_json())
    logging.info(type(request.get_json()))
    data = request.get_json()
    tmp_id = str(uuid.uuid1())
    _, extension = os.path.splitext(data["name"])
    tmp_file = f"/tmp/{tmp_id}.{extension[1:]}"
    tmp_parquet = f"/tmp/{tmp_id}.parquet"
    download_blob(data["bucket"], data["name"], tmp_file)
    # try:
    logging.info("Reading file with geopandas")
    gdf = gpd.read_file(tmp_file)
    if data["partition"]:
        logging.info("Partitioning")
        gdf, partition_cols = partition_gdf(gdf)
        logging.info("Writing to Parquet")
        filename = "vectors/" + os.path.splitext(data["name"])[0] + ".parquet"
        remote_path = os.path.join(f"gs://{os.environ['OUTPUT_BUCKET']}", filename)
        gdf.to_parquet(tmp_parquet)
        delete_blob(os.environ["OUTPUT_BUCKET"], filename)
        # to_parquet in geopandas doesn't yet implement partitions, so we're writing with pandas
        # This impacts reading, see README
        to_write = pd.read_parquet(tmp_parquet)
        print(to_write)
        print(to_write.columns)
        to_write.to_parquet(
            remote_path, partition_cols=partition_cols, max_partitions=1_000_000
        )
    else:
        print("No Partitions")
        filename = "vectors/" + os.path.splitext(data["name"])[0] + ".parquet"
        remote_path = os.path.join(f"gs://{os.environ['OUTPUT_BUCKET']}", filename)
        gdf.to_parquet(remote_path)
        # If polygon, write the Rep Pts as well since those are generally useful.
        if is_polygon(gdf):
            filename_pts = "vectors/" + os.path.splitext(data["name"])[0] + "_reppts" + ".parquet"
            remote_path = os.path.join(f"gs://{os.environ['OUTPUT_BUCKET']}", filename_pts)
            gdf.geometry = gdf.geometry.representative_point()
            gdf.to_parquet(remote_path)


    return ("Completed", 200)

    # except Exception as e:
    #     logging.error(f"Error encountered: {str(e)}")
    #     return f"Error: {str(e)}", 500


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
        logging.info(event.data["id"])

        # Gets the GCS bucket name from the CloudEvent data
        # Example: "storage.googleapis.com/projects/_/buckets/my-bucket"
        # try:
        gcs_object = os.path.join(event.data["bucket"], event.data["name"])
        logging.info(gcs_object)
        logging.info(os.environ["FORWARD_SERVICE"])
        fire_and_forget(
            f"{os.environ['FORWARD_SERVICE']}/{os.environ['FORWARD_PATH']}",
            json={
                "bucket": event.data["bucket"],
                "name": event.data["name"],
                "partition": False
            },
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


@app.get("/")
def test():
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
