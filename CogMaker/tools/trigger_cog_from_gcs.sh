curl -X POST http://localhost:3004/build_COG/managed/ \
   -H "Content-Type: application/json" \
   -d '{ "bucket": "cloud-native-geospatial", "name": "test/small.tif" }'