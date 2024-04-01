ARG BASE_IMAGE

FROM ${BASE_IMAGE}
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt
COPY ./app.py ./app.py
COPY ./countries-codes.csv ./countries-codes.csv
ENTRYPOINT [ "python3", "app.py" ]