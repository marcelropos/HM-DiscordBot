FROM python:3.9

WORKDIR /app
COPY . /app

RUN apt update && apt install -y ffmpeg libopus0 opus-tools \
    && python3 -m pip install -r requirements.txt


CMD [ "python3", "-O",  "main.py" ]
