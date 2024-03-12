BOTTOM="37.5863"
LEFT="-122.39337"
TOP="37.61098"
RIGHT="-122.35065"
ISO3="USA"

curl --location 'http://localhost:3003/get_open_buildings/' \
--header 'Content-Type: application/json' \
--data '{
    "left": '$LEFT',
    "right": '$RIGHT',
    "top": '$TOP',
    "bottom": '$BOTTOM',
    "ISO3": "'$ISO3'"
}' > ~/Desktop/TestData/OpenBuildings_Burlingame.gpkg
