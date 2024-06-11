import pandas as pd
import geopandas as gpd
import fiona
import numpy as np

vuln_curves = pd.read_csv('../vulnerability_curves/nsi_median_vulnerability_curves.csv')

def list_gdb_layers(gdb_path):
    """
    Lists the available layers in a Geodatabase.

    Parameters:
    gdb_path (str): The path to the Geodatabase.

    Returns:
    list: A list of layer names available in the Geodatabase.
    """
    try:
        # Use fiona to open the Geodatabase and list layers
        layers = fiona.listlayers(gdb_path)
        return layers
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def read_gdb_table(gdb_path, table_name):
    """
    Reads a specific table from a Geodatabase into a GeoDataFrame.

    Parameters:
    gdb_path (str): The path to the Geodatabase.
    table_name (str): The name of the table to read.

    Returns:
    GeoDataFrame: A GeoDataFrame containing the data from the table.
    """
    try:
        # Read the table into a GeoDataFrame
        gdf = gpd.read_file(gdb_path, driver='FileGDB', layer=table_name)
        return gdf
    except Exception as e:
        print(f"An error occurred: {e}")
        return gpd.GeoDataFrame()
    
    
def get_curve_mapping(column, column_mapping):
    k = column_mapping[column]
    curve = vuln_curves[vuln_curves.Occupancy == k]
    curve["Occupancy_ID_Full"] = column
    return curve


def frequencies_to_composite_curve(freq, curves, column, curve_columns):
    damage_cols = [c for c in curves.columns if c[0] == 'm']
    total = freq[curve_columns.keys()].sum()
    damage_buff = []
    for curve in curve_columns.keys():
        damages = curves[curves[column] == curve][damage_cols].mean()
        damages = damages * freq[curve]
        damages['StateAbbr'] = freq['StateAbbr']
        damages['Tract'] = freq['Tract']
        damage_buff.append(damages)
        
    def sum_when_some_are_strings(row):
        sample = row.iloc[0]
        if isinstance(sample, str):
            return sample
        else:
            if total == 0:
                return np.nan
            return row.sum() / total
        
    
    
    combined = pd.concat(damage_buff, axis=1)  
    combined = combined.apply(lambda row: sum_when_some_are_strings(row), axis=1)
    return combined
    
    # return pd.concat(damage_buff, axis=1).sum(axis=1) / total

    
    
    
def get_representative_count(gdf):
    column_mapping = {c: c[0:-1] for c in gdf.columns if c[0:3] in ("RES", "COM", "IND", "AGR", "REL", "GOV", "EDU") }
    curves = pd.concat([get_curve_mapping(c, column_mapping) for c in column_mapping.keys()])
    return gdf.apply(lambda row: frequencies_to_composite_curve(
            row,
            curves, 
            "Occupancy_ID_Full",
            column_mapping
        ), axis=1
    )

# Example usage
gdb_path = "./National.gdb"
table_name = "BuildingCountByOccupancyCensusTract"
gdf = read_gdb_table(gdb_path, table_name)
get_representative_count( gdf).to_csv("../damage/Building_RepresentativeDDF_byCensusTract.csv")

