ENV=${1:?"Must set environment as first arg"}
echo $ENV
BASE_GAR_DIRECTORY=us-west1-docker.pkg.dev/global-mangroves
BASE_IMAGE=${BASE_GAR_DIRECTORY}/base/python_gis_base_${ENV}
VECTORUPLOADER_IMAGE=${BASE_GAR_DIRECTORY}/vectoruploader/vectoruploader_${ENV}
VECTORUPLOADER_SERVICE=vectoruploader-${ENV}
VECTORUPLOADER_SERVICE_FRONT=vectoruploader-front-${ENV}

echo """
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '--build-arg', 'BASE_IMAGE=$BASE_IMAGE', '-t', '$VECTORUPLOADER_IMAGE', '.']
  dir: '.'
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '$VECTORUPLOADER_IMAGE']
- name: 'gcr.io/cloud-builders/gcloud'
  args: ['run', 'deploy', 
    '$VECTORUPLOADER_SERVICE', 
    '--image', '$VECTORUPLOADER_IMAGE', 
    '--set-env-vars', 'MAPBOX_ACCESS_TOKEN=<secret>',
    '--set-env-vars', 'MAPBOX_USERNAME=clowrie',
    '--allow-unauthenticated', 
    '--region', 'us-west1', 
    '--service-account', 'cog-maker@global-mangroves.iam.gserviceaccount.com',
    '--cpu', '4',
    '--memory', '16G',
    '--timeout', '3600'
    ]
- name: 'gcr.io/cloud-builders/gcloud'
  args: ['run', 'deploy', 
    '${VECTORUPLOADER_SERVICE_FRONT}', 
    '--image', '$VECTORUPLOADER_IMAGE', 
    '--set-env-vars', 'FORWARD_SERVICE=$(gcloud run services describe $VECTORUPLOADER_SERVICE --platform managed --region us-west1 --format 'value(status.url)')',
    '--set-env-vars', 'FORWARD_PATH=/mapbox_upload/',
    '--allow-unauthenticated', 
    '--region', 'us-west1', 
    '--service-account', 'cog-maker@global-mangroves.iam.gserviceaccount.com'
    ]
images:
# - $BASE_IMAGE
- $VECTORUPLOADER_IMAGE
""" > /tmp/cloudbuild.yaml

gcloud builds submit \
    --config /tmp/cloudbuild.yaml

bash ./eventarc.sh $ENV $VECTORUPLOADER_SERVICE_FRONT

# Test
# TODO, implement a proper test that fails
