ENV=${1:?"Must set environment as first arg"}
echo $ENV

GEOPARQUET_SERVICE=${2:?"Must set GeoParquetMaker service"}

gcloud eventarc triggers delete storage-events-trigger-$ENV \
     --location=us-west1
     
gcloud eventarc triggers create storage-events-trigger-$ENV \
     --location=us-west1 \
     --destination-run-service=$GEOPARQUET_SERVICE \
     --destination-run-region=us-west1 \
     --event-filters="type=google.cloud.storage.object.v1.finalized" \
     --event-filters="bucket=test-vector-server" \
     --service-account="geoparquet-maker@global-mangroves.iam.gserviceaccount.com"
