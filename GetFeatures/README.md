## To access tiles

## To Run Locally
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
    -e MNT_BUCKETS="cloud-native-geospatial;supporting-data2" \
    -it \
    -p 3000:8080 \
    $IMAGE
```

To download:
```
curl -X POST http://localhost:3000/get_features/ \
   -H "Content-Type: application/json" \
   -d '{"features_file": "supporting-data2/google-microsoft-open-buildings.parquet/country_iso=USA/", "raster": "cogmaker-output-staging/hmax_rp_500_rest_150.tiff" }' > features.gpkg
```