ARG BASE_IMAGE

FROM ${BASE_IMAGE}
COPY ./requirements.txt .
COPY ./mesh2tiff.py ./mesh2tiff.py
RUN pip3 install -r requirements.txt
ENTRYPOINT [ "python3", "mesh2tiff.py" ]