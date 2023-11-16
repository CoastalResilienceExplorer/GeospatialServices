## To access tiles

## To Run Locally
docker run \
    -e BUCKET=vector-uploader \
    --cap-add SYS_ADMIN --device /dev/fuse \
    -v $HOME/.config/gcloud:/root/.config/gcloud \
    -v $PWD:/app \
    -it \
    us-west1-docker.pkg.dev/global-mangroves/mbtileserver/mbtileserver-dev:latest