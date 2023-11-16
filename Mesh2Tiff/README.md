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
It's important for the final line to stay as one line
```
MSYS_NO_PATHCONV=1 docker run \
    -v $PWD:/app \
    -v $HOME/Desktop/TestData/test_mesh2tiff:/data \
    --entrypoint bash \
    $BASE_IMAGE \
    iterate_directory.sh --resolution 1 --crs EPSG:32620 --clip-radius 10
```

### To run Mesh2Tiff for an individual file
```
MSYS_NO_PATHCONV=1 docker run \
    -v $PWD:/app \
    -v $HOME/Desktop/TestData/test_mesh2tiff:/data \
    --entrypoint python3 \
    $IMAGE \
    mesh2tiff.py /data/hmax_rp_500_rest_150.csv \
    --resolution 1 \
    --crs EPSG:32620 \
    --clip-radius 10
```