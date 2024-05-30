
INDIR=gs://cogmaker-output-staging/NBS_ADAPTS/JAM/damages/
HOST=https://cog2pt-staging-myzvqet7ua-uw.a.run.app/cog2pt/
# HOST=http://localhost:3000/cog2pt/



for l in `gsutil ls $INDIR`
do
    echo $l
    # Extract substring from the starting index to the end of the string
    substring="${l:5}"

    echo "$substring"
    output="${l/cogmaker-output-staging/geopmaker-output-staging}"
    output="${output/tiff/parquet}"
    output="${output:5}"
    echo $output
    curl \
        -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
        -H "Content-Type: application/json" \
        -X POST $HOST \
        -d '{ "raster": "'$substring'", "output": "'$output'" }' &
    sleep 5

done
