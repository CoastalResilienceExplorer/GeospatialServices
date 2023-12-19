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
from utils.timing import timeit
from utils.cache import memoize_with_persistence
from utils.geo import xr_vectorize, extract_points
import shutil
import copy
# A Python program to demonstrate working of OrderedDict
from collections import OrderedDict
import numpy as np

# from utils.census import get_blockgroups_by_county


logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)


def gpd_read_parquet(path):
    data = pd.read_parquet(path)
    gdf = gpd.GeoDataFrame(data, geometry=gpd.GeoSeries.from_wkb(data["geometry"]))
    return gdf


gpd.read_parquet = gpd_read_parquet


def get_covering(lower_left, upper_right):
    r = s2sphere.RegionCoverer()
    p1 = s2sphere.LatLng.from_degrees(lower_left[1], lower_left[0])
    p2 = s2sphere.LatLng.from_degrees(upper_right[1], upper_right[0])
    covering = r.get_covering(s2sphere.LatLngRect.from_point_pair(p1, p2))
    return covering


def get_relevant_partitions(covering, features):
    partition_ids = [int(i.split(".")[0]) for i in os.listdir(features)]
    buff = []
    for p in partition_ids:
        p = s2sphere.CellId(p)
        for c in covering:
            if p.contains(c) or c.contains(p) or p == c:
                buff.append(p)
    return list(set(buff))


# @memoize_with_persistence("/tmp/cache.pkl")
def get_bbox_filtered_gdf(features, lower_left, upper_right) -> gpd.GeoDataFrame:
    covering = get_covering(
        [lower_left.x, lower_left.y], [upper_right.x, upper_right.y]
    )

    relevant_partitions = get_relevant_partitions(covering, features)
    print(relevant_partitions)
    buff = []
    for p in relevant_partitions:
        buff.append(
            gpd.read_parquet(
                os.path.join(features, f"{p.id()}.parquet")
            )
        )
    gdf = pd.concat(buff)
    print(gdf.shape)
    gdf_filtered = gdf.cx[lower_left.x : upper_right.x, lower_left.y : upper_right.y]
    return gdf_filtered


def apply_ddf(features, depth_column, ddfs='data/composite_ddfs_by_bg.csv', avg_costs='data/avg_cost_by_bg.csv'):
    def is_numeric(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    to_return = copy.deepcopy(features)
    ddfs = pd.read_csv(ddfs, dtype = {'Blockgroup': str})
    avg_costs = pd.read_csv(avg_costs, dtype={'Blockgroup': str})
    to_return = pd.merge(to_return, ddfs, left_on="GEOID", right_on="Blockgroup")
    depth_cols = [i for i in ddfs.columns if i[0] == 'm' and is_numeric(i[1:])]
    depth_vals = OrderedDict()
    for i in depth_cols:
        depth_vals[i] = float(i[1:])
    values = []
    for idx, row in to_return.iterrows():
        print('---')
        depth = row[depth_column]
        print(depth)
        prev_val = row[depth_cols[0]]
        prev_depth = depth_vals[depth_cols[0]]
        for k,v in depth_vals.items():
            print(k)
            this_val = row[k]
            this_depth = v
            if depth < v:
                val = np.interp(depth, [prev_depth, this_depth], [prev_val, this_val])
                print(f'matched on {k} - {v}')
                values.append(val)
                break
            prev_val = this_val
            prev_depth = this_depth
    print(depth_vals)
    to_return['percent_damage'] = values
    to_return = pd.merge(to_return, avg_costs, left_on="GEOID", right_on="Blockgroup")
    to_return['total_damage'] = to_return['percent_damage'] * to_return['MeanValue']
    return to_return



@app.route("/get_features/", methods=["POST"])
@timeit
def build_geoparquet():
    """Handle tile requests."""
    logging.info(request.get_json())
    logging.info(type(request.get_json()))
    data = request.get_json()
    id = data['raster'].split('/')[-1].split('.')[0]
    output_dir = f'/tmp/{id}'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    raster = xr.open_dataarray(os.path.join(os.environ["MNT_BASE"], data["raster"]))
    b = raster.rio.bounds()
    lower_left = transform_point(b[0], b[1], raster.rio.crs)
    upper_right = transform_point(b[2], b[3], raster.rio.crs)

    ###
    # Get Flood Depths by Building
    ###
    all_buildings = get_bbox_filtered_gdf(
            os.path.join(os.environ["MNT_BASE"], data["features_file"]),
            lower_left,
            upper_right,
        ).set_crs("EPSG:4326").to_crs(raster.rio.crs)
    all_buildings.geometry = all_buildings.geometry.centroid
    all_buildings.sindex
    features = copy.deepcopy(all_buildings)
    features.geometry = features.geometry.centroid
    features.sindex
    print("getting extent...")
    extent = xr_vectorize(raster)
    print("joining...")
    result = gpd.sjoin(features, extent, how="inner", predicate="intersects")
    print("extracting values at points...")
    result = extract_points(raster, result, column_name=id)
    result = result.drop(columns=[i for i in result.columns if i[0:5] == "index"])
    result = result[result[id] > 0]

    mode = data["mode"]
    if mode == "SAN_MATEO":
        print("doing special things for San Mateo...")
        bgs = gpd.read_file("data/bcdc_vulnerability_2020.gpkg").to_crs(raster.rio.crs)
        # Totals
        all_joined = gpd.sjoin(all_buildings, bgs, how="inner", predicate="intersects")
        total_count_buildings = all_joined.groupby('GEOID').count().geometry.rename('total_buildings')
        # Flooded Totals
        flooded_joined = gpd.sjoin(result, bgs, how="inner", predicate="intersects")
        damages = apply_ddf(flooded_joined, id)
        print("writing buildings gpkg...")
        damages.to_file(os.path.join(output_dir, "features.gpkg"), driver="GPKG")

        print('calculating damage totals...')
        damage_summary = damages[['GEOID', 'total_damage']].groupby('GEOID').sum()
        flooded_count_buildings = flooded_joined.groupby('GEOID').count().geometry.rename('flooded_buildings')
        output = pd.merge(total_count_buildings, flooded_count_buildings, left_index=True, right_index=True)
        bg_columns = ['GEOID', 'estimate_t', 'socVulnRan']
        output = pd.merge(bgs[bg_columns], output, left_on="GEOID", right_index=True)
        output['percent_flooded'] = output['flooded_buildings'] / output['total_buildings']
        output['people_flooded'] = output['estimate_t'] * output['percent_flooded']
        output = pd.merge(output, damage_summary, left_on="GEOID", right_on="GEOID")
        output.to_csv(
            os.path.join(output_dir, 'flooded_statistics.csv')
        )

    print("file written, sending...")
    if not os.path.exists('/results'):
        os.makedirs('/results')
    results_dir = f'/results/{id}'
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    shutil.make_archive(os.path.join(results_dir, "results"), 'zip', output_dir)
    return flask.send_from_directory(results_dir, "results.zip")


@app.get("/")
def test():
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
