
# HOST=https://cog2pt-staging-myzvqet7ua-uw.a.run.app/zarr2pt/
# HOST=http://localhost:3000/zarr2pt/
HOST=http://molokai.pbsci.ucsc.edu:3000/zarr2pt/
INPUT=$1
OUTPUT=$2
CRS_WKT=$3

curl \
    -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
    -H "Content-Type: application/json" \
    -X POST $HOST \
    -d '{ "data": "'$INPUT'", "output": "'$OUTPUT'", "crs": "'$CRS_WKT'" }'