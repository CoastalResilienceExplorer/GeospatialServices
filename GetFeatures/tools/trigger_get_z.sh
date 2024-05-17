
INDIR=/Users/chlowrie/Desktop/TestData/NBS_Adapts/JAM/

for l in `ls $INDIR*.tiff`
do
    echo $l
    echo $INDIR$l
    IFS='/' read -ra ADDR <<< "$l"
    last_index=$(( ${#ADDR[@]} - 1 ))
    fname=${ADDR[$last_index]}
    fname=${fname/tiff/parquet}
    echo $fname
    
    IFS='.' read -ra ADDR <<< "$fname"
    id=${ADDR[0]}
    echo $id
    n=NBS_ADAPTS/JAM/OSM/$fname
    echo $n

    python3 tools/trigger.py \
        -f $l \
        -t get_z \
        --gcs-output gs://geopmaker-output-staging/$n \
        --rescale --id $id \
        --local 
    sleep 2
done

