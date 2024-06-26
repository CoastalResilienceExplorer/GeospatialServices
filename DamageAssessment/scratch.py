import geopandas as gpd
from string import Template
import itertools
import os
from glob import glob
import numpy as np
import xarray as xr

# Constants
BASEDIR = "/app/data/USGS_USVI"
id_prefix = "AEV-Econ"
rps = (10, 50, 100, 500)
template = "${island}_FZ_rp{rp}_${scen}_flood_depth"
_template = Template(template)
url = f'{os.getenv("HOST")}/aev/'


def AEV(values, rps, year_of_zero_damage=2.):
    rps      = np.array(rps)
    values  = np.array(values)

    probability = 1.0 / rps
        
    #add rp = 1
    probability_of_zero_damage = 1/year_of_zero_damage
    if not any(probability==probability_of_zero_damage): 
        x = probability.tolist()
        x.append(probability_of_zero_damage)
        y = values.tolist()
        y = np.hstack((y, np.zeros((values.shape[0], 1)))).T # loss 0 for annual flood 
        
        
        probability = np.array(x) 
        values      = np.array(y)

    ind = np.argsort(probability)
    ind[::-1]
    probability = probability[ind[::-1]]
    values      = values[ind[::-1]]

    DX  = probability[0:-1] - probability[1:]
    upper = sum((DX * values[1:].T).T)
    lower = sum((DX * values[0:-1].T).T)
    aev = (upper + lower) / 2
    return aev


# Helper Functions
def parse_scenarios(template, basedir):
    scenario_parse = [i.split('/')[-1].split('.')[0].split('_') for i in glob(os.path.join(basedir, '*.gpkg'))]
    scenarios = dict()
    for idx, k in enumerate(template.split('_')):
        if "$" in k:
            scenarios[k.replace("$", "").replace('{', '').replace('}', '')] = list(set([i[idx] for i in scenario_parse]))
    return scenarios

def compute_cartesian_product(scenarios):
    keys = scenarios.keys()
    values = scenarios.values()
    cross_product = itertools.product(*values)
    return [dict(zip(keys, items)) for items in cross_product]

def merge_geodataframes(paths, fields_to_keep=["flooding", "damages", "OccupancyWeightedValue"]):
    gdfs = [gpd.read_file(path) for path in paths]
    merged_gdf = gdfs[0][fields_to_keep + ["geometry"]]
    merged_gdf.rename(columns={col: col+"_"+paths[0].split("/")[-1].split(".")[0] for col in merged_gdf.columns if col != "geometry"}, inplace=True)

    for idx, gdf in enumerate(gdfs[1:], start=1):
        gdf = gdf[fields_to_keep + ["geometry"]]
        gdf.rename(columns={col: col+"_"+paths[idx].split("/")[-1].split(".")[0] for col in gdf.columns if col != "geometry"}, inplace=True)
        merged_gdf = merged_gdf.merge(gdf, how='outer', on='geometry')
    return merged_gdf

def spatial_join_nearest(left_gdf, right_gdf, id_column):
    if left_gdf.crs != right_gdf.crs:
        right_gdf = right_gdf.to_crs(left_gdf.crs)
    joined_gdf = left_gdf.sjoin_nearest(right_gdf[[id_column, 'geometry']], how='left', distance_col='distance')
    return joined_gdf.drop(columns=['distance'])

def process_scenarios(scenarios, template, basedir, id_prefix, rps):
    for values in scenarios:
        formatter = _template.safe_substitute(values)
        print(formatter)

        id = id_prefix + '_' + '_'.join(values.values())
        data = {
            "formatter": formatter,
            "damages": basedir,
            "output": basedir,
            "id": id,
            "rps": rps
        }
        gdf = merge_geodataframes([os.path.join(basedir, i) for i in [formatter.format(rp=rp)+'.gpkg' for rp in rps]])
        v = np.nan_to_num(gdf[[i for i in gdf.columns if "damages" in i]].to_numpy())
        aev = AEV(v, rps)
        print(aev)
        gdf['AEV'] = aev
        base_string = f'{basedir}/AEV/AEV-Econ' + ''.join([f"_{v}" for v in values.values()])
        gdf.to_file(f'{base_string}.gpkg', driver='GPKG')

def process_geospatial_data(base, bands_path, lines_base, ids):
    bands = gpd.read_file(bands_path, driver="SHP").reset_index()
    lines = {i: gpd.read_file(os.path.join(lines_base, f"{i}_Coastline_Intersect_SummaryPts_TransOrder{'_Merge' if i == 'StThomas' else ''}.shp")) for i in ["StCroix", "StThomas", "StJohn"]}

    for i in glob(os.path.join(base, "*.gpkg")):
        island = i.split('/')[-1].split('.')[0].split('_')[1]
        print(island)
        line = lines[island].drop(columns=[i for i in ["index_right", "index_left"] if i in lines[island].columns])
        line_id = ids[island]
        gdf = gpd.read_file(i)
        print(gdf.columns)
        out_lines = os.path.join(base, "aggs", "lines", f"{i.split('/')[-1].split('.')[0]}_points.gpkg")
        gdf_joined_lines = spatial_join_nearest(gdf, line, line_id)
        gdf_joined_lines.to_file(out_lines, driver="GPKG")
        out_bands = os.path.join(base, "aggs", "bands", f"{i.split('/')[-1].split('.')[0]}_points.gpkg")
        gdf_joined_bands = spatial_join_nearest(gdf, bands, "index")
        gdf_joined_bands.to_file(out_bands, driver="GPKG")
        
        fields_to_agg = [i for i in gdf_joined_lines.columns if np.any([j in i for j in ["AEV", "damages"]])]
        for field in fields_to_agg:
            gdf_joined_lines = gdf_joined_lines[fields_to_agg + [line_id]].groupby(line_id).sum().reset_index()
            out_lines = os.path.join(base, "aggs", "lines", f"{i.split('/')[-1].split('.')[0]}_lines.gpkg")
            line.merge(gdf_joined_lines, on=line_id, how='left').to_file(out_lines, driver="GPKG")
            
            gdf_joined_bands = gdf_joined_bands[fields_to_agg + ["index"]].groupby("index").sum().reset_index()
            out_bands = os.path.join(base, "aggs", "bands", f"{i.split('/')[-1].split('.')[0]}_bands.gpkg")
            bands.merge(gdf_joined_bands, on="index", how='left').to_file(out_bands, driver="GPKG")

# Main Execution
scenarios = parse_scenarios(template, BASEDIR)
scenarios = compute_cartesian_product(scenarios)
process_scenarios(scenarios, template, BASEDIR, id_prefix, rps)

base = '/app/data/USGS_USVI/AEV'
bands_path = '/app/damage_data/USVI_data/USVI_Band_Shells.zip'
lines_base = '/app/damage_data/USVI_data/CoastalSegments_ForBorja'
ids = {k: f"FID_{k[0:6]}" for k in ["StCroix", "StThomas", "StJohn"]}

process_geospatial_data(base, bands_path, lines_base, ids)