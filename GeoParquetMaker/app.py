import os
import logging
import uuid
import threading
import requests
from cloudevents.http import from_http
from flask import Flask, request
from google.cloud import storage
import geopandas as gpd
import pandas as pd
import s2sphere

logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)


def delete_blob(bucket_name, blob_name):
    """Deletes a blob from the bucket."""
    # bucket_name = "your-bucket-name"
    # blob_name = "your-object-name"

    storage_client = storage.Client(project="global-mangroves")

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    existing_blobs = storage_client.list_blobs(bucket_name)
    for existing_blob in existing_blobs:
        # print(existing_blob)
        if blob_name == existing_blob:
            print("Deleting")
            blob.delete()
            print(f"Blob {blob_name} deleted.")


def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The ID of your GCS object
    # source_blob_name = "storage-object-name"

    # The path to which the file should be downloaded
    # destination_file_name = "local/path/to/file"

    storage_client = storage.Client(project="global-mangroves")

    bucket = storage_client.bucket(bucket_name)

    # Construct a client side representation of a blob.
    # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
    # any content from Google Cloud Storage. As we don't need additional data,
    # using `Bucket.blob` is preferred here.
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    logging.info(
        "Downloaded storage object %s from bucket %s to local file %s.",
        source_blob_name,
        bucket_name,
        destination_file_name,
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
        source_file_name,
        bucket_name,
        destination_blob_name,
    )

    storage_client = storage.Client(project="global-mangroves")
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

    logging.info("File %s uploaded to %s.", source_file_name, destination_blob_name)


def is_polygon(gdf):
    polygon_bools = gdf.geom_type.apply(lambda s: "polygon" in s.lower()).unique()
    return len(polygon_bools) == 1 and polygon_bools[0]


def partition_gdf(
    gdf,
    partition_file="gs://geopmaker-output-dev/vectors/World_Countries_Generalized.parquet",
    partition_cols=["ISO"],
    partition_by_s2=True,
):
    if "ISO3" in gdf.columns:
        partitioned_gdf = gdf.rename(columns={"ISO3": "ISO"})
    else:
        partitions = gpd.read_parquet(partition_file)
        partitions = partitions[["geometry"] + partition_cols]
        partitioned_gdf = gpd.sjoin(gdf, partitions, how="left")
        # Swap ISO2 for ISO3, since that is generally more common
        if (
            partition_file
            == "gs://geopmaker-output-dev/vectors/World_Countries_Generalized.parquet"
        ):
            iso_mappings = pd.read_csv("countries-codes.csv")
            partitioned_gdf = (
                pd.merge(
                    partitioned_gdf, iso_mappings, left_on="ISO", right_on="ISO2 CODE"
                )
                .drop(columns=["ISO"])
                .rename(columns={"ISO3 CODE": "ISO"})
            )

    def get_bounds_by_geom(geom):
        bounds = geom.bounds
        p1 = s2sphere.LatLng.from_degrees(max(bounds[1], -90), max(bounds[0], -180))
        p2 = s2sphere.LatLng.from_degrees(min(bounds[3], 90), min(bounds[2], 180))
        if not p1.is_valid():
            print("p1")
            print(p1)
        if not p2.is_valid():
            print("p2")
            print(p2)
        cell_ids = [
            str(i.id())
            for i in r.get_covering(s2sphere.LatLngRect.from_point_pair(p1, p2))
        ]
        return cell_ids

    cols = partition_cols

    if partition_by_s2:
        r = s2sphere.RegionCoverer()
        r.min_level = 5
        r.max_level = 7
        partitioned_gdf["s2"] = partitioned_gdf.geometry.apply(
            lambda g: get_bounds_by_geom(g)
        )
        partitioned_gdf = partitioned_gdf.explode("s2")
        cols += ["s2"]

    return partitioned_gdf, cols


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
