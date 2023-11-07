## Purpose
To auto-generate GeoTiffs from Mesh XYZ files.

This assumes `python-gis-base` has been built, using the `BasePythonImage` directory.

### To Build Mesh2Tiff Image
```
TAG=dev
BASE=python-gis-base
IMAGE=mesh2tiff-${TAG}
docker build -t $IMAGE --build-arg BASE_IMAGE=${BASE} -f script.Dockerfile .
```

### To run Mesh2Tiff
```
docker run \
    -v $HOME/Desktop/TestData:/data \
    $IMAGE \
    /data/hmax_land2.csv \
    --id hmax_land2
```
