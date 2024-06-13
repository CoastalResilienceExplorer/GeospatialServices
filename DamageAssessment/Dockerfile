FROM ghcr.io/osgeo/gdal:ubuntu-full-latest
WORKDIR /app
RUN apt update && apt install -y python3-pip

ENV GS_SECRET_ACCESS_KEY=7oipOqgMC2b7NFI37aOJVEvUwb8/84cggjebB73U
ENV GS_ACCESS_KEY_ID=GOOG1EAWTN2EVMJWVO3ES5DLNZ6JKJ3KGK5X7ID7WXN7CVKDL47ST37B5RKT7
COPY ./requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt --break-system-packages
COPY . /app

RUN set -e; \
    apt-get update -y && apt-get install -y \
    tini \
    lsb-release; \
    gcsFuseRepo=gcsfuse-`lsb_release -c -s`; \
    echo "deb https://packages.cloud.google.com/apt $gcsFuseRepo main" | \
    tee /etc/apt/sources.list.d/gcsfuse.list; \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    apt-key add -; \
    apt-get update; \
    apt-get install -y gcsfuse \
    && apt-get clean


# Ensure the script is executable
RUN chmod +x /app/gcsfuse_run.sh

# https://github.com/krallin/tini
ENTRYPOINT ["/usr/bin/tini", "--"] 

# Pass the startup script as arguments to Tini
CMD ["/app/gcsfuse_run.sh"]

# ENTRYPOINT [ "gunicorn" ]
# CMD [ "app:app", "--bind", "0.0.0.0:8080", "--workers", "40", "--max-requests", "3", "--max-requests-jitter", "3", "--timeout", "3600" ]