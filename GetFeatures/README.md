# Service for downloading geospatial features
Currently designed to work with OSM and OpenBuildings. but can easily be extended to any large datasets which are created and partitioned with `GeoParquetMaker`.

### To Build and Run Locally
```
ENV=dev
IMAGE=cog2extent-${ENV}
BASE_GAR_DIRECTORY=us-west1-docker.pkg.dev/global-mangroves
BASE_IMAGE=${BASE_GAR_DIRECTORY}/base/python_gis_base_${ENV}
docker build -t $IMAGE --build-arg BASE_IMAGE=$BASE_IMAGE .
```

```
docker run \
    --cap-add SYS_ADMIN --device /dev/fuse \
    -v $HOME/.config/gcloud:/root/.config/gcloud \
    -v $PWD:/app \
    -e MNT_BUCKETS="supporting-data2" \
    -it \
    -p 3003:8080 \
    $IMAGE
```

### Examples
To download, see the `tools/trigger` scripts.

### Next Up
This is eventually working it's way up to include the following:
- bindings to the ArcGIS Online Catalog
- application of damage statistics

The latter of these has been implemented for one specific project (see `san_mateo.py`), but needs a fair amount of thought and abstraction, mostly about how to classify features to apply appropriate vulnerability curves.