## Purpose
To auto-generate Cloud-Optimized GeoTiffs.
To prevent PubSub from retrying on a long-running task, I had to use a front service that forwards the requests.

## TODOs
- Error handling in Eventarc.  Currently Eventarc keeps retrying, we need it to just fail, and ideally to notify us.
- Add success/failure notifications on completion.
- Proper testing.

### Sources
- https://gdal.org/drivers/raster/cog.html
- https://cloud.google.com/eventarc/docs/run/create-trigger-storage-gcloud#python
- https://github.com/GoogleCloudPlatform/python-docs-samples/blob/main/eventarc/storage_handler/main.py

### GCP Consoles
- https://console.cloud.google.com/eventarc/triggers?project=global-mangroves
- https://console.cloud.google.com/storage/browser/test-tiff-to-cog/test?pageState=(%22StorageObjectListTable%22:(%22f%22:%22%255B%255D%22))&project=global-mangroves&prefix=&forceOnObjectsSortingFiltering=false
- https://console.cloud.google.com/storage/browser/cloud-native-geospatial/test;tab=objects?project=global-mangroves&prefix=&forceOnObjectsSortingFiltering=false
- https://console.cloud.google.com/run/detail/us-west1/cogmaker-staging/logs?project=global-mangroves

### Local Development
ENV=staging
docker build -t cogmaker --build-arg BASE_IMAGE=us-west1-docker.pkg.dev/global-mangroves/base/python_gis_base_${ENV} .
docker run -it -v $PWD:/app -v $HOME/.config/gcloud/:/root/.config/gcloud -p 3004:8080 --env OUTPUT_BUCKET=cogmaker-output-${ENV} cogmaker app:app --reload --host 0.0.0.0 --port 8080