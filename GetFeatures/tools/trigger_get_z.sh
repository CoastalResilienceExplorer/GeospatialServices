curl -X POST http://localhost:3002/get_features_with_z_values/ \
    -F "z=@/Users/chlowrie/Desktop/TestData/hmax_medium_large.tiff" \
    -F "features_from=OSM" \
    -F "way_type=building" > ~/Desktop/TestData/OSM_USVI_building_depths.gpkg