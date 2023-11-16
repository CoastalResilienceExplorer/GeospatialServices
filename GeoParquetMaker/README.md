## Purpose
This service creates GeoParquets from GDAL-compatible vector formats and uploads to Geoparquet.  It implements basic partitioning using ISO country code and S2 cells.

### Example of reading 
```
data = pd.read_parquet(remote_path)
gdf = gpd.GeoDataFrame(
    data, geometry=gpd.GeoSeries.from_wkb(data["geometry"])
)
```
