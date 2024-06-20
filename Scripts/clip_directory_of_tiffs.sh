CRS=EPSG:32619
INDIR=/GeospatialServicesData/NBS_ADAPTS/DOM_01/flooding
OUTDIR=/users/chlowrie/TestData/TEST_NBS_ADAPTS

rm -r $OUTDIR/*

for i in `ls $INDIR/WaterDepth*`
do
    echo $i
    IFS='/' read -ra ADDR <<< "$i"
    layer_name=$(echo ${ADDR[5]} | sed 's/"//')
    echo $layer_name
    gdalwarp -te 354233 2178007 357500 2183212 $i $OUTDIR/$layer_name
done

zip $OUTDIR/TEST.zip $OUTDIR/*.tif -j
