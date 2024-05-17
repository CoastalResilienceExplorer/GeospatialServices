
INDIR=$1
OUTPUT_DIR=$2

for l in `ls $INDIR*.tiff`
do
    echo $l
    IFS='/' read -ra ADDR <<< "$l"
    last_index=$(( ${#ADDR[@]} - 1 ))
    echo ${ADDR[$last_index]}
    n=$OUTPUT_DIR/${ADDR[$last_index]}

    curl \
        -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
        -X POST https://cogmaker-staging-myzvqet7ua-uw.a.run.app/build_COG/ \
        -F "name=$n" \
        -F "data=@${l}" &
    sleep 10
done
