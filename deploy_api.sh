# openapi2-functions.yaml
ENV=${1:?"Must set environment as first arg"}
echo $ENV

COGMAKER=cogmaker-${ENV}

echo """
swagger: '2.0'
info:
  title: geospatialservices-api
  description: Manage all endpoints related to cloud native geospatial data
  version: 1.0.0
schemes:
  - https
produces:
  - application/json
securityDefinitions:
  api_key:
    type: apiKey
    name: api_key
    in: header
    description: API Key
paths:
  /build_COG:
    post:
      summary: Create a managed Cloud Optimized Geotiff dataset from a submission
      operationId: build_COG
      x-google-backend:
        address: '$(gcloud run services describe $COGMAKER --platform managed --region us-west1 --format 'value(status.url)')/build_COG/'
      responses:
        '200':
          description: A successful response
          schema:
            type: string
      security:
        - api_key: []
      parameters:
        - in: formData
          name: data
          type: string
          description: The file to upload.
        - in: formData
          name: name
          type: string
          description: The name of the file to create.

  /build_COG/managed:
    post:
      summary: Create a managed Cloud Optimized Geotiff dataset from a dataset in GCP
      operationId: build_COG_managed
      x-google-backend:
        address: '$(gcloud run services describe $COGMAKER --platform managed --region us-west1 --format 'value(status.url)')/build_COG/managed/'
      responses:
        '200':
          description: A successful response
          schema:
            type: string
      security:
        - api_key: []
      consumes:
        - application/json
      parameters:
        - in: body
          name: params
          schema: 
            type: object
            properties:
              name:
                type: string
              bucket:
                type: string
""" > /tmp/apibuild.yaml

CONFIG_ID=config-$RANDOM
gcloud api-gateway api-configs create $CONFIG_ID \
    --api=geospatialservices-api --openapi-spec=/tmp/apibuild.yaml \
    --backend-auth-service-account=cog-maker@global-mangroves.iam.gserviceaccount.com

gcloud api-gateway gateways update geospatialservices-gateway \
  --api=geospatialservices-api --api-config=$CONFIG_ID \
  --location=us-west2