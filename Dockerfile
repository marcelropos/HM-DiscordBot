FROM python:3.8-alpine

WORKDIR /data
COPY . /data

RUN apk add --no-cache --virtual .build-deps gcc libc-dev \
 && python3 -m pip install -r requirements.txt \
 && apk del .build-deps

CMD [ "python3", "./main.py" ]
