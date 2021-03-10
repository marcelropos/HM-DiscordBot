FROM python:3.8-alpine

WORKDIR /app
COPY . /app

RUN apk add gcc libc-dev \
    && python3 -m pip install -r requirements.txt \
    && apk del gcc libc-dev

CMD [ "python3", "main.py" ]
