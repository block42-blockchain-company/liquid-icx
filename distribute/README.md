# Liquid-ICX Telegram Bot

### Development
The easiest way to start a bot is via:
 ```
python3 licx_distribute_bot.py
```
### Production
It is recommended to run a bot in a docker container.
Execute to command bellow to build an image:
 ```
docker build -t licx-bot .
```
And later, to run the docker container execute:
 ```
docker run --env-file variables.env --name licx-bot licx-bot
```
