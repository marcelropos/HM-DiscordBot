FROM python:3.8-alpine

WORKDIR /data
COPY . /data

RUN apk add --no-cache g++ \
 && python3 -m pip install -r requirements.txt \
 && apk del g++

CMD [ "python3", "./main.py" ]
