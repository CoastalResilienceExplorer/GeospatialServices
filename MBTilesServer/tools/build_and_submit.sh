ENV=${1:?"Must set environment as first arg"}
echo $ENV
BASE_GAR_DIRECTORY=us-west1-docker.pkg.dev/global-mangroves
IMAGE=${BASE_GAR_DIRECTORY}/mbtileserver/mbtileserver-${ENV}
SERVICE=mbtileserver-${ENV}
BUCKET=geoparquet2mbtiles-output-${ENV}

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
    '--set-env-vars', 'BUCKET=${BUCKET}',
    '--execution-environment', 'gen2',
    '--cpu', '4',
    '--memory', '16G',
    '--timeout', '3600'
    ]
""" > /tmp/cloudbuild.yaml

gcloud builds submit \
    --config /tmp/cloudbuild.yaml

# Test
# TODO, implement a proper test that fails
