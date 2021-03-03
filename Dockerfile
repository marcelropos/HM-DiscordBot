FROM python:latest
RUN python -m pip install discord
RUN python -m pip install pyotp
RUN python -m pip install requests
RUN python -m pip install bs4
WORKDIR /app:
ADD . .
CMD ["python", "main.py"]
