### Local Testing
```
ENV=dev
BASE_GAR_DIRECTORY=us-west1-docker.pkg.dev/global-mangroves
BASE_IMAGE=${BASE_GAR_DIRECTORY}/base/python_gis_base_${ENV}
docker build -t xb2zarr --build-arg BASE_IMAGE=$BASE_IMAGE .
docker run -it \
    --cap-add SYS_ADMIN --device /dev/fuse \
    -v $HOME/.config/gcloud:/root/.config/gcloud \
    -e MNT_BUCKETS="xbeach-outputs;xb2zarr" \
    -e OUTPUT_BUCKET=xb2zarr \
    -p 3002:8080 \
    -v $PWD:/app \
    xb2zarr
```