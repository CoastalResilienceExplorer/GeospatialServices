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
import uuid

# A Python program to demonstrate working of OrderedDict
from collections import OrderedDict
import numpy as np
from utils.AEV import calculate_AEV

# from utils.census import get_blockgroups_by_county


logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)


def gpd_read_parquet(path):
    data = pd.read_parquet(path)
    gdf = gpd.GeoDataFrame(data, geometry=gpd.GeoSeries.from_wkb(data["geometry"]))
    return gdf


gpd.read_parquet = gpd_read_parquet


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


@memoize_with_persistence("/tmp/cache.pkl")
def get_bbox_filtered_gdf(features, lower_left, upper_right) -> gpd.GeoDataFrame:
    covering = get_covering(
        [lower_left.x, lower_left.y], [upper_right.x, upper_right.y]
    )

    relevant_partitions = get_relevant_partitions(covering, features)
    print(relevant_partitions)
    buff = []
    for p in relevant_partitions:
        buff.append(gpd.read_parquet(os.path.join(features, f"{p.id()}.parquet")))
    gdf = pd.concat(buff)
    print(gdf.shape)
    gdf_filtered = gdf.cx[lower_left.x : upper_right.x, lower_left.y : upper_right.y]
    return gdf_filtered


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


@app.route("/san_mateo/", methods=["POST"])
@timeit
def san_mateo():
    """Handle tile requests."""
    logging.info(request.get_json())
    logging.info(type(request.get_json()))
    data = request.get_json()
    rasters = data["rasters"]
    rps = data["rps"]

    ### Get All Buildings from the Last Raster
    # This should be the largest extent
    last_raster = xr.open_dataarray(os.path.join(os.environ["MNT_BASE"], rasters[-1]))
    b = last_raster.rio.bounds()
    lower_left = transform_point(b[0], b[1], last_raster.rio.crs)
    upper_right = transform_point(b[2], b[3], last_raster.rio.crs)
    all_buildings = (
        get_bbox_filtered_gdf(
            os.path.join(os.environ["MNT_BASE"], data["features_file"]),
            lower_left,
            upper_right,
        )
        .set_crs("EPSG:4326")
        .to_crs(last_raster.rio.crs)
        .reset_index()
        .rename(columns={"index": "building_fid"})
    )
    all_buildings_polygons = copy.deepcopy(all_buildings)
    all_buildings.geometry = all_buildings.geometry.centroid
    all_buildings.sindex

    ## BCDC
    bgs = gpd.read_file("data/BCDC.gpkg").to_crs(
        last_raster.rio.crs
    )
    bcdc_buildings = gpd.sjoin(all_buildings, bgs, how="inner")
    bcdc_buildings = bcdc_buildings[list(all_buildings.columns) + ["GEOID"]]
    print(bcdc_buildings)

    ### Loop over all rasters
    all_damages = []
    damage_columns = []
    xid = str(uuid.uuid1())
    output_dir = f"/tmp/{xid}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for raster in rasters:
        id = raster.split("/")[-1].split(".")[0]
        raster = xr.open_dataarray(os.path.join(os.environ["MNT_BASE"], raster))
        print('calculating extent...')
        extent = xr_vectorize(raster, coarsen_by=50)
        extent.to_file(os.path.join(output_dir, f"extent_{id}.gpkg"), driver="GPKG")

        ###
        # Get Flood Depths by Building
        ###  
        features = copy.deepcopy(bcdc_buildings)
        print("extracting values at points...")
        extracted = extract_points(raster, features, column_name=id)
        extracted = extracted.drop(columns=[i for i in extracted.columns if i[0:5] == "index"])
        extracted = extracted[extracted[id] > 0]

        # Flooded Totals BCDC
        print("applying DDFs...")
        damages, col = apply_ddf(extracted, id)
        all_damages.append(damages[["building_fid", col]].set_index("building_fid"))
        damage_columns.append(col)

    all_damages = all_damages[0].fillna(0)
    all_damages["AED"] = all_damages[damage_columns[0]]
    # Combine Damages
    print('writing buildings file...')
    bcdc_buildings = pd.merge(bcdc_buildings, all_damages, on="building_fid", how="left").fillna(0)
    bcdc_buildings.to_file(os.path.join(output_dir, "building_damages.gpkg"), driver="GPKG")

    # # Get Blockgroup-Level Damage Statistics
    print('creating blockgroup summary statistics...')
    total_count_buildings = bcdc_buildings.groupby('GEOID').count().geometry.rename('total_buildings')
    total_damage = bcdc_buildings[['GEOID', 'AED']].groupby('GEOID').sum()['AED'].rename('total_damage')
    buildings_flooded_buff = []
    bldg_cnt_col_buff = []
    for dc in damage_columns:
        count_col = dc.replace('total_damage_', 'count_flooded_')
        buildings_flooded_buff.append(bcdc_buildings[bcdc_buildings[dc] > 0].groupby('GEOID').count().geometry.rename(count_col))
        bldg_cnt_col_buff.append(count_col)
    # buildings_flooded = recursive_merge(*buildings_flooded_buff)
    buildings_flooded = buildings_flooded_buff[0].rename('Annual_Exp_Cnt_Bldgs_Flooded')
    print(buildings_flooded)
    # flooded_count_buildings = bcdc_buildings[bcdc_buildings["AED"] > 0].groupby('GEOID').count().geometry.rename('flooded_buildings')
    output = recursive_merge(total_count_buildings, total_damage, buildings_flooded)
    output = pd.merge(bgs, output, left_on="GEOID", right_index=True)
    output['annual_exp_percent_flooded'] = output['Annual_Exp_Cnt_Bldgs_Flooded'] / output['total_buildings']
    output['annual_exp_people_flooded'] = output['estimate_t'] * output['annual_exp_percent_flooded']
    output.to_file(
        os.path.join(output_dir, 'BCDC_flooded_statistics.gpkg'),
        driver="GPKG"
    )

    ################
    ##### CES4 #####
    ################
    # print('running CES4...')
    # ces4 = gpd.read_file("data/CES4.gpkg").to_crs(raster.rio.crs)

    # # # Totals
    # all_buildings = pd.merge(all_buildings, all_damages, on="building_fid", how="left").fillna(0)
    # ces4_grouping_columns = ['Tract', 'AED'] + [i for i in all_buildings.columns if 'total_damage' in i]
    # ces4_buildings = gpd.sjoin(all_buildings, ces4, how="inner")[ces4_grouping_columns]
    # print(ces4_buildings)
    # print(ces4_buildings.columns)

    # ces4_statistics = ces4_buildings.groupby('Tract').sum()
    # ces4_building_totals = ces4_buildings.groupby('Tract').count()['AED'].rename("total_buildings")
    # print('getting annual expected buildings flooded...')
    # buildings_flooded_buff = []
    # bldg_cnt_col_buff = []
    # for dc in damage_columns:
    #     count_col = dc.replace('total_damage_', 'count_flooded_')
    #     buildings_flooded_buff.append(ces4_buildings[ces4_buildings[dc] > 0].groupby('Tract').count()[dc].rename(count_col))
    #     bldg_cnt_col_buff.append(count_col)
    # buildings_flooded = recursive_merge(*buildings_flooded_buff)
    # buildings_flooded['Annual_Exp_Cnt_Bldgs_Flooded'] = buildings_flooded.apply(
    #     lambda row: calculate_AEV(
    #         rps,
    #         [row[col] for col in bldg_cnt_col_buff], 
    #     ),
    #     axis=1, 
    # )
    # ces4_statistics = recursive_merge(ces4.set_index("Tract"), ces4_statistics, ces4_building_totals, buildings_flooded).reset_index()
    # ces4_statistics['annual_exp_percent_flooded'] = ces4_statistics['Annual_Exp_Cnt_Bldgs_Flooded'] / ces4_statistics['total_buildings']
    # ces4_statistics['annual_exp_people_flooded'] = ces4_statistics['TotPop19'] * ces4_statistics['annual_exp_percent_flooded']
    # ces4_statistics.to_file(
    #     os.path.join(output_dir, 'CES4_flooded_statistics.gpkg'),
    #     driver="GPKG"
    # )

    print("file written, sending...")
    if not os.path.exists("/results"):
        os.makedirs("/results")
    results_dir = f"/results/{xid}"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    shutil.make_archive(os.path.join(results_dir, "results"), "zip", output_dir)
    return flask.send_from_directory(results_dir, "results.zip")


@app.get("/")
def test():
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
