
# Use the official Node.js image.
# https://hub.docker.com/_/node
FROM ubuntu:22.04

# Install system dependencies
WORKDIR /app
COPY ./install_fuse.sh /app
RUN bash install_fuse.sh

# Set fallback mount directory
ENV MNT_DIR /mnt/gcs

# Copy local code to the container image.
COPY . /app

RUN apt update && apt install -y golang-go
RUN go install github.com/consbio/mbtileserver@latest

RUN mkdir -p $MNT_DIR
RUN chown www-data:www-data $MNT_DIR
RUN chmod +x /app/gcsfuse_run.sh

# https://github.com/krallin/tini
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/gcsfuse_run.sh"] 
