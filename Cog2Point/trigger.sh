curl -X POST $URL/to_extent/ \
   -H "Content-Type: application/json" \
   -d '{"output": "cloud-native-geospatial/cwon_data_chunked/with_1996_TC_Tr_050.parquet", "raster": "cloud-native-geospatial/cwon_data/with_1996_TC_Tr_050.tiff"}' &
sleep 5

curl -X POST $URL/to_extent/ \
   -H "Content-Type: application/json" \
   -d '{"output": "cloud-native-geospatial/cwon_data_chunked/with_2015_TC_Tr_050.parquet", "raster": "cloud-native-geospatial/cwon_data/with_2015_TC_Tr_050.tiff"}' &
sleep 5