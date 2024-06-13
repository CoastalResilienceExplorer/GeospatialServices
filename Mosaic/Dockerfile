FROM ghcr.io/osgeo/gdal:ubuntu-full-latest
WORKDIR /app
RUN apt update && apt install -y python3-pip

COPY . /app/
RUN pip3 install -r requirements.txt --break-system-packages

ENTRYPOINT [ "gunicorn" ]
CMD [ "app:app", "--bind", "0.0.0.0:8080", "--workers", "20", "--max-requests", "2", "--timeout", "3600" ]