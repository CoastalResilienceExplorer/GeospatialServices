import os
import logging
from flask import Flask, request
import flask
import geopandas as gpd
import pandas as pd
import s2sphere
import xarray as xr
import rioxarray as rxr
from transform_point import transform_point


logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)


def gpd_read_parquet(path):
    data = pd.read_parquet(path)
    gdf = gpd.GeoDataFrame(data, geometry=gpd.GeoSeries.from_wkb(data["geometry"]))
    return gdf

gpd.read_parquet = gpd_read_parquet


@app.route("/get_features/", methods=["POST"])
def build_geoparquet():
    """Handle tile requests."""
    logging.info(request.get_json())
    logging.info(type(request.get_json()))
    data = request.get_json()
    raster = xr.open_dataarray(os.path.join(os.environ["MNT_BASE"], data["raster"]))
    r = s2sphere.RegionCoverer()

    def get_covering(lower_left, upper_right):
        p1 = s2sphere.LatLng.from_degrees(lower_left[1], lower_left[0])
        p2 = s2sphere.LatLng.from_degrees(upper_right[1], upper_right[0])
        covering = r.get_covering(s2sphere.LatLngRect.from_point_pair(p1, p2))
        return covering

    def get_relevant_partitions(covering):
        partition_ids = [
            int(i.split(".")[0])
            for i in os.listdir(
                os.path.join(os.environ["MNT_BASE"], data["features_file"])
            )
        ]
        buff = []
        for p in partition_ids:
            p = s2sphere.CellId(p)
            for c in covering:
                if p.contains(c) or c.contains(p) or p == c:
                    buff.append(p)
        return list(set(buff))


    b = raster.rio.bounds()
    lower_left = transform_point(b[0], b[1], raster.rio.crs)
    upper_right = transform_point(b[2], b[3], raster.rio.crs)
    covering = get_covering(
        [lower_left.x, lower_left.y], [upper_right.x, upper_right.y]
    )

    relevant_partitions = get_relevant_partitions(covering)
    print(relevant_partitions)
    buff = []
    for p in relevant_partitions:
        buff.append(
            gpd.read_parquet(os.path.join(os.environ['MNT_BASE'], data['features_file'], f'{p.id()}.parquet'))
        )
    gdf = pd.concat(buff)
    print(gdf.shape)
    gdf_filtered = gdf.cx[lower_left.x:upper_right.x, lower_left.y:upper_right.y]
    print(gdf_filtered.shape)
    gdf_filtered.to_file('/tmp/features.gpkg', driver="GPKG")
    print('file written, sending...')

    return flask.send_from_directory('/tmp', 'features.gpkg')


@app.get("/")
def test():
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
