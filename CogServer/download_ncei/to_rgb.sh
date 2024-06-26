IN_GTF=$1
OUT_GTF=$2

# gdal_calc.py --calc "((A+10000)/0.1)/255/255" --type UInt16 -A $IN_GTF --outfile R.tif
# gdal_calc.py --calc "((A+10000)/0.1)/255" --type UInt16 -A $IN_GTF --outfile G.tif
# gdal_calc.py --calc "((A+10000)/0.1)" --type UInt16 -A $IN_GTF --outfile B.tif

# gdal_merge.py -separate -o RGB.tif R.tif G.tif B.tif

gdalwarp -t_srs EPSG:3857 RGB.tif RGB_3857.tif

gdal_translate RGB_3857.tif $OUT_GTF -co TILED=YES -co COPY_SRC_OVERVIEWS=YES -co COMPRESS=DEFLATE
