ENV=${1:?"Must set environment as first arg"}
echo $ENV
BASE_GAR_DIRECTORY=us-west1-docker.pkg.dev/global-mangroves
BASE_IMAGE=${BASE_GAR_DIRECTORY}/base/python_gis_base_${ENV}
GEOPMAKER_IMAGE=${BASE_GAR_DIRECTORY}/geoparquetmaker/geoparquetmaker${ENV}
GEOPMAKER_SERVICE=geoparquetmaker-${ENV}
GEOPMAKER_SERVICE_FRONT=geoparquetmaker-front-${ENV}
INPUT_BUCKET=geopmaker-input-${ENV}
OUTPUT_BUCKET=geopmaker-output-${ENV}

gsutil mb -l us-west1 gs://$INPUT_BUCKET
gsutil mb -l us-west1 gs://$OUTPUT_BUCKET

echo """
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '--build-arg', 'BASE_IMAGE=$BASE_IMAGE', '-t', '$GEOPMAKER_IMAGE', '.']
  dir: '.'
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '$GEOPMAKER_IMAGE']
- name: 'gcr.io/cloud-builders/gcloud'
  id: 'geopmaker'
  args: ['run', 'deploy', 
    '$GEOPMAKER_SERVICE', 
    '--image', '$GEOPMAKER_IMAGE', 
    '--allow-unauthenticated', 
    '--region', 'us-west1', 
    '--service-account', 'cog-maker@global-mangroves.iam.gserviceaccount.com',
    '--set-env-vars', 'OUTPUT_BUCKET=${OUTPUT_BUCKET}',
    '--cpu', '4',
    '--memory', '16G',
    '--timeout', '3600'
    ]
- name: 'gcr.io/cloud-builders/gcloud'
  args: ['run', 'deploy', 
    '${GEOPMAKER_SERVICE_FRONT}', 
    '--image', '$GEOPMAKER_IMAGE', 
    '--set-env-vars', 'FORWARD_SERVICE=$(gcloud run services describe $GEOPMAKER_SERVICE --platform managed --region us-west1 --format 'value(status.url)')',
    '--set-env-vars', 'FORWARD_PATH=/build_geoparquet/',
    '--allow-unauthenticated', 
    '--region', 'us-west1', 
    '--service-account', 'cog-maker@global-mangroves.iam.gserviceaccount.com'
    ]
  waitFor: ['geopmaker']
""" > /tmp/cloudbuild.yaml

gcloud builds submit \
    --config /tmp/cloudbuild.yaml

bash ./eventarc.sh $ENV $GEOPMAKER_SERVICE_FRONT $INPUT_BUCKET

# Test
# TODO, implement a proper test that fails
