ENV=${1:?"Must set environment as first arg"}
echo $ENV

COGMAKER_SERVICE=${2:?"Must set Cogmaker service"}
ID=cogmaker

gcloud eventarc triggers delete ${ID}-trigger-$ENV \
     --location=us-west1
     
gcloud eventarc triggers create ${ID}-trigger-$ENV \
     --location=us-west1 \
     --destination-run-service=$COGMAKER_SERVICE \
     --destination-run-region=us-west1 \
     --event-filters="type=google.cloud.storage.object.v1.finalized" \
     --event-filters="bucket=test-tiff-to-cog" \
     --service-account="cog-maker@global-mangroves.iam.gserviceaccount.com"
