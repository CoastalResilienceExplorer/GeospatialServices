import os
import logging
from flask import Flask, request
import pandas as pd
from get_features import get_osm, get_open_buildings, get_features_unpartitioned
import xarray as xr
import rioxarray as rxr
import copy, io

# A Python program to demonstrate working of OrderedDict
from collections import OrderedDict
import numpy as np
from utils.api_requests import data_to_parameters_factory, response_to_gpkg
from utils.geo import extract_z_values, rescale_raster

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
    bddf_column="occtype",
    ddfs="data/vulnerability_curves/nsi_median_vulnerability_curves.csv",
    ddf_column="DerivedOccType",
    divide_by_100=True
):
    def correct_nsi_occtype(occtype):
        to_return = occtype.split('-')[0]
        if to_return in ("RES3A", "RES3B", "RES3C", "RES3D", "RES3E", "RES3F"):
            return "RES3"
        return to_return

    def is_numeric(s):
        try:
            float(s)
            return True
        except ValueError:
            return False
        
    def transform_nsi(occtype, nstories, found_type):
        if "RES" not in occtype:
            return f"{occtype}-1-NB"
        else:
            if occtype != "RES1":
                return f"{occtype}-1-NB"
            nstories = int(min(3, nstories))
            if found_type != "B":
                found_type = "NB"
            else:
                found_type = "WB"
            return f"{occtype}-{nstories}-{found_type}"

    to_return = copy.deepcopy(features)
    to_return[bddf_column] = to_return[bddf_column].apply(lambda x: correct_nsi_occtype(x))
    to_return['FAST_match'] = to_return[[bddf_column, "num_story", "found_type"]].apply(
        lambda x: transform_nsi(x[bddf_column], x['num_story'], x['found_type']), axis=1
    )
    ddfs = pd.read_csv(ddfs)
    match_cols = ddfs[ddf_column].unique()
    for t in to_return['FAST_match'].unique():
        assert t in match_cols, f"{t} not in FAST"
    to_return = pd.merge(to_return, ddfs, left_on='FAST_match', right_on=ddf_column)
    depth_cols = [i for i in ddfs.columns if i[0] == "m" and is_numeric(i[1:])]
    depth_vals = OrderedDict()
    for i in depth_cols:
        depth_vals[i] = float(i[1:])
    values = []
    count_values_not_found = 0
    for idx, row in to_return.iterrows():
        depth = row[depth_column]
        if depth <= 0:
            values.append(0)
            continue
        prev_val = row[depth_cols[0]]
        prev_depth = 0
        val_found = False
        for k, v in depth_vals.items():
            this_val = row[k]
            this_depth = v
            if depth < v:
                val = np.interp(depth, [prev_depth, this_depth], [prev_val, this_val])
                if divide_by_100:
                    val = val * 0.01
                values.append(val)
                val_found = True
                break
            prev_val = this_val
            prev_depth = this_depth
        if not val_found:
            count_values_not_found += 1
    print(count_values_not_found)
            
    col = f"percent_damage_{depth_column}"
    to_return[col] = values
    to_return = to_return[[c for c in to_return.columns if c not in depth_cols]]
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
        io.BytesIO(request.files['z'].read())
    ).isel(band=0)
    features_from = request.form.get('features_from', 'OSM')
    assert features_from in ('OSM, OpenBuildings')
    if features_from == "OSM":
        way_type = request.form.get('way_type', 'building')
        b = z.rio.bounds()
        left, bottom, right, top = b
        gdf = get_osm(left=left, bottom=bottom, right=right, top=top, way_type=way_type)
        gdf_points = copy.deepcopy(gdf)
        gdf_points['geometry'] = gdf_points['geometry'].centroid
        gdf_points = extract_z_values(ds=z, gdf=gdf_points, column_name="z")
        gdf['z'] = gdf_points['z']
        gdf['z'][gdf['z'] == z.rio.nodata] = np.nan
        return gdf
    
    else:
        return ("Only OSM currently supported", 404)

@app.route('/get_nsi/', methods=["POST"])
@response_to_gpkg
def api_get_nsi():
    z = rxr.open_rasterio(
        io.BytesIO(request.files['z'].read())
    ).isel(band=0).rio.reproject("EPSG:4326")
    b = z.rio.bounds()
    left, bottom, right, top = b
    gdf = get_features_unpartitioned(
        features_file="geopmaker-output-staging/vectors/san-mateo/NSI_SanMateo.parquet",
        left=left,
        bottom=bottom,
        right=right,
        top=top,
        CRS=z.rio.crs
    )
    return gdf

@app.route('/get_building_damages/', methods=["POST"])
@response_to_gpkg
def api_get_building_damages():
    z = rxr.open_rasterio(
        io.BytesIO(request.files['z'].read())
    ).isel(band=0).rio.reproject("EPSG:4326")
    z = rescale_raster(z)
    features_from = request.form.get('features_from')
    id = request.form.get('id')
    offset_column = request.form.get('offset_column')
    offset_units = request.form.get('offset_units')
    print(features_from)
    assert features_from in ('OSM, OpenBuildings', 'NSI')
    if features_from == "OSM":
        way_type = request.form.get('way_type', 'building')
        b = z.rio.bounds()
        left, bottom, right, top = b
        gdf = get_osm(left=left, bottom=bottom, right=right, top=top, way_type=way_type)
        gdf_points = copy.deepcopy(gdf)
        gdf_points['geometry'] = gdf_points['geometry'].centroid
        gdf_points = extract_z_values(ds=z, gdf=gdf_points, column_name=id, offset_column=offset_column, offset_units=offset_units)
        gdf[id] = gdf_points[id]
        gdf[id][gdf[id] == z.rio.nodata] = np.nan
        return gdf
    
    elif features_from == "NSI":
        b = z.rio.bounds()
        left, bottom, right, top = b
        gdf = get_features_unpartitioned(
            features_file="geopmaker-output-staging/vectors/san-mateo/NSI_SanMateo.parquet",
            left=left,
            bottom=bottom,
            right=right,
            top=top,
            CRS=z.rio.crs
        )
        gdf_points = extract_z_values(ds=z, gdf=gdf, column_name=id, offset_column=offset_column, offset_units=offset_units)
        gdf_points = gdf_points[gdf_points[id] > 0]
        x = apply_ddf(gdf_points, id)
        return x[0]
        
    
    else:
        return ("Only OSM currently supported", 404)


@app.get("/")
def test():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
