INDIR=$1
PROJECT=$2
OUTPUT_DIR=$3

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

for l in `ls $INDIR*.tiff`
do
    echo $l
    IFS='/' read -ra ADDR <<< "$l"
    last_index=$(( ${#ADDR[@]} - 1 ))
    echo ${ADDR[$last_index]}
    n=$PROJECT/$OUTPUT_DIR/${ADDR[$last_index]}
    echo $n

    python3 $SCRIPT_DIR/trigger.py -f $l -t damages -p $PROJECT -i $OUTPUT_DIR/${ADDR[$last_index]} &
    sleep 200
done

# python3 tools/trigger.py -f /Users/chlowrie/Desktop/TestData/NBS_Adapts/JAM/WaterDepth_Historic_S3_Tr100_t33.tiff -t damages -p NBS_ADAPTS -i JAM/damages/WaterDepth_Historic_S3_Tr100_t33.tiff --output ./tmp/WaterDepth_Historic_S3_Tr100_t33.tiff
