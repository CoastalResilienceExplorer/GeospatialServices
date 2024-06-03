HOST=http://molokai.pbsci.ucsc.edu:3000
INDIR=$1
OUTPUT_DIR=$2

for l in `ls $INDIR*.tif`
do
    # echo $l
    IFS='/' read -ra ADDR <<< "$l"
    last_index=$(( ${#ADDR[@]} - 1 ))
    # echo ${ADDR[$last_index]}
    n=$OUTPUT_DIR/${ADDR[$last_index]}

    curl \
        -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
        -X POST $HOST/build_COG/ \
        -F "name=$n" \
        -F "data=@${l}" &
    sleep 1
done
