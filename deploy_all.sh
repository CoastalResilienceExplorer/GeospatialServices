ENV=${1:?"Must set environment as first arg"}
echo $ENV

echo """
steps:
- name: 'gcr.io/cloud-builders/gcloud'
  id: base
  entrypoint: 'bash'
  args: ['tools/build_and_submit.sh', '$ENV']
  dir: 'BasePythonImage'
- name: 'gcr.io/cloud-builders/gcloud'
  entrypoint: 'bash'
  args: ['tools/build_and_submit.sh', '$ENV']
  dir: 'CogMaker'
  waitFor: 
  - base
- name: 'gcr.io/cloud-builders/gcloud'
  entrypoint: 'bash'
  args: ['tools/build_and_submit.sh', '$ENV']
  dir: 'CogServer'
- name: 'gcr.io/cloud-builders/gcloud'
  entrypoint: 'bash'
  args: ['tools/build_and_submit.sh', '$ENV']
  dir: 'GeoParquetMaker'
  waitFor: 
  - base
- name: 'gcr.io/cloud-builders/gcloud'
  entrypoint: 'bash'
  args: ['tools/build_and_submit.sh', '$ENV']
  dir: 'Mesh2Tiff'
  waitFor: 
  - base
""" > /tmp/cloudbuild.yaml

gcloud builds submit \
    --config /tmp/cloudbuild.yaml
