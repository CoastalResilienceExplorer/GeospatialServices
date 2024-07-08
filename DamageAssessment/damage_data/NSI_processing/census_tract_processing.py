import pandas as pd
import geopandas as gpd
import fiona
import numpy as np
import re
import logging

vuln_curves = pd.read_csv('/app/damage_data/vulnerability_curves/nsi_median_vulnerability_curves.csv')

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

def read_gdb_table(gdb_path, table_name, **kwargs):
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
        gdf = gpd.read_file(gdb_path, driver='FileGDB', layer=table_name, **kwargs)
        return gdf
    except Exception as e:
        print(f"An error occurred: {e}")
        return gpd.GeoDataFrame()
    

def convert_to_percentage(df, columns):
    """
    Convert specified columns of a dataframe to percentages of the sum across a row.

    Parameters:
    df (pd.DataFrame): The input dataframe.
    columns (list): The list of columns to be converted.

    Returns:
    pd.DataFrame: A new dataframe with specified columns converted to percentages.
    """
    df_copy = df.copy()
    row_sums = df_copy[columns].sum(axis=1)
    for column in columns:
        df_copy[column] = df_copy[column] / row_sums
    return df_copy

def filter_columns_by_prefix(df, prefixes):
    """
    Filter columns of a dataframe that start with one of the specified prefixes.

    Parameters:
    df (pd.DataFrame): The input dataframe.
    prefixes (list): The list of prefixes to filter columns by.

    Returns:
    pd.DataFrame: A dataframe with columns that start with one of the specified prefixes.
    """
    filtered_columns = [col for col in df.columns if any(col.startswith(prefix) for prefix in prefixes)]
    return df[filtered_columns]


def rename_columns(df, cols):
    new_cols = {col: col.split(" - ")[0] for col in cols}
    return (
        df.rename(columns=new_cols),
        new_cols.values()
    )
    

def remove_trailing_letters(s):
    """
    Remove trailing letters from each string in the list.

    Parameters:
    strings (list of str): List of strings to process.

    Returns:
    list of str: List of strings with trailing letters removed.
    """
    import re
    return re.sub(r'[a-zA-Z]+$', '', s)


def process_dataframes(df1, df2, id_column, column_mapping, column_to_match, column_identifier_regex):
    """
    Get a weighted mean of rows in df2, using weights from the columns of df1

    Parameters:
    df1 Dataframe of weights
    df2 Dataframe to get weighted mean from
    id_column Column to group by
    column_mapping Mapping of columns to vulnerability curve
    column_to_match Column to match on in df2
    column_identifier_regex Regex to identify columns to match on in df2

    Returns:
    list of str: List of strings with trailing letters removed.
    """
    import pandas as pd
    
    def process_row(row, id_column):
        results = []
        for key, value in column_mapping.items():
            perc = row[key]
            matching_rows = df2[df2[column_to_match] == value]
            if (matching_rows.shape[0] == 0):
                raise ValueError
            
            filtered_columns = [col for col in matching_rows.columns if re.search(column_identifier_regex, col)]
            if not filtered_columns:
                raise ValueError
            
            mean_values = matching_rows[filtered_columns].mean(axis=0)
            weighted_mean = mean_values * perc
            results.append(weighted_mean)
        
        if results:
            combined_df = pd.concat(results, axis=1).sum(axis=1)
            combined_df[id_column] = row[id_column]
            return combined_df
        else:
            raise ValueError
        
    results = df1.apply(lambda row: process_row(row, id_column), axis=1)
    return results






ID_COL = "Block"
gdb_path = "/app/damage_data/National.gdb"
census_occupancy_counts = f"BuildingCountByOccupancyCensus{ID_COL}"
census_values = f"BuildingContentFullReplacementValueByOccupancyCensus{ID_COL}Level"
StateAbbr = "VI"
structure_types = ("RES", "COM", "IND", "AGR", "REL", "GOV", "EDU")


occupancies = pd.read_csv('/app/BuildingCountByOccupancyCensusBlock_VI.csv')
occupancies_columns = filter_columns_by_prefix(occupancies, structure_types)
gdf, columns = rename_columns(occupancies, occupancies_columns)
column_mapping_to_nsi = {
    c: remove_trailing_letters(c)
    for c in columns
}
frequencies = convert_to_percentage(gdf, columns)
frequencies = filter_columns_by_prefix(frequencies, structure_types + ("CensusBlock",)).set_index("CensusBlock")
weighted_vulnerability_curves = process_dataframes(frequencies, vuln_curves, "CensusBlock", column_mapping_to_nsi, "Occupancy", r'^m\d*\.?\d*$')

values = pd.read_csv('/app/BuildingContentFullReplacementValueByOccupancyCensusBlockLevel_VI.csv')
values = filter_columns_by_prefix(values, structure_types + ("CensusBlock",)).set_index("CensusBlock")
values = values * 1000
column_mapping_to_nsi = {
    c: remove_trailing_letters(c)
    for c in values.columns
}

values = values.sort_index()
frequencies = frequencies.sort_index()

weighted_values = (frequencies[columns] * values[columns])
weighted_values = weighted_values.sum(axis=1).rename("OccupancyWeightedValue")

weighted_vulnerability_curves = weighted_vulnerability_curves.set_index("CensusBlock")

composite_values = pd.merge(weighted_vulnerability_curves, weighted_values, left_index=True, right_index=True)
composite_values.to_csv(f"/app/damage_data/vulnerability_curves/{StateAbbr}_{ID_COL}_weighted_vulnerability_curves_and_values.csv")

geogs = gpd.read_file("/app/damage_data/CensusBlock_VI.gpkg")
geogs = geogs[geogs["StateAbbr"] == StateAbbr].set_index("CensusBlock")
composite_values.index = composite_values.index.astype(int).astype(str)
geogs = pd.merge(geogs, composite_values, left_index=True, right_index=True)
geogs.to_file(f"/app/damage_data/vulnerability_curves/{StateAbbr}_{ID_COL}_weighted_vulnerability_curves_and_values.gpkg")


