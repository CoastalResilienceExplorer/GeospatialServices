import os
import logging
from flask import Flask, request
import flask
import geopandas as gpd
import subprocess
from utilities.gcs import list_blobs, upload_blob, download_blob

logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)




@app.route("/create_pmtiles/", methods=["POST"])
def geoparquet_to_pmtiles():
    """Handle tile requests."""
    logging.info(request.get_json())
    data = request.get_json()
    logging.info(data)

    x = gpd.read_parquet(data['input'])
    logging.info(x)
    if not x.crs:
        x = x.set_crs("EPSG:4326")
    x = x.to_crs("EPSG:4326")
    # tmp_id = str(uuid.uuid1())
    tmp_id = data["output"].split('/')[-1].split('.')[0]
    if tmp_id == "":
        tmp_id = data["output"].split('/')[-2].split('.')[0]
    use_id=data["use_id"]
    if use_id not in x.columns:
        x[use_id] = x.index
    tmp_file = f'/tmp/{tmp_id}.geojson'
    tmp_pmtiles = f'/tmp/{tmp_id}.pmtiles'
    logging.info(x)
    x.to_file(tmp_file)
    
    tippecanoe_command = f"tippecanoe -o {tmp_pmtiles} --drop-rate=0.1 --no-feature-limit --read-parallel --no-tile-size-limit --use-attribute-for-id={use_id} {tmp_file} --force"
    process = subprocess.Popen(tippecanoe_command.split(' '), stdout=subprocess.PIPE)
    logging.info('Running tippecanoe')
    while True:
        line = process.stdout.readline()
        if not line: break
        print(line, flush=True)
    remote_name = data['output'].split('/')
    if remote_name[-1] == "":
        remote_name = '/'.join(remote_name[0:-1]).replace('.parquet', '.pmtiles')
    else:
        remote_name = '/'.join(remote_name).replace('.parquet', '.pmtiles')
    upload_blob(os.environ['OUTPUT_BUCKET'], tmp_pmtiles, remote_name)
    return ("Completed", 200)


@app.route('/get_tilesets/', methods=["GET"])
def get_tilesets():
    response = flask.jsonify(list_blobs(os.environ['OUTPUT_BUCKET']))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
