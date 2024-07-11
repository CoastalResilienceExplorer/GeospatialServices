import requests

TEST_FLOOD = "/Users/chlowrie/Desktop/TestData/damages_test/WaterDepth_Historic_S4_Tr25_t33.tiff"
URL = "http://localhost:3000/damage/nsi/generic/"


files = {"data": open(TEST_FLOOD, "rb")}
data = {
    "ISO3": "JAM"
}
res = requests.post(URL, data=data, files=files)

with open('./test.gpkg', 'wb') as f:
    f.write(res.content)
