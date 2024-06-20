MOUNT_PATH=/app/data

docker build -t mosaic --platform linux/amd64 .
docker run -it \
    -v $PWD:/app \
    -v /GeospatialServicesData:/app/data \
    --entrypoint python3 \
    -p 4000:8080 \
    -e MOUNT_PATH=${MOUNT_PATH} \
    mosaic \
    app.py