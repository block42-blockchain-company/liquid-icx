# Liquid ICX (LICX)

Secure the ICON network, earn staking rewards while staying liquid. 🧽💧

### About LICX protocol

##### ICON network staking

On ICON network the native token (ICX) can be staked in the protocol which gives stakers a passive return in form of ICX tokens but the staked tokens are locked and can not be moved while the ICX is staked. 

##### LICX

LICX is IRC-2 token standard implementation, where 1 LICX represents 1 ICX staked in the LICX pool.
The main goal of LICX implementation is for users to be able to transfer assets, while still getting staking rewards. 

LICX can be used for personal use to stake ICX and still be able to transfer it from one wallet to another while the rewards earned are getting restaked and redelegated so the users can get compounding interest on their investment.

Protocols that only use IRC-2 tokens can use LICX instead of ICX, similar to wrapped assets on other networks (for example wETH).
Protocols that hold ICX can hold LICX instead and the users can also benefit from the network staking rewards.
Protocols where users can spend their ICX can accept LICX instead and allow user to also receive the staking rewards.

As stated above the ratio between LICX and ICX will always stay 1:1.
LICX is achieving that by air-dropping rewards each prep-term. Air-drop does not happen through the transfer function but it just increases the amount of LICX in wallets based on the amount of LICX a specific wallet has at the time of the distribution.
This allows ease of use for the users as they always know the amount of ICX they are dealing with when interacting with LICX.

#### Depositing and withdrawal

###### Deposit

Depositing ICX into LICX protocol will put all the assets into the LICX pool. User will receive LICX (in ratio of 1:1) to their wallet as proof that they have deposited ICX into the LICX pool. When depositing ICX into LICX pool it will take 2 terms (2 days) before LICX becomes transferable and eligible for rewards. Because the ICON network staking rewards are first distributed after 2 terms this is a necessary step. After the two terms LICX will be unlocked and transferable.

###### Withdrawal

Depositing LICX into LICX protocol will withdraw ICX (in ratio of 1:1) from the LICX pool. When withdrawing ICX it will take between 5 to 20 terms (days) based on the unstaking period that the ICON network currently has. The number of days depends on the amount the ICX staked in the ICON network, the higher the % of ICON network is staked the fewer days you need to wait to unstake. User will have to manually claim their ICX once it has been unstaked (after the unstaking period).
*If a user would stake on his own he would have to also wait the same amount of days to unstake.*

###### Rewards
Staking rewards distribution from the network can happen only once per term and has to be manually triggered. Anyone can trigger this function which will execute claiming new rewards, distribution of LICX to eligible users, restaking and redelegating ICX.
Wallets that have less than 10 LICX in them are not eligible to prevent dust attacks (this number may be a subject to change).
***
### LICX functions
LICX implements all the standard IRC-2 methods.

- name
- symbol
- decimals
- totalSupply
- balanceOf
- transfer

To participate at the pool/protocol,they are also some other methods implemented.
##### Join
```python
def join(self, delegation: str = None)
```
It's a payable function, that adds a join (mint) request to the wallet, which converts ICX to LICX. Requests are resolved once per term in distribute function. 
Each wallet has maximum of 10 join requests per term. LICX tokens are locked for 2 terms, since they are not producing any rewards yet, 
meaning you can not transfer them.  

The ICX is also being staked and delegated to prep addresses that user provided when calling a function.
In case the user does not care and does not pass any delegations, then they voting power is proportionally divided between
all the preps, that SCORE is currently delegating.

##### Leave
```python
def leave(self, _value: int = None)
```
Adds a leave (burn) request to the wallet, which converts LICX back to ICX. Similar to the joining requests, leave requests are resolved
once per term only.   
User can specify the leaving amount/value, meaning they can burn all of their LICX tokens or just part of it. In case that _value 
is not passed to the function call, all of their tokens will be burned in the next distribute cycle.

#### Vote
```python
def vote(self, delegation: str)
```
Allows users (who joined the protocol) to change their delegations. Meaning, all the previous delegations are removed and the new ones are added.

#### Claim
```python
def claim(self)
```
Sends all currently available user's ICX from SCORE back to the account.

#### Distribute
```python
def distribute(self)
```
This function distributes rewards to the all the eligible wallets (currently wallets with more than 10 ICX, but this value can be changed) 
involved in protocol, it also resolves each wallets join/leave requests. 
The function mints and burns the LICX (total supply and each wallet balance is being updated).
Everyone can call the function, which benefits the whole ecosystem. In the future incentives to call the function will be implemented.

## Development
### Installation

To start local development you can choose between two options.

1. Install and run tbears in docker container (quick and easy) or you can 
2. Install tbears with PIP.

#### 1. Docker
```bash
docker run -it --name local-tbears -p 9000:9000 -v /path/to/repo/liquid-icx/score:/work iconloop/tbears:mainnet
```

This command will do the following

* download tbears docker image
* create and start a container
* create a volume
* and attach stdin/stderr to the container

#### 2. Pip
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
