## Purpose
To auto-generate GeoTiffs from Mesh XYZ files.

## Setup
All commands are assumed to be run from `Mesh2Tiff` directory.

### Updating the code:
- `git fetch`
- `git stash`
- `git pull`

### If you need to rebuild the base image.

You can generally assume this command does not need to be re-run.  This assumes `python-gis-base` has been built, using the `BasePythonImage` directory.
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
export DATA_PATH=/mnt/c/Users/cgaid/CoastalResilienceLab\ Dropbox/Camila\ Gaido/USVI/csv/rest_v3
BASE_IMAGE=python-gis-base
MSYS_NO_PATHCONV=1 docker run \
    -v $PWD:/app \
    -v $HOME/Desktop/TestData/test_mesh2tiff:/data \
    --entrypoint bash \
    $BASE_IMAGE \
    iterate_directory.sh --resolution 1 --crs EPSG:32620 --clip-radius 5
```

#### Tip
- If you are in Windows you can get the DATA_PATH by using Powershell to `cd` into the appropriate directory, running `bash` and copying the path.  It should use forward slash `/`, instead of `\` (`\` is for Windows)
- If there are spaces in your path, escape them using `\ `
- The script will not overwrite existing files.  Make sure to delete before if you'd like to replace the existing directory.

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