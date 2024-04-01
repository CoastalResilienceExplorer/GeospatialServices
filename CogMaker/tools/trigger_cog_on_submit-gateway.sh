
curl \
    -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
    -X POST https://express-gateway-staging-myzvqet7ua-uw.a.run.app/build_COG/ \
    -F "name=hmax_medium_large.tiff" \
    -F "data=@/Users/chlowrie/Desktop/UCSC/GeospatialServices/CogMaker/test/small.tif"
    # -F "data=@/Users/chlowrie/Desktop/TestData/hmax_medium_large.tiff"

# curl \
#     -H "Authorization: Bearer $(gcloud auth application-default print-access-token) \
#     http://localhost:3004/get_managed_assets/