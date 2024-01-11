LEFT="-64.73821713046833"
BOTTOM="17.7186018228738"
RIGHT="-64.68036724643513"
TOP="17.796174416088725"
ISO3="USA"

curl --location 'http://localhost:3002/get_open_buildings/' \
--header 'Content-Type: application/json' \
--data '{
    "left": '$LEFT',
    "right": '$RIGHT',
    "top": '$TOP',
    "bottom": '$BOTTOM',
    "ISO3": "'$ISO3'"
}' > ~/Desktop/TestData/OpenBuildings_USVI.gpkg
