# Inputs
GDB=/Users/chlowrie/Desktop/TestData/NBS_Adapts/JAM/JAM_Flood_Raster_00cm_00cm.gdb
DIR=/Users/chlowrie/Desktop/TestData/NBS_Adapts/JAM/
KEY=JAM
PROJECT=NBS_ADAPTS

gsutil -m rm -r gs://cogmaker-output-staging/$PROJECT/$KEY/
gsutil -m rm -r gs://geopmaker-output-staging/$PROJECT/$KEY/

FLOODING_OUTPUT=$PROJECT/$KEY
DAMAGES_OUTPUT=$KEY/damages

DAMAGES_INPUT_DIR=cogmaker-output-staging/$PROJECT/$DAMAGES_OUTPUT

DAMAGES_ZARR=gs://cogmaker-output-staging/$PROJECT/$DAMAGES_OUTPUT/damages.zarr
FLOODING_ZARR=gs://cogmaker-output-staging/$PROJECT/$KEY/flooding.zarr

FLOODING_PARQUET=geopmaker-output-staging/$PROJECT/$KEY/flooding.parquet
DAMAGES_PARQUET=geopmaker-output-staging/$PROJECT/$DAMAGES_OUTPUT/damages.parquet

GDB to COG
bash Scripts/gdb_data_to_tiff.sh $GDB $DIR

Upload COGs
bash CogMaker/tools/trigger_cog_on_submit.sh $DIR $FLOODING_OUTPUT
sleep 20

CRS_WKT=EPSG:$(gdalinfo -json $(ls $DIR*.tif | head -1 ) | jq '.stac.["proj:epsg"]')
echo $CRS_WKT

# # Damages
bash DamageAssessment/tools/bulk_trigger_damages.sh $DIR $PROJECT $DAMAGES_OUTPUT
sleep 120


# Build Damages Zarr

bash CogMaker/tools/trigger_build_zarr.sh $DAMAGES_INPUT_DIR damages.zarr

# Build Flooding Zarr
bash CogMaker/tools/trigger_build_zarr.sh cogmaker-output-staging/$PROJECT/$KEY flooding.zarr

# AEV
bash DamageAssessment/tools/bulk_trigger_damages_aev.sh $DAMAGES_ZARR

# To Parquet
bash Cog2Point/tools/trigger_zarr.sh $DAMAGES_ZARR $DAMAGES_PARQUET $CRS_WKT

# To Parquet
bash Cog2Point/tools/trigger_zarr.sh $FLOODING_ZARR $FLOODING_PARQUET $CRS_WKT

# To PMTiles
bash Geoparquet2Pmtiles/tools/trigger.sh $PROJECT/$DAMAGES_OUTPUT/damages.parquet
bash Geoparquet2Pmtiles/tools/trigger.sh $PROJECT/$KEY/flooding.parquet
