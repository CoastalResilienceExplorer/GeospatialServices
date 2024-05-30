ENV=${1:?"Must set environment as first arg"}
echo $ENV
BASE_GAR_DIRECTORY=us-west1-docker.pkg.dev/global-mangroves
BASE_IMAGE=${BASE_GAR_DIRECTORY}/base/python_gis_base_${ENV}
IMAGE=${BASE_GAR_DIRECTORY}/mbtileserver/getfeatures-${ENV}
SERVICE=getfeatures-${ENV}

echo """
steps:
# - name: 'gcr.io/cloud-builders/docker'
#   args: ['build', '--build-arg', 'BASE_IMAGE=$BASE_IMAGE', '-t', '$IMAGE', '.']
#   dir: '.'
# - name: 'gcr.io/cloud-builders/docker'
#   args: ['push', '$IMAGE']
- name: 'gcr.io/cloud-builders/gcloud'
  args: ['run', 'deploy', 
    '$SERVICE', 
    '--execution-environment', 'gen2',
    '--image', '$IMAGE', 
    '--allow-unauthenticated', 
    '--region', 'us-west1', 
    '--service-account', 'fs-identity',
    '--update-env-vars', 'MNT_BUCKETS=cloud-native-geospatial;supporting-data2;cogmaker-output-${ENV}',
    '--cpu', '8',
    '--memory', '32G',
    '--timeout', '3600',
    '--concurrency', '2'
    ]
""" > /tmp/cloudbuild.yaml

gcloud builds submit \
    --config /tmp/cloudbuild.yaml