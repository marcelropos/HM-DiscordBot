FROM python:3.8

WORKDIR /data

COPY . /data

RUN python3 -m pip install -r requirements.txt

CMD [ "python", "./server.py" ]
