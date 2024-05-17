# Inputs
GDB=/Users/chlowrie/Desktop/TestData/NBS_Adapts/BLZ/BLZ_Flood_Raster_00cm.gdb
DIR=/Users/chlowrie/Desktop/TestData/CoPe/BLZ/
KEY=BLZ
PROJECT=CoPe

# GDB to COG
# bash Scripts/gdb_data_to_tiff.sh $GDB $DIR

# Upload COGs
FLOODING_OUTPUT=$PROJECT/$KEY
# bash CogMaker/tools/trigger_cog_on_submit.sh $DIR $FLOODING_OUTPUT
# exit 1

CRS_WKT=EPSG:$(gdalinfo -json $(ls $DIR*.tiff | head -1 ) | jq '.stac.["proj:epsg"]')
echo $CRS_WKT

# # Damages
DAMAGES_OUTPUT=$KEY/damages
bash DamageAssessment/tools/bulk_trigger_damages.sh $DIR $PROJECT $DAMAGES_OUTPUT
exit 1
sleep 300

# Build Damages Zarr
INPUT_DIR=cogmaker-output-staging/$PROJECT/$DAMAGES_OUTPUT
# bash CogMaker/tools/trigger_build_zarr.sh $INPUT_DIR damages.zarr

# Build Flooding Zarr
# bash CogMaker/tools/trigger_build_zarr.sh cogmaker-output-staging/$PROJECT/$KEY flooding.zarr

# AEV
DAMAGES_ZARR=gs://cogmaker-output-staging/$PROJECT/$DAMAGES_OUTPUT/damages.zarr
FLOODING_ZARR=gs://cogmaker-output-staging/$PROJECT/$KEY/flooding.zarr
# echo $DAMAGES_ZARR
# bash DamageAssessment/tools/bulk_trigger_damages_aev.sh $DAMAGES_ZARR

# To Parquet
DAMAGES_PARQUET=geopmaker-output-staging/$PROJECT/$DAMAGES_OUTPUT/damages.parquet
# bash Cog2Point/tools/trigger_zarr.sh $DAMAGES_ZARR $DAMAGES_PARQUET $CRS_WKT

# To Parquet
FLOODING_PARQUET=geopmaker-output-staging/$PROJECT/$KEY/flooding.parquet
bash Cog2Point/tools/trigger_zarr.sh $FLOODING_ZARR $FLOODING_PARQUET $CRS_WKT

sleep 60

# To PMTiles
# bash Geoparquet2Pmtiles/tools/trigger.sh $PROJECT/$DAMAGES_OUTPUT/damages.parquet
bash Geoparquet2Pmtiles/tools/trigger.sh $PROJECT/$KEY/flooding.parquet
