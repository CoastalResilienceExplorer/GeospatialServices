ENV=${1:?"Must set environment as first arg"}
echo $ENV
BASE_GAR_DIRECTORY=us-west1-docker.pkg.dev/global-mangroves
BASE_IMAGE=${BASE_GAR_DIRECTORY}/base/python_gis_base_${ENV}
IMAGE=${BASE_GAR_DIRECTORY}/cogmaker/cogmaker_${ENV}
SERVICE=cogmaker-${ENV}
SERVICE_FRONT=cogmaker-front-${ENV}
INPUT_BUCKET=cogmaker-input-${ENV}
OUTPUT_BUCKET=cogmaker-output-${ENV}

gsutil mb -l us-west1 gs://$INPUT_BUCKET
gsutil mb -l us-west1 gs://$OUTPUT_BUCKET

echo """
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '--build-arg', 'BASE_IMAGE=$BASE_IMAGE', '-t', '$IMAGE', '.']
  dir: '.'
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '$IMAGE']
- name: 'gcr.io/cloud-builders/gcloud'
  args: ['run', 'deploy', 
    '$SERVICE', 
    '--image', '$IMAGE', 
    '--allow-unauthenticated', 
    '--region', 'us-west1', 
    '--service-account', 'cog-maker@global-mangroves.iam.gserviceaccount.com',
    '--set-env-vars', 'OUTPUT_BUCKET=${OUTPUT_BUCKET}',
    '--cpu', '4',
    '--memory', '16G',
    '--timeout', '3600'
    ]
images:
- $IMAGE
""" > /tmp/cloudbuild.yaml

gcloud builds submit \
    --config /tmp/cloudbuild.yaml

echo """
steps:
- name: 'gcr.io/cloud-builders/gcloud'
  args: ['run', 'deploy', 
    '${SERVICE_FRONT}', 
    '--image', '$IMAGE', 
    '--set-env-vars', 'FORWARD_SERVICE=$(gcloud run services describe $SERVICE --platform managed --region us-west1 --format 'value(status.url)')',
    '--set-env-vars', 'FORWARD_PATH=/build_COG/managed/',
    '--allow-unauthenticated', 
    '--region', 'us-west1', 
    '--service-account', 'cog-maker@global-mangroves.iam.gserviceaccount.com'
    ]
""" > /tmp/cloudbuild.yaml

gcloud builds submit \
    --config /tmp/cloudbuild.yaml

bash ./eventarc.sh $ENV $SERVICE_FRONT $INPUT_BUCKET

# Test
gsutil -m cp ./test/small.tif gs://test-tiff-to-cog/test/small.tif
