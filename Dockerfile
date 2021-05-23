FROM python

WORKDIR /app
COPY . /app

RUN python3 -m pip install --upgrade pip && python3 -m pip install -r requirements.txt

CMD [ "python3", "-O",  "main.py" ]
