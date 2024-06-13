CRS=EPSG:32618
INDIR=/GeospatialServicesData/NBS_ADAPTS/JAM/flooding
OUTDIR=/users/chlowrie/TestData/TEST_NBS_ADAPTS

rm -r $OUTDIR/*

for i in `ls $INDIR/WaterDepth*`
do
    echo $i
    IFS='/' read -ra ADDR <<< "$i"
    layer_name=$(echo ${ADDR[5]} | sed 's/"//')
    echo $layer_name
    gdalwarp -te 404265 2039983 410892 2044857 $i $OUTDIR/$layer_name
done

zip $OUTDIR/TEST.zip $OUTDIR/*.tif -j
