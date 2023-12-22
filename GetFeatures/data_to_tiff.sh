# This script is run with GDAL 3.7.1
# It converts layers in a FileGDB into efficiently compressed GeoTiffs
IN_DIR=/Users/chlowrie/Downloads/floodmaps/
OUTPUT_DIR=/Users/chlowrie/Desktop/OPC/floodmaps/

for layer in `ls $IN_DIR`
do
    echo $layer
    gdal_translate \
        -ot Int16 \
        -of COG \
        -scale 0 8 0 32767 \
        ${IN_DIR}${layer} ${OUTPUT_DIR}${layer} \
        -co NUM_THREADS=ALL_CPUS
    gdal_edit.py ${OUTPUT_DIR}${layer} -scale $(bc -l <<< "8/32767.0")
done

