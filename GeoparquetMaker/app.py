import os
import logging
from flask import Flask, request
import geopandas as gpd
import io
from utils.geoparquet_utils import partition_gdf, is_polygon, write_partitioned_gdf


logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)

GCS_BASE=os.environ['OUTPUT_BUCKET']

@app.route('/build_geoparquet/', methods=["POST"])
def api_build_geoparquet():
    fname = os.path.join('/tmp', request.files['data'].filename.split('/')[-1])
    with open(fname, 'wb') as f:
        f.write(request.files['data'].read())
    gdf = gpd.read_file(
        fname, engine='pyogrio', use_arrow=True
    )
    print('loaded')
    print(gdf.shape)
    partitions = request.form['partitions'].split(',')
    if len(partitions) == 1 and partitions[0] == '':
        partitions = []
    partitioned_gdf, cols = partition_gdf(
        gdf, 
        partition_cols=partitions, 
        partition_by_country=bool(int(request.form['partition_by_country'])),
        partition_by_s2=bool(int(request.form['partition_by_s2'])),
    )
    print(partitioned_gdf.shape)
    remote_path = os.path.join(f"gs://{os.environ['OUTPUT_BUCKET']}", request.form["output_to_gcs"])
    write_partitioned_gdf(partitioned_gdf, remote_path, cols)
    if is_polygon(gdf):
        remote_path = os.path.join(f"gs://{os.environ['OUTPUT_BUCKET']}", "reppts", request.form["id"])
        partitioned_gdf.geometry = partitioned_gdf.geometry.representative_point()
        write_partitioned_gdf(partitioned_gdf, remote_path, cols)
    return "200"


@app.route('/join_geoparquets/', methods=["POST"])
def api_join_geoparquets():
    datasets = request.form['datasets'].split(';')
    print(datasets)
    gdf = gpd.read_parquet(datasets[0])
    base_cols = gdf.columns

    for ds in datasets[1:]:
        gdf_to_add = gpd.read_parquet(ds)
        join_cols = [c for c in gdf_to_add.columns if c in base_cols]
        gdf = gdf.merge(gdf_to_add, how="outer", on=join_cols)
        del gdf_to_add

    write_partitioned_gdf(gdf, request.form['output'])
    return "200"


@app.get("/")
def test():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
