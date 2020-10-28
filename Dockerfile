FROM python:3.8

WORKDIR /data

COPY . /data

ENV TOKEN /data

RUN python3 -m pip install -r requirements.txt

CMD [ "python3", "./main.py" ]
