
INDIR=/Users/chlowrie/Desktop/TestData/NBS_Adapts/Dom02/

for l in `ls $INDIR*.tiff`
do
    echo $l
    echo $INDIR$l
    IFS='/' read -ra ADDR <<< "$l"
    last_index=$(( ${#ADDR[@]} - 1 ))
    echo ${ADDR[$last_index]}
    n=NBS_ADAPTS/Dom02/${ADDR[$last_index]}

    curl \
        -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
        -X POST https://cogmaker-staging-myzvqet7ua-uw.a.run.app/build_COG/ \
        -F "name=$n" \
        -F "data=@${l}" &
    sleep 2
done

#     # -F "data=@/Users/chlowrie/Desktop/TestData/hmax_medium_large.tiff"

# curl \
#     -H "Authorization: Bearer $(gcloud auth application-default print-access-token) \
#     http://localhost:3004/get_managed_assets/