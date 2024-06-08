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


import xarray as xr
import numpy as np
from shapely.geometry import Polygon, Point, MultiLineString, LineString, MultiPolygon
from scipy.spatial import cKDTree

from utils.dataset import compressRaster

import logging

def calculate_distances_to_multipolygon(xr_obj, boundary, op=np.max):
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

    def get_dist(polygon, pt):
        if isinstance(polygon, shapely.geometry.LineString):
            return polygon.distance(pt)

        else:
            if not polygon.contains(pt):
                return 0
            else:
                return polygon.exterior.distance(pt)


    if isinstance(boundary, shapely.geometry.MultiPolygon) or isinstance(boundary, shapely.geometry.MultiLineString):
        distances_buff = []
        for polygon in boundary.geoms:
            logging.info('xxx')
            distances = [
                get_dist(polygon, Point(*c)) 
                for c in coords
            ]
            distances_buff.append(distances)
        distances = op(distances_buff, axis=0)

    data = np.reshape(distances, [ds_clipped.shape[1], ds_clipped.shape[0]])
    data_array = xr.DataArray(
        data, 
        coords={"y": ds_clipped.y, "x": ds_clipped.x}, 
        dims=["x", "y"],
        attrs={}
    ).transpose('y', 'x')

    data_array.rio.write_crs(xr_obj.rio.crs, inplace=True)
    return data_array
    x = xr_obj.coords['x'].values
    y = xr_obj.coords['y'].values
    x_grid, y_grid = np.meshgrid(x, y)
    
    # Flatten the grids to create a list of points
    points = np.vstack((x_grid.ravel(), y_grid.ravel())).T
    
    # Create a list of all polygon boundary points in the MultiPolygon
    polygon_points = np.vstack([np.array(polygon.exterior.coords) for polygon in multipolygon.geoms])
    
    # Create a KDTree for the polygon boundary points
    tree = cKDTree(polygon_points)
    
    # Calculate distances to the nearest polygon point
    distances, _ = tree.query(points)
    
    # Check which points are inside any of the polygons
    points_inside = np.array([multipolygon.contains(Point(p)) for p in points])
    
    # Set distances to NaN for points outside the polygons
    distances[~points_inside] = np.nan
    
    # Reshape the distances to match the original grid shape
    distances = distances.reshape(x_grid.shape)
    
    # Create a new xarray DataArray with the distances
    distance_da = xr.DataArray(distances, coords=xr_obj.coords, dims=xr_obj.dims)
    
    return distance_da



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


def mosaic_xarray(arr1, arr2):

    # Calculate Polygons
    p1 = xr_vectorize(arr1>0, coarsen_by=1)
    p2 = xr_vectorize(arr2>0, coarsen_by=1)
    p1 = unary_union(p1.geometry)
    p2 = unary_union(p2.geometry)

    def to_line(p):
        if isinstance(p, shapely.geometry.MultiPolygon):
            return MultiLineString([LineString(polygon.exterior.coords) for polygon in p.geoms])
        return MultiLineString(p.exterior.coords)


    intersection_polygon=p1.intersection(p2)
    l1 = to_line(p1).intersection(intersection_polygon)
    l2 = to_line(p2).intersection(intersection_polygon)

    logging.info(len(intersection_polygon.geoms))
    logging.info(len(l1.geoms))
    # p2.to_file('p2.gpkg')
    d1 = calculate_distances_to_multipolygon(arr1, intersection_polygon)
    dl1 = calculate_distances_to_multipolygon(arr1, l1, op=np.min)
    dl2 = calculate_distances_to_multipolygon(arr1, l2, op=np.min)

    compressRaster(d1, "test_poly.tif")
    compressRaster(dl1, "test_line1.tif")
    compressRaster(dl2, "test_line2.tif")
    # logging.info(d1)
    # del d1.attrs['grid_mapping']
    # d1.rio.write_crs(arr1.rio.crs, inplace=True)
    # compressRaster(d1, 'test.tif')
    return
    d2 = calculate_distances_to_multipolygon(arr2, p2)
    d1.rio.to_raster('d1.tif')
    d2.rio.to_raster('d2.tif')

    return

    # Determine the bounds of the new mosaic
    y_min = min(arr1.y.min().item(), arr2.y.min().item())
    y_max = max(arr1.y.max().item(), arr2.y.max().item())
    x_min = min(arr1.x.min().item(), arr2.x.min().item())
    x_max = max(arr1.x.max().item(), arr2.x.max().item())

    # Determine the common resolution (assume regular grids and identical resolutions)
    y_res = min(np.abs(arr1.y[1] - arr1.y[0]).item(), np.abs(arr2.y[1] - arr2.y[0]).item())
    x_res = min(np.abs(arr1.x[1] - arr1.x[0]).item(), np.abs(arr2.x[1] - arr2.x[0]).item())

    # Create new coordinates
    new_y = np.arange(y_min, y_max + y_res, y_res)
    new_x = np.arange(x_min, x_max + x_res, x_res)

    # Create a new DataArray with the expanded coordinates filled with NaNs
    new_shape = (len(new_y), len(new_x))
    new_data1 = np.full(new_shape, np.nan)
    new_data2 = np.full(new_shape, np.nan)

    new_arr1 = xr.DataArray(new_data1, coords=[new_y, new_x], dims=["y", "x"])
    new_arr2 = xr.DataArray(new_data2, coords=[new_y, new_x], dims=["y", "x"])

    # Reindex the original arrays to the new coordinates
    arr1_reindexed = arr1.reindex_like(new_arr1, method="nearest")
    arr2_reindexed = arr2.reindex_like(new_arr2, method="nearest")

    # Merge the two arrays
    combined_data = np.nanmax(np.stack([arr1_reindexed, arr2_reindexed], axis=0), axis=0)

    # Create the final mosaic array
    mosaic = xr.DataArray(combined_data, coords=[new_y, new_x], dims=["y", "x"])

    return mosaic


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