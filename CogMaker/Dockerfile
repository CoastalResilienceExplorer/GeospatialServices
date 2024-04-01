ARG BASE_IMAGE

FROM ${BASE_IMAGE}
COPY ./requirements.txt .
COPY ./app.py ./app.py
COPY utils /app/utils
RUN pip3 install -r requirements.txt
ENTRYPOINT [ "python3", "app.py" ]