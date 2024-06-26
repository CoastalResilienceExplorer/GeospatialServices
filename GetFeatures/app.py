import os
import logging
from flask import Flask, request
import pandas as pd
from get_features import get_osm, get_open_buildings
import xarray as xr
import rioxarray as rxr
import copy, io

# A Python program to demonstrate working of OrderedDict
from collections import OrderedDict
import numpy as np
from utils.api_requests import data_to_parameters_factory, response_to_gpkg
from utils.geo import extract_z_values
from utils.geoparquet_utils import write_partitioned_gdf

TMP_FOLDER = '/tmp'

logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)


def recursive_merge(*series_list):
    if len(series_list) < 2:
        raise ValueError("At least two Series are required for merging.")

    # Base case: if only two Series are left, merge them and return
    if len(series_list) == 2:
        return pd.merge(
            series_list[0],
            series_list[1],
            left_index=True,
            right_index=True,
            how="outer",
        )

    # Recursive case: merge the first two, then merge with the next one, and so on
    merged_series = pd.merge(
        series_list[0], series_list[1], left_index=True, right_index=True, how="outer"
    )

    return recursive_merge(merged_series, *series_list[2:])


def apply_ddf(
    features,
    depth_column,
    ddfs="data/composite_ddfs_by_bg.csv",
    avg_costs="data/avg_cost_by_bg.csv",
):
    def is_numeric(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    to_return = copy.deepcopy(features)
    ddfs = pd.read_csv(ddfs, dtype={"Blockgroup": str})
    avg_costs = pd.read_csv(avg_costs, dtype={"Blockgroup": str})
    to_return = pd.merge(to_return, ddfs, left_on="GEOID", right_on="Blockgroup")
    depth_cols = [i for i in ddfs.columns if i[0] == "m" and is_numeric(i[1:])]
    depth_vals = OrderedDict()
    for i in depth_cols:
        depth_vals[i] = float(i[1:])
    values = []
    for idx, row in to_return.iterrows():
        depth = row[depth_column]
        prev_val = row[depth_cols[0]]
        prev_depth = depth_vals[depth_cols[0]]
        for k, v in depth_vals.items():
            this_val = row[k]
            this_depth = v
            if depth < v:
                val = np.interp(depth, [prev_depth, this_depth], [prev_val, this_val])
                values.append(val)
                break
            prev_val = this_val
            prev_depth = this_depth
    to_return["percent_damage"] = values
    to_return = pd.merge(to_return, avg_costs, left_on="GEOID", right_on="Blockgroup")
    col = f"total_damage_{depth_column}"
    to_return[col] = to_return["percent_damage"] * to_return["MeanValue"]
    return to_return, col



@app.route('/get_osm/', methods=["POST"])
@data_to_parameters_factory(app)
@response_to_gpkg
def api_get_osm(left, bottom, top, right, way_type):
    gdf = get_osm(left, bottom, top, right, way_type)
    return gdf


@app.route('/get_open_buildings/', methods=["POST"])
@data_to_parameters_factory(app)
@response_to_gpkg
def api_get_open_buildings(left, bottom, right, top, ISO3):
    buildings = get_open_buildings(left, bottom, right, top, ISO3)
    return buildings


@app.route('/get_features_with_z_values/', methods=["POST"])
@response_to_gpkg
def api_extract_z_values():
    z = rxr.open_rasterio(
        io.BytesIO(request.files['flooding'].read())
    ).isel(band=0).rio.reproject("EPSG:4326")
    attrs = z.attrs
    z = xr.where(z == z.rio.nodata, 0, z)
    z.rio.write_nodata(0, inplace=True) 
    id = request.form['id']
    if (bool(request.form['rescale'])): 
        z = z * attrs['scale_factor']
    features_from = request.form.get('features_from', 'OSM')
    assert features_from in ('OSM, OpenBuildings')
    if features_from == "OSM":
        way_type = request.form.get('way_type', 'building')
        b = z.rio.bounds()
        left, bottom, right, top = b
        gdf = get_osm(left=left, bottom=bottom, right=right, top=top, way_type=way_type)
        gdf = gdf[['id', 'type', 'geometry']]
        gdf_points = copy.deepcopy(gdf)
        gdf_points['geometry'] = gdf_points['geometry'].centroid
        gdf_points = extract_z_values(ds=z, gdf=gdf_points, column_name=id)
        gdf[id] = gdf_points[id]
        gdf[id][gdf[id] == z.rio.nodata] = np.nan
        write_partitioned_gdf(
            gdf, 
            f"{request.form['gcs_output']}"
        )

        return gdf
    
    if features_from == "OPEN_BUILDINGS":
        b = z.rio.bounds()
        left, bottom, right, top = b
        ISO3 = request.form["ISO3"]
        gdf = get_open_buildings(left=left, bottom=bottom, right=right, top=top, ISO3=ISO3)
        gdf_points = copy.deepcopy(gdf)
        gdf_points['geometry'] = gdf_points['geometry'].centroid
        gdf_points = extract_z_values(ds=z, gdf=gdf_points, column_name=id)
        gdf[id] = gdf_points[id]
        gdf[id][gdf[id] == z.rio.nodata] = np.nan
        return gdf
    
    else:
        return ("Only OSM currently supported", 404)



@app.get("/")
def test():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
