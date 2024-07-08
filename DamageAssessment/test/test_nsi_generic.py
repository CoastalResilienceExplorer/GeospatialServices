import requests, os

BASEDIR = "/users/chlowrie/TestData/USGS_USVI/"

URL = "http://localhost:4000/damage/nsi/generic/"

for i in os.listdir(BASEDIR):
    files = {"data": open(os.path.join(BASEDIR, i), "rb")}
    data = {
        "ISO3": "USA"
    }
    res = requests.post(URL, data=data, files=files)
