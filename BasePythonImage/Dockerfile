FROM python:3.11.6

RUN apt update
RUN apt install -y gdal-bin libgdal-dev

WORKDIR /app
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt

# docker build -t base_image .