# curl -X POST https://geoparquet2mbtiles-staging-myzvqet7ua-uw.a.run.app/create_mbtiles/ \
#    -H "Content-Type: application/json" \
#    -d '{ "bucket": "geopmaker-output-staging", "name": "vectors/cwon-teselas/RESULTS_TESELA_1996_reppts.parquet" }' &
# sleep 5

curl -X POST https://geoparquet2mbtiles-staging-myzvqet7ua-uw.a.run.app/create_mbtiles/ \
   -H "Content-Type: application/json" \
   -d '{ "bucket": "geopmaker-output-staging", "name": "vectors/cwon-teselas/RESULTS_TESELA_1996.parquet" }' &
sleep 5

curl -X POST https://geoparquet2mbtiles-staging-myzvqet7ua-uw.a.run.app/create_mbtiles/ \
   -H "Content-Type: application/json" \
   -d '{ "bucket": "geopmaker-output-staging", "name": "vectors/cwon-teselas/RESULTS_TESELA_2010_reppts.parquet" }' &
sleep 5

curl -X POST https://geoparquet2mbtiles-staging-myzvqet7ua-uw.a.run.app/create_mbtiles/ \
   -H "Content-Type: application/json" \
   -d '{ "bucket": "geopmaker-output-staging", "name": "vectors/cwon-teselas/RESULTS_TESELA_2010.parquet" }' &
sleep 5

curl -X POST https://geoparquet2mbtiles-staging-myzvqet7ua-uw.a.run.app/create_mbtiles/ \
   -H "Content-Type: application/json" \
   -d '{ "bucket": "geopmaker-output-staging", "name": "vectors/cwon-teselas/RESULTS_TESELA_2015_reppts.parquet" }' &
sleep 5

curl -X POST https://geoparquet2mbtiles-staging-myzvqet7ua-uw.a.run.app/create_mbtiles/ \
   -H "Content-Type: application/json" \
   -d '{ "bucket": "geopmaker-output-staging", "name": "vectors/cwon-teselas/RESULTS_TESELA_2015.parquet" }' &
