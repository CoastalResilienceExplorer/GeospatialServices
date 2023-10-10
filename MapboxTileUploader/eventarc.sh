ENV=${1:?"Must set environment as first arg"}
echo $ENV

VECTORUPLOADER_SERVICE=${2:?"Must set VectorUploader service"}

gcloud eventarc triggers delete storage-events-trigger-$ENV \
     --location=us-west1
     
gcloud eventarc triggers create storage-events-trigger-$ENV \
     --location=us-west1 \
     --destination-run-service=$VECTORUPLOADER_SERVICE \
     --destination-run-region=us-west1 \
     --event-filters="type=google.cloud.storage.object.v1.finalized" \
     --event-filters="bucket=cloud-native-geospatial/vector-uploader" \
     --service-account="geoparquet-maker@global-mangroves.iam.gserviceaccount.com"
