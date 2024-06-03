# HOST=http://localhost:3004
# HOST=https://cogmaker-staging-myzvqet7ua-uw.a.run.app
HOST=http://molokai.pbsci.ucsc.edu:3000
INPUT=$1
OUTPUT=$2

curl \
    -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
    -X POST $HOST/build_zarr/ \
    -F "gcs_directory=$INPUT" \
    -F "parser={\"1\": \"Climate\", \"2\": \"Scenario\", \"3\": \"Return Period\"}" \
    -F "output=$OUTPUT"