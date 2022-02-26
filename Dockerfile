FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt /app
RUN python3 -m pip install -r requirements.txt

COPY . /app


CMD [ "python3", "-O",  "main.py" ]
