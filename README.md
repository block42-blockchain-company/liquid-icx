# Liquid ICX (LICX)

Secure the ICON network, earn staking rewards while staying liquid. 🧽💧

## Installation

To start local development you can choose between two options. 

1. Install and run tbears in docker container (quick and easy) or you can 
2. Install tbears with PIP.

#### Docker
```bash
docker run -it --name local-tbears -p 9000:9000 -v /path/to/repo/liquid-icx/score:/work iconloop/tbears:mainnet
```

This command will do the following

* download tbears docker image
* create and start a container
* create a volume
* and attach stdin/stderr to the container

#### Pip
##### MacOS
```bash
# install develop tools
$ brew install leveldb
$ brew install autoconf automake libtool pkg-config

# install RabbitMQ and start service
$ brew install rabbitmq
$ brew services start rabbitmq

# Create a working directory
$ mkdir work
$ cd work

# setup the python virtualenv development environment
$ pip3 install virtualenv
$ virtualenv -p python3 .
$ source bin/activate

# Install the ICON SCORE dev tools
(work) $ pip install tbears

```

##### Linux
```bash
# Install levelDB
$ sudo apt-get install libleveldb1 libleveldb-dev
# Install libSecp256k
$ sudo apt-get install libsecp256k1-dev

# install RabbitMQ and start service
$ sudo apt-get install rabbitmq-server

# Create a working directory
$ mkdir work
$ cd work

# Setup the python virtualenv development environment
$ virtualenv -p python3 .
$ source bin/activate

# Install the ICON SCORE dev tools
(work) $ pip install tbears
```