# Liquid-ICX Telegram Bot

This Telegram Bot checks periodically if a new ICON term has started
and calls LICX's `distribute` function if that's the case.
In addition, the telegram user can also manually invoke a method
call `distribute`.

## Environment variables
Set the following environment variables in your environment or in the files
`variables_mainnet.env` and `variables_testnet.env` respectively:
- `TELEGRAM_BOT_TOKEN` to your Telegram Bot Token obtained from [BotFather](#create-telegram-bot-token-via-botfather)
- `NETWORK` to either `MAINNET` or `TESTNET` (defaults to TESTNET if written incorrectly)
- `SCORE_ADDRESS` to the LICX SCORE address
- `PRIVATE_KEY` to the private key of the wallet that should invoke `distribute` and pay the transaction fee
- `ADMIN_USER_IDS` to a comma separated list of Telegram User IDs that are permissioned to interact with the Telegram Bot.
E.g.: `ADMIN_USER_IDS=1234,5678`

#### [Create Telegram bot token via BotFather](#create-telegram-bot-token-via-botfather)
Start a Telegram chat with [BotFather](https://t.me/BotFather) and click `start`.

Then send `/newbot` in the chat, and follow the given steps to create a new telegram token. Save this token, you will need it in a second.

Beware that you need a separate Telegram Bot for each Network you want the bot to run on, 
i.e. one Token for Mainnet and one for Testnet.

## Development
After setting the environment variables, the easiest way to start a bot is via:
 ```
python3 licx_distribute_bot.py
```

## Production
It is recommended to run a bot in a docker container.
Execute to command below to build an image:
 ```
docker build -t licx-bot .
```
And later, to run the docker container execute:
 ```
# For Mainnet
docker run --env-file variables_mainnet.env --name licx-bot licx-bot

# For Testnet
docker run --env-file variables_testnet.env --name licx-bot licx-bot
```
