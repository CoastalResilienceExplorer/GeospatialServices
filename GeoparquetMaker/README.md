## Purpose
This service creates GeoParquets from GDAL-compatible vector formats and uploads to Geoparquet.  It implements basic partitioning using ISO country code and S2 cells.

### Triggering builds
The easiest way to build Geoparquets is to drop GDAL-supported files into `geopmaker-input-${ENV}`, where ENV is one of `staging`, `main`, or some other published service.  Supported files include `geojson`, `gpkg`, and `shp` (as a `zip` package).  You can view the build process in the Cloud Run logs.

When triggered this way, partitions will not currently be created.  You can also trigger with partitions via API for the relevant Cloud Run service from a file already in GCS.

ie
```
ENDPOINT={{base_url}}/build_geoparquet/

POST_DATA={
    "bucket": "geopmaker-input-staging",
    "name": "cwon-teselas/RESULTS_TESELA_2010.zip",
    "partition": true
}
```

### Example of reading 
Reading partitioned Geoparquet requires going through `pandas` before converting to `geopandas`:
```
data = pd.read_parquet(remote_path)
gdf = gpd.GeoDataFrame(
    data, geometry=gpd.GeoSeries.from_wkb(data["geometry"])
)
```

### Local Testing
ENV=staging
BASE_GAR_DIRECTORY=us-west1-docker.pkg.dev/global-mangroves
BASE_IMAGE=${BASE_GAR_DIRECTORY}/base/python_gis_base_${ENV}
docker build -t geopmaker --build-arg BASE_IMAGE=$BASE_IMAGE .
docker run -it -v $HOME/.config/gcloud:/root/.config/gcloud -e OUTPUT_BUCKET=supporting-data2 -p 3002:8080 -v $PWD:/app geopmaker