FROM python:3.10.14

WORKDIR /app
COPY ./requirements.txt /app

RUN pip3 install -r requirements.txt

COPY ./ /app

ENTRYPOINT [ "gunicorn" ]
CMD [ "app:app", "--bind", "0.0.0.0:8080", "--workers", "4", "--max-requests", "2", "--timeout", "3600" ]
