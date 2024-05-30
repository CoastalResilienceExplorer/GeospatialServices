ARG BASE_IMAGE

FROM ${BASE_IMAGE}
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt

COPY ./app.py ./app.py
COPY utils /app/utils


ENV GS_SECRET_ACCESS_KEY=7oipOqgMC2b7NFI37aOJVEvUwb8/84cggjebB73U
ENV GS_ACCESS_KEY_ID=GOOG1EAWTN2EVMJWVO3ES5DLNZ6JKJ3KGK5X7ID7WXN7CVKDL47ST37B5RKT7

# ENTRYPOINT [ "python3", "app.py" ]
ENTRYPOINT [ "gunicorn" ]
CMD [ "app:app", "--bind", "0.0.0.0:8080", "--workers", "20", "--max-requests", "5", "--timeout", "3600" ]