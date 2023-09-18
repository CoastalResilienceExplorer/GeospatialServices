ENV=${1:?"Must set environment as first arg"}
echo $ENV
BASE_GAR_DIRECTORY=us-west1-docker.pkg.dev/global-mangroves
BASE_IMAGE=${BASE_GAR_DIRECTORY}/base/python_gis_base_${ENV}
GEOPMAKER_IMAGE=${BASE_GAR_DIRECTORY}/geoparquetmaker/geoparquetmaker${ENV}
GEOPMAKER_SERVICE=geoparquetmaker-${ENV}
GEOPMAKER_SERVICE_FRONT=geoparquetmaker-front-${ENV}

echo """
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '--build-arg', 'BASE_IMAGE=$BASE_IMAGE', '-t', '$GEOPMAKER_IMAGE', '.']
  dir: '.'
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '$GEOPMAKER_IMAGE']
- name: 'gcr.io/cloud-builders/gcloud'
  args: ['run', 'deploy', 
    '$GEOPMAKER_SERVICE', 
    '--image', '$GEOPMAKER_IMAGE', 
    '--allow-unauthenticated', 
    '--region', 'us-west1', 
    '--service-account', 'geoparquet-maker@global-mangroves.iam.gserviceaccount.com',
    '--cpu', '4',
    '--memory', '16G',
    '--timeout', '3600'
    ]
- name: 'gcr.io/cloud-builders/gcloud'
  args: ['run', 'deploy', 
    '${GEOPMAKER_SERVICE_FRONT}', 
    '--image', '$GEOPMAKER_IMAGE', 
    '--set-env-vars', 'FORWARD_SERVICE=$(gcloud run services describe $GEOPMAKER_SERVICE --platform managed --region us-west1 --format 'value(status.url)')',
    '--set-env-vars', 'FORWARD_PATH=/build_GEOP/',
    '--allow-unauthenticated', 
    '--region', 'us-west1', 
    '--service-account', 'geoparquet-maker@global-mangroves.iam.gserviceaccount.com'
    ]
images:
# - $BASE_IMAGE
- $GEOPMAKER_IMAGE
""" > /tmp/cloudbuild.yaml

gcloud builds submit \
    --config /tmp/cloudbuild.yaml

bash ./eventarc.sh $ENV $GEOPMAKER_SERVICE_FRONT

# Test
# TODO, implement a proper test that fails
