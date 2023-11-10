## Purpose
To auto-generate GeoTiffs from Mesh XYZ files.

This assumes `python-gis-base` has been built, using the `BasePythonImage` directory.
```
BASE_DIR=../
BASE_IMAGE=python-gis-base
cd $BASE_DIR/BasePythonImage
docker build -t $BASE_IMAGE .
cd $BASE_DIR/Mesh2Tiff
```

### To run Mesh2Tiff in bulk
```
DATA_DIR=$HOME/Desktop/TestData/test_mesh2tiff
docker run \
    -v $PWD:/app \
    -v $DATA_DIR:/data \
    --entrypoint bash \
    $BASE_IMAGE \
    iterate_directory.sh --resolution 1 --crs EPSG:32620 #it's important for these to stay on a single line
```

### To run Mesh2Tiff for an individual file
```
DATA_DIR=$HOME/Desktop/TestData/test_mesh2tiff
docker run \
    -v $PWD:/app \
    -v $DATA_DIR:/data \
    --entrypoint python3 \
    $BASE_IMAGE \
    mesh2tiff.py \
    /data/hmax_land2.csv \
    --resolution 1 \
    --crs EPSG:32620
```