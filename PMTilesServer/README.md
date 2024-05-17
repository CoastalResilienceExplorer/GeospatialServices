## To access tiles

## To Run Locally

ENV=staging
docker build -t us-west1-docker.pkg.dev/global-mangroves/mbtileserver/pmtileserver-${ENV} .

docker run \
    -e BUCKET=geoparquet2pmtiles-output-${ENV} \
    --cap-add SYS_ADMIN --device /dev/fuse \
    -v $HOME/.config/gcloud:/root/.config/gcloud \
    -v $PWD:/app \
    -p 3002:8080 \
    -it \
    us-west1-docker.pkg.dev/global-mangroves/mbtileserver/pmtileserver-${ENV}:latest