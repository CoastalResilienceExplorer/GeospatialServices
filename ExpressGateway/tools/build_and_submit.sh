ENV=${1:?"Must set environment as first arg"}
echo $ENV
SERVICE_BASE_NAME=express-gateway
BASE_GAR_DIRECTORY=us-west1-docker.pkg.dev/global-mangroves
IMAGE=${BASE_GAR_DIRECTORY}/${SERVICE_BASE_NAME}/${SERVICE_BASE_NAME}_${ENV}
SERVICE=${SERVICE_BASE_NAME}-${ENV}

if [[ $ENV == "main" ]]
then
  N_INSTANCES=0 #Temporary. We may want to change this for faster TTL in the future
else
  N_INSTANCES=0
fi

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
    '--cpu', '1',
    '--memory', '2G',
    '--timeout', '3600',
    '--min-instances', '$N_INSTANCES'
    ]
""" > /tmp/cloudbuild.yaml

gcloud builds submit \
    --config /tmp/cloudbuild.yaml
