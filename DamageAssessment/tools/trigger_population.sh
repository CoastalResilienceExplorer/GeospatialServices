FLOODING=${1:?"Must set path to flooding tiff"}
THRESHOLD=${2:?"Must set minimum threshold in meters"}
REMOTE_OUTPUT=${3:?"Must set remote path to flooding tiff.  This will be the directory in gs://cloud-native-geospatial"}
LOCAL_OUTPUT=${4:?"Must set path to return GZIP TIFF."}


# curl -X POST 'https://damages-staging-myzvqet7ua-uw.a.run.app/damage/dlr_guf/' \
curl -X POST 'http://localhost:3001/population/GHSL_2020_100m/' \
    -F "flooding=@$FLOODING" \
    -F "threshold=$THRESHOLD" \
    -F "output_to_gcs=$REMOTE_OUTPUT" > $LOCAL_OUTPUT
