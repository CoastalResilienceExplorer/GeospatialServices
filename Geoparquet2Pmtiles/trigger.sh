curl -X POST https://geoparquet2mbtiles-staging-myzvqet7ua-uw.a.run.app/create_mbtiles/ \
   -H "Content-Type: application/json" \
   -d '{ "bucket": "geopmaker-output-staging", "name": "vectors/CWON_combined_teselas_hexs.parquet" }'