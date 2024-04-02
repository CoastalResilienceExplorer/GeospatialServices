FLOODING=${1:?"Must set path to flooding tiff"}
REMOTE_OUTPUT=${2:?"Must set remote path to flooding tiff.  This will be the directory in gs://cloud-native-geospatial"}
LOCAL_OUTPUT=${3:?"Must set path to return GZIP TIFF."}

# curl -X POST 'http://localhost:3001/damage/dlr_guf/' \
curl -X POST 'https://damages-staging-myzvqet7ua-uw.a.run.app/damage/dlr_guf/' \
    -F "flooding=@$FLOODING" \
    -F "output=$REMOTE_OUTPUT" > $LOCAL_OUTPUT
