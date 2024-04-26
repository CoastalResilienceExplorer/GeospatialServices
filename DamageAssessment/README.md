## Damage Assessment from Global Urban Footprint
This directory contains code for running damage and exposure assessments.  It references:
- Damage functions and max damage values from [JRC](https://publications.jrc.ec.europa.eu/repository/handle/JRC105688).
- Urban Footprint data from [Global Urban Footprint](https://www.dlr.de/eoc/en/desktopdefault.aspx/tabid-9628/).
- Population from [Global Human Settlement Layer](https://ghsl.jrc.ec.europa.eu/download.php?ds=pop).
- [National Structure Inventory](https://nsi.sec.usace.army.mil/downloads/) data for California, Hawaii, and Florida


### Workflow
The code takes a raster input representing a georeferenced floodmap, and returns a raster output representing a damage or exposure layer.  It reindexes the Global Urban Footprint data to match the floodmap, and calculates the damage at each cell.

If running as a server, the return response is a Geotiff.  If running as a Python import, the returned response is a Rioxarray object.  
Data is also posted up to Google Cloud Storage when running from server.

### To Run From Server
See `tools/trigger.py`

This requires very minimal installations, specifically `pip3 install requests requests_toolbelt`.  It works as a REST API running Google Cloud Platform.

It supports three options:
- `-t damages`
- `-t population`
- `-t damages_nsi`

#### Damages
```
python3 tools/trigger.py -f ./data/belize_test_flooding.tiff -t damages -p belize -i belize_test.tiff --output ./test_damages.tiff
```

You can optionally set a population filter on the output, using `--window_size 500 --population_min 10` (or some other values)
- `window_size` controls the windowing of population in meters
- `population_min` controls the minimum population summed over the window for which to return results.  

So, `--window_size 500 --population_min 10` means "return only damages where at least 10 people live in a 500m window around the pixel"

The current iteration is hardcoded to the Americas for DDFs, and Belize for the Max Value, but it would be easy to extend this.

#### Population
```
python3 tools/trigger.py -f ./data/belize_test_flooding.tiff -t population -p belize -i belize_test.tiff --output ./test_population.tiff
```

You can optionally specify the flood depth threshold for which to return results.  The default is 0.5 meters, which indicates that people are only considered exposed to flooding if the flood depth is greater than this.


#### NSI
```
python3 tools/trigger.py -f "/Users/chlowrie/Downloads/InundationMaps_V&LA_BOUS/Ventura/SLR_1.5/VE02_flddepth_SLR150_W100.tif" -t damages_nsi --nsi california --output ./test_nsi.gpkg 

# Remote output is currently not supported for NSI outputs, just downloads to local
# --project test --id test/test_nsi.geoparquet

```

Currently it is required to specify the state you are running in with the `--nsi` parameter.


### Other Notes
#### Remote Output
`REMOTE_OUTPUT` is stored in `cogmaker-output-staging` for `damages` and `population`.

### Building Locally
```
ENV=staging
IMAGE=us-west1-docker.pkg.dev/global-mangroves/damages/damages-${ENV}
docker build \
    -t $IMAGE \
    -f new.Dockerfile \
    --build-arg BASE_IMAGE=us-west1-docker.pkg.dev/global-mangroves/base/python_gis_base_${ENV} \
    .

docker run -it \
    -v $PWD:/app \
    -v $HOME/.config/gcloud/:/root/.config/gcloud \
    -p 3001:8080 \
    -e OUTPUT_BUCKET_RASTER=cloud-native-geospatial \
    -e OUTPUT_BUCKET_VECTOR=cloud-native-geospatial \
    -e MNT_BASE="gs://" \
    $IMAGE
```

After doing this, you can test with the same trigger script by attaching `--local` to the call.

### Testing
The image built above includes `pytest`.
```
docker run -it \
    -v $PWD:/app \
    -v $HOME/.config/gcloud/:/root/.config/gcloud \
    -p 3001:8080 \
    -e OUTPUT_BUCKET_RASTER=cloud-native-geospatial \
    -e OUTPUT_BUCKET_VECTOR=cloud-native-geospatial \
    -e MNT_BASE="gs://" \
    -e TEST_WRITE=1 \
    --entrypoint pytest \
    $IMAGE
```