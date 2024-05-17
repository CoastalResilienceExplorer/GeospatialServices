
HOST=https://geoparquet2pmtiles-staging-myzvqet7ua-uw.a.run.app/create_pmtiles/
# HOST=http://localhost:3001/create_pmtiles/
INPUT=$1

echo $HOST
curl \
    -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
    -H "Content-Type: application/json" \
    -X POST $HOST \
    -d '{ "bucket": "'geopmaker-output-staging'", "name": "'$INPUT'", "use_id": "fid" }'
