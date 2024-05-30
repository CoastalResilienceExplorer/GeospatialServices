INPUT_DIR=/Volumes/cccr-lab/001_projects/006_nsfcope/100_BELIZE/124_SFINCS_SIMULATIONS/008_LIMITED_MANGROVE_ELEVATION_LULC_TREES_015_FREQ_CUT_CORRECT_RP
OUTPUT_DIR=/Users/chlowrie/Desktop/TestData/CoPe/BLZ

mkdir -p $OUTPUT_DIR

for i in `ls $INPUT_DIR`
do
    if [ "$i" = "comparison" ]; then
        break
    fi;
    fname=${i}_hmax_masked.tif
    x=$INPUT_DIR/$i/results/$fname
    cp $x $OUTPUT_DIR/${fname}f
done