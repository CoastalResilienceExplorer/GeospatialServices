import rasterio
from shapely.geometry import shape
import geopandas as gpd
import odc.geo.xr
import xarray as xr
import numpy as np
from rasterio.sample import sample_gen
from utils.cache import memoize_geospatial_with_persistence

import pyproj
from shapely.geometry import Point
from shapely.ops import transform

import copy


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


# @memoize_geospatial_with_persistence('/tmp/extract_points.pkl')
def extract_z_values(ds, gdf, column_name, offset_column, offset_units) -> gpd.GeoDataFrame:
    # note the extra 'z' dimension that our results will be organized along
    da_x = xr.DataArray(gdf.geometry.x.values, dims=['z'])
    da_y = xr.DataArray(gdf.geometry.y.values, dims=['z'])
    results = ds.sel(x=da_x, y=da_y, method='nearest')
    gdf[column_name] = results.values
    gdf[column_name][gdf[column_name] == ds.rio.nodata] = 0
    gdf[column_name][gdf[column_name].isna()] = 0
    if offset_units == "ft":
        offset = gdf[offset_column] * 0.3048
    else:
        offset = gdf[offset_column]
    gdf[column_name] = gdf[column_name] - offset
    return gdf

# Convert GeoJSON to GeoDataFrame
def geojson_to_geodataframe(geojson):
    features = geojson["features"]
    geometries = [shape(feature["geometry"]) for feature in features]
    properties = [feature["properties"] for feature in features]
    gdf = gpd.GeoDataFrame(properties, geometry=geometries)
    return gdf


def transform_point(x, y, crs):
    pt = Point(x, y)
    init_crs = pyproj.CRS(crs)
    wgs84 = pyproj.CRS('EPSG:4326')
    project = pyproj.Transformer.from_crs(init_crs, wgs84, always_xy=True).transform
    return transform(project, pt)


def rescale_raster(ds):
    print(ds.attrs)
    ds = copy.deepcopy(ds)
    ds = ds.where(ds != ds.attrs['_FillValue'], 0)
    # rxr doesn't respect integer scaling when running selects, so we need to do it manually.
    # Might be nice to wrap this into our own rxr import
    ds = ds * ds.attrs['scale_factor'] + ds.attrs['add_offset']
    return ds