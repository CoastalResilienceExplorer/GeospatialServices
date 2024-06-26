docker build -t ss .

docker run -it \
    -p 4000:8080 \
    --entrypoint python3 \
    -e MOUNT_PATH=${MOUNT_PATH} \
    -v $PWD:/app \
    -v ${DATA_FOLDER}:${MOUNT_PATH} \
    ss app.py