import rasterio
from shapely.geometry import shape
import geopandas as gpd
import odc.geo.xr
import xarray as xr
import numpy as np
from rasterio.sample import sample_gen

import pyproj
from shapely.geometry import Point
from shapely.ops import transform, unary_union
import shapely

from tqdm import tqdm
import xarray as xr
import numpy as np
from shapely.geometry import Polygon, Point, MultiLineString, LineString, MultiPolygon
from scipy.spatial import cKDTree
import copy

from utils.dataset import compressRaster

import logging

def calculate_distances_to_edges(xr_obj, line_feature, boundary, op=np.max):
    """
    Calculate the distance from each pixel in an xarray object to the nearest polygon in a MultiPolygon,
    setting pixel values outside the polygons to NaN.
    
    Parameters:
    xr_obj (xarray.DataArray or xarray.Dataset): The input xarray object containing spatial data.
    multipolygon (shapely.geometry.MultiPolygon): The input MultiPolygon to measure distances from.
    
    Returns:
    xarray.DataArray: An xarray DataArray with the same shape as the input, containing distances to the nearest polygon,
                      with values outside the polygons set to NaN.
    """
    # Get the dimensions and coordinates
    ds = xr_obj.compute()

    # Clip
    ds_clipped = ds.rio.clip([boundary], all_touched=True)
    ds_clipped_dict = ds_clipped.to_dict()

    # Stack
    ds_stacked = ds_clipped.stack(pt=['x','y'])
    ds_dict = ds_stacked.to_dict()
    coords = ds_dict['coords']['pt']['data']

    def get_dist(line_feature, pt):
        if not boundary.contains(pt):
            return 0
        else:
            return line_feature.distance(pt)

    distances = []
    for c in tqdm(coords):
        distances.append(
            get_dist(line_feature, Point(*c)) 
        )

    data = np.reshape(distances, [ds_clipped.shape[1], ds_clipped.shape[0]])
    data_array = xr.DataArray(
        data, 
        coords={"y": ds_clipped.y, "x": ds_clipped.x}, 
        dims=["x", "y"],
        attrs={}
    ).transpose('y', 'x')

    data_array.rio.write_crs(xr_obj.rio.crs, inplace=True)
    return data_array



# @memoize_geospatial_with_persistence('/tmp/xr_vectorize_cache.pkl')
def xr_vectorize(
    da,
    coarsen_by=50,
    attribute_col=None,
    crs=None,
    dtype="float32",
    output_path=None,
    verbose=True,
    **rasterio_kwargs,
) -> gpd.GeoDataFrame:
    """
    Vectorises a raster ``xarray.DataArray`` into a vector
    ``geopandas.GeoDataFrame``.

    Parameters
    ----------
    da : xarray.DataArray
        The input ``xarray.DataArray`` data to vectorise.
    attribute_col : str, optional
        Name of the attribute column in the resulting
        ``geopandas.GeoDataFrame``. Values from ``da`` converted
        to polygons will be assigned to this column. If None,
        the column name will default to 'attribute'.
    crs : str or CRS object, optional
        If ``da``'s coordinate reference system (CRS) cannot be
        determined, provide a CRS using this parameter.
        (e.g. 'EPSG:3577').
    dtype : str, optional
         Data type  of  must be one of int16, int32, uint8, uint16,
         or float32
    output_path : string, optional
        Provide an optional string file path to export the vectorised
        data to file. Supports any vector file formats supported by
        ``geopandas.GeoDataFrame.to_file()``.
    verbose : bool, optional
        Print debugging messages. Default True.
    **rasterio_kwargs :
        A set of keyword arguments to ``rasterio.features.shapes``.
        Can include `mask` and `connectivity`.

    Returns
    -------
    gdf : geopandas.GeoDataFrame

    """

    # Add GeoBox and odc.* accessor to array using `odc-geo`
    da = add_geobox(da, crs)
    da = xr.where(da > 0, 1, 0)
    da = da.coarsen(x=coarsen_by, y=coarsen_by, boundary='pad').max()

    # Run the vectorizing function
    vectors = rasterio.features.shapes(
        source=da.data.astype(dtype), transform=da.odc.transform, **rasterio_kwargs
    )

    # Convert the generator into a list
    vectors = list(vectors)

    # Extract the polygon coordinates and values from the list
    polygons = [polygon for polygon, value in vectors]
    values = [value for polygon, value in vectors]

    # Convert polygon coordinates into polygon shapes
    polygons = [shape(polygon) for polygon in polygons]

    # Create a geopandas dataframe populated with the polygon shapes
    attribute_name = attribute_col if attribute_col is not None else "attribute"
    gdf = gpd.GeoDataFrame(
        data={attribute_name: values}, geometry=polygons, crs=da.odc.crs
    )

    # If a file path is supplied, export to file
    if output_path is not None:
        if verbose:
            print(f"Exporting vector data to {output_path}")
        gdf.to_file(output_path)

    gdf.sindex
    return gdf[gdf["attribute"] == 1.0]


def create_encompassing_grid(arr1, arr2, buff=200):

    def is_ascending(arr):
        return np.all(arr[:-1] <= arr[1:])
    # Determine the bounds of the new mosaic
    y_min = min(arr1.y.min().item(), arr2.y.min().item())-buff
    y_max = max(arr1.y.max().item(), arr2.y.max().item())+buff
    x_min = min(arr1.x.min().item(), arr2.x.min().item())-buff
    x_max = max(arr1.x.max().item(), arr2.x.max().item())+buff

    # Determine the common resolution (assume regular grids and identical resolutions)
    y_res = min(np.abs(arr1.y[1] - arr1.y[0]).item(), np.abs(arr2.y[1] - arr2.y[0]).item())
    x_res = min(np.abs(arr1.x[1] - arr1.x[0]).item(), np.abs(arr2.x[1] - arr2.x[0]).item())

    # Create new coordinates
    new_y = np.arange(y_min, y_max + y_res, y_res)
    if not is_ascending(arr1.y):
        new_y = new_y[::-1]
    new_x = np.arange(x_min, x_max + x_res, x_res)
    if not is_ascending(arr1.x):
        new_x = new_x[::-1]

    # Create a new DataArray with the expanded coordinates filled with NaNs
    new_shape = (len(new_y), len(new_x))
    new_data1 = np.full(new_shape, np.nan)

    new_arr = xr.DataArray(new_data1, coords=[new_y, new_x], dims=["y", "x"])
    return new_arr


