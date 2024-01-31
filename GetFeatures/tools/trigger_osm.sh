HOST="https://getfeatures-staging-myzvqet7ua-uw.a.run.app"

LEFT="-64.73821713046833"
BOTTOM="17.7186018228738"
RIGHT="-64.68036724643513"
TOP="17.796174416088725"

curl --location $HOST'/get_osm/' \
--header 'Content-Type: application/json' \
--data '{
    "left": '$LEFT',
    "right": '$RIGHT',
    "top": '$TOP',
    "bottom": '$BOTTOM',
    "way_type": "building"
}' > ~/Desktop/TestData/OSM_USVI_building.gpkg

curl --location $HOST'/get_osm/' \
--header 'Content-Type: application/json' \
--data '{
    "left": '$LEFT',
    "right": '$RIGHT',
    "top": '$TOP',
    "bottom": '$BOTTOM',
    "way_type": "highway"
}' > ~/Desktop/TestData/OSM_USVI_highway.gpkg