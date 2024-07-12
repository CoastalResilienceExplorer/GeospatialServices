# ARG BASE_IMAGE

# FROM ${BASE_IMAGE}
# COPY ./requirements.txt .
# RUN pip3 install -r requirements.txt

FROM ghcr.io/osgeo/gdal:ubuntu-full-latest
WORKDIR /app
RUN apt update && apt install -y python3-pip

COPY ./requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt --break-system-packages
COPY ./app.py ./app.py
COPY utils /app/utils

ENV GS_SECRET_ACCESS_KEY=7oipOqgMC2b7NFI37aOJVEvUwb8/84cggjebB73U
ENV GS_ACCESS_KEY_ID=GOOG1EAWTN2EVMJWVO3ES5DLNZ6JKJ3KGK5X7ID7WXN7CVKDL47ST37B5RKT7

# ENTRYPOINT [ "python3", "app.py" ]
ENTRYPOINT [ "gunicorn" ]
CMD [ "app:app", "--bind", "0.0.0.0:8080", "--workers", "5", "--max-requests", "1", "--timeout", "3600" ]