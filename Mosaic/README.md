MOUNT_PATH=/app/data

docker build -t mosaic .
docker run -it \
    -v $PWD:/app \
    -v /GeospatialServicesData:/app/data \
    --entrypoint python3 \
    -p 4000:8080 \
    -e MOUNT_PATH=${MOUNT_PATH} \
    mosaic \
    app.py