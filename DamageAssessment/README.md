## Damage Assessment from Global Urban Footprint
This directory contains code for running damage assessments using Global Urban Footprint.  It references damage functions and max damage values from [JRC](https://publications.jrc.ec.europa.eu/repository/handle/JRC105688).

The current iteration is hardcoded to the Americas for DDFs, but it would be easy to extend this.

### Workflow
The code takes a raster input representing a georeferenced floodmap, and returns a raster output representing a damage layer.  It reindexes the Global Urban Footprint data to match the floodmap, and calculates the damage at each cell.

If running as a server, the return response is a GZipped Geotiff, and data is also posted up to Google Cloud Storage.

### To Run From Server
See `tools/trigger.sh`
```
INPUT="/Users/chlowrie/Desktop/TestData/belize_sfincs_MANGROVELIMIT_LWM_MANNING_090020_hmax.tif"
REMOTE_OUTPUT="belize/belize_test.tiff"
LOCAL_OUTPUT="/Users/chlowrie/Desktop/TestData/BelizeTest.tiff"

bash tools/trigger.sh \
    $INPUT \
    $REMOTE_OUTPUT \
    $LOCAL_OUTPUT
```

`REMOTE_OUTPUT` is stored in `cogmaker-output-staging`.

### Building Locally
```
docker build \
    --build-arg BASE_IMAGE=us-west1-docker.pkg.dev/global-mangroves/base/python_gis_base_staging \
    -t us-west1-docker.pkg.dev/global-mangroves/damages/damages-staging .

docker run -it \
    -v $PWD:/app \
    -v $HOME/.config/gcloud/:/root/.config/gcloud \
    -p 3001:8080 \
    us-west1-docker.pkg.dev/global-mangroves/damages/damages-staging
```