# openapi2-functions.yaml
ENV=${1:?"Must set environment as first arg"}
echo $ENV

COGSERVER=cogserver-${ENV}

ID=geospatialservices-api-${ENV}
GATEWAY=${ID}-gateway

echo """
swagger: '2.0'
info:
  title: ${ID}
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
  /{z}/{x}/{y}:
    get:
      summary: Get an XYZ Tile
      operationId: get_tile
      responses:
        '200':
          description: A successful response
          schema:
            type: string
      x-google-backend:
        address: '$(gcloud run services describe $COGSERVER --platform managed --region us-west1 --format 'value(status.url)')/{z}/{x}/{y}.png'
      security:
        - api_key: []
      parameters:
        - in: path
          name: x   # Note the name is the same as in the path
          required: true
          type: integer
          minimum: 1
          description: X
        - in: path
          name: y   # Note the name is the same as in the path
          required: true
          type: integer
          minimum: 1
          description: Y
        - in: path
          name: z   # Note the name is the same as in the path
          required: true
          type: integer
          minimum: 1
          description: Z
""" > /tmp/apibuild.yaml


gcloud api-gateway apis create ${ID}

CONFIG_ID=config-$RANDOM
gcloud api-gateway api-configs create $CONFIG_ID \
    --api=${ID} --openapi-spec=/tmp/apibuild.yaml \
    --backend-auth-service-account=cog-maker@global-mangroves.iam.gserviceaccount.com

gcloud api-gateway gateways create $GATEWAY \
  --api=${ID} --api-config=$CONFIG_ID \
  --location=us-west2

gcloud api-gateway gateways update $GATEWAY \
  --api=${ID} --api-config=$CONFIG_ID \
  --location=us-west2