def add_geobox(ds, crs=None):
    """
    Ensure that an xarray DataArray has a GeoBox and .odc.* accessor
    using `odc.geo`.

    If `ds` is missing a Coordinate Reference System (CRS), this can be
    supplied using the `crs` param.

    Parameters
    ----------
    ds : xarray.Dataset or xarray.DataArray
        Input xarray object that needs to be checked for spatial
        information.
    crs : str, optional
        Coordinate Reference System (CRS) information for the input `ds`
        array. If `ds` already has a CRS, then `crs` is not required.
        Default is None.

    Returns
    -------
    xarray.Dataset or xarray.DataArray
        The input xarray object with added `.odc.x` attributes to access
        spatial information.

    """
    # If a CRS is not found, use custom provided CRS
    if ds.odc.crs is None and crs is not None:
        ds = ds.odc.assign_crs(crs)
    elif ds.odc.crs is None and crs is None:
        raise ValueError(
            "Unable to determine `ds`'s coordinate "
            "reference system (CRS). Please provide a "
            "CRS using the `crs` parameter "
            "(e.g. `crs='EPSG:3577'`)."
        )

    return ds


def update_with_coords(data1, data2):
    # Find the nearest coordinates in data1 for data2
    nearest_start_x = data1.x.sel(x=data2.x[0], method='nearest')
    nearest_start_y = data1.y.sel(y=data2.y[-1], method='nearest')    # Determine the range to replace in data1

    x_start_index = np.searchsorted(data1.x, nearest_start_x)
    x_end_index = x_start_index + len(data2.x)
    y_start_index = np.searchsorted(data1.y, nearest_start_y)
    y_end_index = y_start_index + len(data2.y)

    data1.loc[dict(x=data1.x[x_start_index:x_end_index], y=data1.y[y_start_index:y_end_index])] = data2.to_numpy()[::-1]
    
    return data1


def idw_mosaic(arr1, arr2, DEBUG=False):

    base_grid = create_encompassing_grid(arr1, arr2)
    d = np.zeros(base_grid.shape)
    base_grid.data = d

    logging.info(arr1.shape)
    logging.info(arr2.shape)
    
    arr1 = arr1.fillna(0)
    arr2 = arr2.fillna(0)
    
    l1_grid = update_with_coords(copy.deepcopy(base_grid), arr1.compute())
    l2_grid = update_with_coords(copy.deepcopy(base_grid), arr2.compute())

    l1_grid.rio.write_crs(arr1.rio.crs, inplace=True)
    l2_grid.rio.write_crs(arr2.rio.crs, inplace=True)

    l1_mask = xr.where(l1_grid > 0, 1, 0).compute()
    
    l2_mask = xr.where(l2_grid > 0, 1, 0).compute()

    # return
    # Calculate Polygons
    p1 = xr_vectorize(arr1>0, coarsen_by=1)
    p2 = xr_vectorize(arr2>0, coarsen_by=1)
    p1 = unary_union(p1.geometry)
    p2 = unary_union(p2.geometry)

    def to_line(p):
        if isinstance(p, shapely.geometry.MultiPolygon):
            return MultiLineString([LineString(polygon.exterior.coords) for polygon in p.geoms])
        return MultiLineString(p.exterior.coords)
    
    def exponential_weighting(d1, d2, lambd):
        w1 = np.exp(-lambd * d1)
        w2 = np.exp(-lambd * d2)
        sum_w = w1 + w2
        w1 /= sum_w
        w2 /= sum_w
        return w1, w2

    intersection_polygon=p1.intersection(p2)
    l1 = to_line(p1).intersection(intersection_polygon)
    l2 = to_line(p2).intersection(intersection_polygon)

    # p2.to_file('p2.gpkg')
    dl1 = calculate_distances_to_edges(l1_grid, l1, intersection_polygon)
    dl2 = calculate_distances_to_edges(l2_grid, l2, intersection_polygon)

    dl1 = xr.where(dl1 > 0, dl1, np.nan)
    dl2 = xr.where(dl2 > 0, dl2, np.nan)

    lamb = 0.5
    METHOD="IDW"
    
    if METHOD == "IDW":
        denom = dl1 + dl2
        dl1 = dl1 / denom 
        dl2 = dl2 / denom 
        
    if METHOD == "EXPO":
        dl1, dl2 = exponential_weighting(dl1, dl2, lamb)

    l1_mask = dl1.combine_first(l1_mask)
    l2_mask = dl2.combine_first(l2_mask)
    
    if DEBUG:
        compressRaster(l1_grid, "l1_grid.tif")
        compressRaster(l2_grid, "l2_grid.tif")
        compressRaster(l1_mask, "l1_mask.tif")
        compressRaster(l2_mask, "l2_mask.tif")
        
        compressRaster(dl1, "dl1.tif")
        compressRaster(dl2, "dl2.tif")
    
    to_return = l1_mask * l1_grid + l2_mask * l2_grid
    to_return.rio.write_crs(arr1.rio.crs, inplace=True)
    to_return.rio.write_nodata(0, inplace=True)
    return to_return
    

    return