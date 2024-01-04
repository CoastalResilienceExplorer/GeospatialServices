### Local Testing
ENV=dev
BASE_GAR_DIRECTORY=us-west1-docker.pkg.dev/global-mangroves
BASE_IMAGE=${BASE_GAR_DIRECTORY}/base/python_gis_base_${ENV}
docker build -t xb2zarr --build-arg BASE_IMAGE=$BASE_IMAGE .
docker run -it -v $HOME/.config/gcloud:/root/.config/gcloud -e OUTPUT_BUCKET=geopmaker-output-staging -p 3002:8080 -v $PWD:/app xb2zarr