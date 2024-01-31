import requests, os, io
import geopandas as gpd, pandas as pd
from utils.AEV import calculate_AEV

from utils.timing import timeit


slr = ["0", "05", "1"]
marsh = ["e", "r"]
rps = [1, 20, 100]
BASE_DIR = "/Users/chlowrie/Desktop/OPC/floodmaps/MarshScenarios/"
dmg_prefix = "percent_damage_"
POP_FLOOD_CUTOFF = 0.1

# nsi_response = requests.post(
#     "http://localhost:3002/get_nsi/",
#     files={"z": open(os.path.join(BASE_DIR, f"1e100.tif"), "rb")},
# )
# gdf = gpd.read_file(io.BytesIO(nsi_response.content), driver="GPKG")


@timeit
def build_results(gdf):
    for sea_level in slr:
        for scenario in marsh:
            ids = []
            for rp in rps:
                id = f"{sea_level}{scenario}{rp}"
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
                print(id)
                ids.append(id)
            print(gdf)
            dmg_columns = [f"{dmg_prefix}{i}" for i in ids]
            gdf[dmg_columns] = gdf[dmg_columns].fillna(0)
            gdf[ids] = gdf[ids].fillna(0)
            gdf[f"AEV_Econ_{sea_level}{scenario}"] = gdf.apply(
                lambda row: calculate_AEV(
                    rps,
                    [
                        row[c] * (row["val_struct"] + row["val_cont"])
                        for c in dmg_columns
                    ],
                ),
                axis=1,
            )
            gdf[f"AEV_Pop_{sea_level}{scenario}"] = gdf.apply(
                lambda row: calculate_AEV(
                    rps,
                    [
                        (row[c] > POP_FLOOD_CUTOFF)
                        * (row["pop2amu65"] + row["pop2amo65"])
                        for c in dmg_columns
                    ],
                ),
                axis=1,
            )
        gdf.to_file(f"./results/sl{sea_level}.gpkg")
    gdf.to_file(f"./results/nsi_buildings_sanmateo_damages.gpkg")
    return f"./results/nsi_buildings_sanmateo_damages.gpkg"


# build_results(gdf)
results = f"./results/nsi_buildings_sanmateo_damages.gpkg"
results = gpd.read_file(results)

ids = []
for sea_level in slr:
    for scenario in marsh:
        ids.append(f"{sea_level}{scenario}")
        for rp in rps:
            ids.append(f"{sea_level}{scenario}{rp}")

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
        grouped[f"AEB_Econ_sl{sl}"] = grouped[f"AEV_Econ_{sl}e"] - grouped[f"AEV_Econ_{sl}r"]
        grouped[f"AEB_Pop_sl{sl}"] = grouped[f"AEV_Pop_{sl}e"] - grouped[f"AEV_Pop_{sl}r"]
    grouped.to_file(f"./results/{k}_results.gpkg")
