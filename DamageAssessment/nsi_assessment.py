from get_features import get_features_unpartitioned
from utils.geo import extract_z_values
from utils.cache import memoize_with_persistence
import pandas as pd
import copy
from collections import OrderedDict
import numpy as np

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
    print(to_return)
    to_return[bddf_column] = to_return[bddf_column].apply(lambda x: correct_nsi_occtype(x))
    print(to_return)
    transformed = to_return[[bddf_column, "num_story", "found_type"]].apply(
        lambda x: transform_nsi(x[bddf_column], x['num_story'], x['found_type']), axis=1
    )
    print(transformed)
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
            if divide_by_100:
                values.append(1.0)
            else:
                values.append(100)
            
    col = f"percent_damage_{depth_column}"
    to_return[col] = values
    to_return = to_return[[c for c in to_return.columns if c not in depth_cols]]
    return to_return, col


@memoize_with_persistence("/tmp/cache")
def get_nsi(left, bottom, top, right, state, crs):
    gdf = get_features_unpartitioned(
        features_file=f"geopmaker-output-staging/nsi.geoparquet/{state}.geoparquet",
        left=left,
        bottom=bottom,
        right=right,
        top=top,
        CRS=crs
    )
    return gdf


def get_nsi_damages(ds, gdf):
    id = "depth"
    ds = ds.rio.reproject("EPSG:4326")
    gdf_points = extract_z_values(ds=ds, gdf=gdf, column_name=id, offset_column="found_ht", offset_units="m")
    gdf_points = gdf_points[gdf_points[id] > 0]
    x = apply_ddf(gdf_points, id)
    return x[0]


def get_nsi_damage_tractbased(ds):
    
    features = 
