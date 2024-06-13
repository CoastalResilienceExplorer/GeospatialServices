FROM ghcr.io/osgeo/gdal:ubuntu-full-latest
WORKDIR /app
RUN apt update && apt install -y python3-pip

COPY ./requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt --break-system-packages
COPY . /app

ENTRYPOINT [ "gunicorn" ]
CMD [ "app:app", "--bind", "0.0.0.0:8080", "--workers", "16", "--max-requests", "1", "--max-requests-jitter", "2", "--timeout", "7200" ]