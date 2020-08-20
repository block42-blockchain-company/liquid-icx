#base image
FROM python:3.7

COPY main.py/ /
COPY requirements.txt/ /
COPY variables.env/ /

RUN pip3 install -r requirements.txt

CMD [ "python3", "./main.py" ]