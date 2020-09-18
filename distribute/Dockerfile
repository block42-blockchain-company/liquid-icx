#base image
FROM python:3.7

ADD . /

RUN pip3 install -r requirements.txt

CMD [ "python3", "bot/licx_distribute_bot.py" ]
