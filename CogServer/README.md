## Purpose
To serve raster tiles from GCS

### Sources
- https://cogeotiff.github.io/rio-tiler/advanced/dynamic_tiler/
- https://github.com/cogeotiff/rio-tiler
- https://cogeotiff.github.io/rio-tiler/colormap/

### TODO
- Add capacity to query a point, line, and polygon
- Add proper test case in deployment, maybe just by querying a `0/0/0.png` tile and seeing if we get a result

# Local Development
1. Build an image with `bash build_and_submit.sh dev`
or 
```
ENV=staging
docker build --build-arg BUCKET=gs://cogmaker-output-${ENV} --build-arg BASE_IMAGE=us-west1-docker.pkg.dev/global-mangroves/base/python_gis_base_${ENV} -t us-west1-docker.pkg.dev/global-mangroves/cogserver/cogserver_${ENV} .
docker run -it -v $PWD:/app --entrypoint uvicorn -p 3004:8080 us-west1-docker.pkg.dev/global-mangroves/cogserver/cogserver_${ENV} app:app --reload --host 0.0.0.0 --port 8080
```