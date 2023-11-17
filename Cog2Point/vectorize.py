import xarray as xr
import geopandas as gpd
import rasterio
import odc.geo.xr
from shapely.geometry import shape
import uuid, os


def xr_vectorize(
    da,
    attribute_col=None,
    crs=None,
    dtype="float32",
    output_path=None,
    verbose=True,
    **rasterio_kwargs,
):
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
    print("vectorizing")
    print(da)
    da = da > 0
    print(da)
    # Run the vectorizing function
    vectors = rasterio.features.shapes(
        source=da.data.astype(dtype), transform=da.odc.transform, **rasterio_kwargs
    )

    # Convert the generator into a list
    vectors = list(vectors)
    print(vectors)

    # # Extract the polygon coordinates and values from the list
    polygons = [polygon for polygon, value in vectors]
    values = [value for polygon, value in vectors]

    # # Convert polygon coordinates into polygon shapes
    polygons = [shape(polygon) for polygon in polygons]

    # # Create a geopandas dataframe populated with the polygon shapes
    attribute_name = attribute_col if attribute_col is not None else "attribute"
    gdf = gpd.GeoDataFrame(
        data={attribute_name: values}, geometry=polygons, crs=da.odc.crs
    )

    # If a file path is supplied, export to file
    if output_path is not None:
        if verbose:
            print(f"Exporting vector data to {output_path}")
        gdf.to_parquet(os.path.join(output_path, f'{str(uuid.uuid1())}.parquet'))

    return gdf
