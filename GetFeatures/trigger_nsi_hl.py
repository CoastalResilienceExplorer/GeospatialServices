import requests, os, io
import geopandas as gpd, pandas as pd
from utils.AEV import calculate_AEV

from utils.timing import timeit


slr = ["0", "05", "1"]
scenarios = ["1_100HL", "noHL"]
BASE_DIR = "/Users/chlowrie/Desktop/OPC/floodmaps/HorizontalLevees/"
dmg_prefix = "percent_damage_"
POP_FLOOD_CUTOFF = 0.1

# nsi_response = requests.post(
#     "http://localhost:3002/get_nsi/",
#     files={"z": open(os.path.join(BASE_DIR, f"flooddepth_1_100HL_1SLR.tif"), "rb")},
# )
# gdf = gpd.read_file(io.BytesIO(nsi_response.content), driver="GPKG")

ids = []

@timeit
def build_results(gdf):
    for sea_level in slr:
        for scenario in scenarios:
            id = f"flooddepth_{scenario}_{sea_level}SLR"
            f = os.path.join(BASE_DIR, f"{id}.tif")
            x = requests.post(
                "http://localhost:3002/get_building_damages/",
                files={"z": open(f, "rb")},
                data={
                    "features_from": "NSI",
                    "id": id,
                    "offset_column": "found_ht",
                    "offset_units": "ft",
                },
            )
            gdf_to_add = gpd.read_file(io.BytesIO(x.content), driver="GPKG")
            gdf = pd.merge(
                gdf,
                gdf_to_add[[c for c in gdf_to_add.columns if id in c] + ["fd_id"]],
                on="fd_id",
                how="outer",
            )
            gdf[f"EconFlooded_{id}"] = gdf.apply(
                lambda row: (row[id] * (row["val_struct"] + row["val_cont"])),
                axis=1,
            )
            gdf[f"PopFlooded_{id}"] = gdf.apply(
                lambda row: (row[id] > POP_FLOOD_CUTOFF) * (row["pop2amu65"] + row["pop2amo65"]),
                axis=1,
            )
            ids.append(id)
    gdf.to_file(f"./results/nsi_buildings_HL_sanmateo_damages.gpkg")
    return f"./results/nsi_buildings_HL_sanmateo_damages.gpkg"


# results = build_results(gdf)
results = f"./results/nsi_buildings_HL_sanmateo_damages.gpkg"
results = gpd.read_file(results)

ids = []
for sea_level in slr:
    for scenario in scenarios:
        ids.append(f"flooddepth_{scenario}_{sea_level}SLR")

print(ids)
dmg_cols = list(set([c for c in results.columns for i in ids if i in c and c not in ids and 'percent_damage' not in c]))
print(dmg_cols)

regions = {
    "BCDC": {"path": "./data/regions/BCDC.gpkg", "grouping_cols": ["GEOID"]},
    "CES4": {"path": "./data/regions/CES4.gpkg", "grouping_cols": ["Tract"]},
}

for k, v in regions.items():
    region = gpd.read_file(v["path"])
    grouped = gpd.sjoin(region, results, how="left")[v["grouping_cols"] + dmg_cols]
    grouped[dmg_cols] = grouped[dmg_cols].fillna(0)
    grouped = grouped.groupby(v["grouping_cols"]).sum()
    grouped = region.set_index(v["grouping_cols"]).merge(
        grouped, how="left", left_index=True, right_index=True
    )
    print(grouped)
    for sl in slr:
        grouped[f"AEB_Econ_sl{sl}"] = grouped[f"EconFlooded_flooddepth_noHL_{sl}SLR"] - grouped[f"EconFlooded_flooddepth_1_100HL_{sl}SLR"]
        grouped[f"AEB_Pop_sl{sl}"] = grouped[f"PopFlooded_flooddepth_noHL_{sl}SLR"] - grouped[f"PopFlooded_flooddepth_1_100HL_{sl}SLR"]
    grouped.to_file(f"./results/{k}_hl_results.gpkg")
