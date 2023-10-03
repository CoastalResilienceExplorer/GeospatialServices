ENV=${1:?"Must set environment as first arg"}
echo $ENV
BASE_GAR_DIRECTORY=us-west1-docker.pkg.dev/global-mangroves
BASE_IMAGE=${BASE_GAR_DIRECTORY}/base/python_gis_base_${ENV}

echo """
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', '$BASE_IMAGE', '.']
  dir: '.'
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', '$BASE_IMAGE']
""" > /tmp/cloudbuild.yaml

gcloud builds submit \
    --config /tmp/cloudbuild.yaml