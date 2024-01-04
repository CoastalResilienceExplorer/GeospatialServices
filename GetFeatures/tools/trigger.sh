curl -X POST http://localhost:3002/san_mateo/ \
   -H "Content-Type: application/json" \
   -d '{"features_file": "supporting-data2/google-microsoft-open-buildings.parquet/country_iso=USA/", "rasters": ["cloud-native-geospatial/san-mateo-2/0e1.tif", "cloud-native-geospatial/san-mateo-2/0e20.tif", "cloud-native-geospatial/san-mateo-2/0e100.tif"], "rps": [1, 20, 100], "mode": "SAN_MATEO" }' > /Users/chlowrie/Desktop/OPC/outputs/0e.zip

echo "0e"
curl -X POST http://localhost:3002/san_mateo/ \
   -H "Content-Type: application/json" \
   -d '{"features_file": "supporting-data2/google-microsoft-open-buildings.parquet/country_iso=USA/", "rasters": ["cloud-native-geospatial/san-mateo-2/0r1.tif", "cloud-native-geospatial/san-mateo-2/0r20.tif", "cloud-native-geospatial/san-mateo-2/0r100.tif"], "rps": [1, 20, 100], "mode": "SAN_MATEO" }' > /Users/chlowrie/Desktop/OPC/outputs/0r.zip

echo "0r"
curl -X POST http://localhost:3002/san_mateo/ \
   -H "Content-Type: application/json" \
   -d '{"features_file": "supporting-data2/google-microsoft-open-buildings.parquet/country_iso=USA/", "rasters": ["cloud-native-geospatial/san-mateo-2/05e1.tif", "cloud-native-geospatial/san-mateo-2/05e20.tif", "cloud-native-geospatial/san-mateo-2/05e100.tif"], "rps": [1, 20, 100], "mode": "SAN_MATEO" }' > /Users/chlowrie/Desktop/OPC/outputs/05e.zip

echo "05e"
curl -X POST http://localhost:3002/san_mateo/ \
   -H "Content-Type: application/json" \
   -d '{"features_file": "supporting-data2/google-microsoft-open-buildings.parquet/country_iso=USA/", "rasters": ["cloud-native-geospatial/san-mateo-2/05r1.tif", "cloud-native-geospatial/san-mateo-2/05r20.tif", "cloud-native-geospatial/san-mateo-2/05r100.tif"], "rps": [1, 20, 100], "mode": "SAN_MATEO" }' > /Users/chlowrie/Desktop/OPC/outputs/05r.zip

echo "05r"
curl -X POST http://localhost:3002/san_mateo/ \
   -H "Content-Type: application/json" \
   -d '{"features_file": "supporting-data2/google-microsoft-open-buildings.parquet/country_iso=USA/", "rasters": ["cloud-native-geospatial/san-mateo-2/1e1.tif", "cloud-native-geospatial/san-mateo-2/1e20.tif", "cloud-native-geospatial/san-mateo-2/1e100.tif"], "rps": [1, 20, 100], "mode": "SAN_MATEO" }' > /Users/chlowrie/Desktop/OPC/outputs/1e.zip

echo "1e"
curl -X POST http://localhost:3002/san_mateo/ \
   -H "Content-Type: application/json" \
   -d '{"features_file": "supporting-data2/google-microsoft-open-buildings.parquet/country_iso=USA/", "rasters": ["cloud-native-geospatial/san-mateo-2/1r1.tif", "cloud-native-geospatial/san-mateo-2/1r20.tif", "cloud-native-geospatial/san-mateo-2/1r100.tif"], "rps": [1, 20, 100], "mode": "SAN_MATEO" }' > /Users/chlowrie/Desktop/OPC/outputs/1r.zip

echo "1r"