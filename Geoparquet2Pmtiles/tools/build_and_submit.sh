ENV=${1:?"Must set environment as first arg"}
echo $ENV
BASE_GAR_DIRECTORY=us-west1-docker.pkg.dev/global-mangroves
IMAGE=${BASE_GAR_DIRECTORY}/geoparquetmaker/geoparquet2pmtiles-${ENV}
SERVICE=geoparquet2pmtiles-${ENV}
OUTPUT_BUCKET=geoparquet2pmtiles-output-${ENV}

gsutil mb -l us-west1 gs://$OUTPUT_BUCKET

echo """
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', '$IMAGE', '.']
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
""" > /tmp/cloudbuild.yaml

gcloud builds submit \
    --config /tmp/cloudbuild.yaml

# Test
# TODO, implement a proper test that fails
