
INDIR=gs://geopmaker-output-staging/NBS_ADAPTS/Dom02/
HOST=https://geoparquet2pmtiles-staging-myzvqet7ua-uw.a.run.app/create_pmtiles/
HOST=http://localhost:3000/create_pmtiles/



for l in `gsutil ls $INDIR*.parquet`
do
    echo $l
    # Extract substring from the starting index to the end of the string
    bucket=geopmaker-output-staging
    name=${l/gs:\/\/geopmaker-output-staging\//}
    # echo $name
    name=${name/:/}
    echo $name
    # name=NBS_ADAPTS/Dom02/WaterDepth_Future2050_S1_Tr100_t33.parquet/184356._1976192_30000.parquet

    # # echo "$substring"
    # # output="${l/cogmaker-output-staging/geopmaker-output-staging}"
    # # output="${output/tiff/parquet}"
    # # output="${output:5}"
    # # echo $output
    curl \
        -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
        -H "Content-Type: application/json" \
        -X POST $HOST \
        -d '{ "bucket": "'$bucket'", "name": "'$name'", "use_id": "fid" }' 
    break

done
