ENV=${1:?"Must set environment as first arg"}
echo $ENV
BASE_GAR_DIRECTORY=us-west1-docker.pkg.dev/global-mangroves
IMAGE=${BASE_GAR_DIRECTORY}/mbtileserver/pmtileserver-${ENV}
SERVICE=pmtileserver-${ENV}
BUCKET=geoparquet2mbtiles-output-${ENV}

gcloud run deploy $SERVICE --source . \
    --execution-environment gen2 \
    --allow-unauthenticated \
    --service-account cog-maker@global-mangroves.iam.gserviceaccount.com \
    --set-env-vars BUCKET=${BUCKET} \
    --region us-west1

# echo """
# steps:
# - name: 'gcr.io/cloud-builders/docker'
#   args: ['build', '-t', '$IMAGE', '.']
#   dir: '.'
# - name: 'gcr.io/cloud-builders/docker'
#   args: ['push', '$IMAGE']
# - name: 'gcr.io/cloud-builders/gcloud'
#   args: ['run', 'deploy', 
#     '$SERVICE', 
#     '--execution-environment', 'gen2',
#     '--image', '$IMAGE', 
#     '--allow-unauthenticated', 
#     '--region', 'us-west1', 
#     '--service-account', 'fs-identity',
#     '--update-env-vars', 'BUCKET=${BUCKET}'
#     ]
# """ > /tmp/cloudbuild.yaml

# gcloud builds submit \
#     --config /tmp/cloudbuild.yaml

# Test
# TODO, implement a proper test that fails
