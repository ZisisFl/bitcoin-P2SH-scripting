## Project description
This project consists of two different scripts. The first one creates a P2SH Bitcoin address where all funds sent to it are locked
until a specific time, specified either by block height, or UNIX Epoch time; other than the
time locking the redeem script is equivalent to P2PKH.
The second program spends all funds from this address.

## Dependencies
In order to reproduce this project it is highly recommended to create a dedicated Python 3 virtual environment 

### Script a
script_a.py expects 

### Script b
script_a.py expects 

## Reproduce
Assume your private key is 923zDqT2JS6ggmhWKXUsvaFnHTEFPd7XKGXQfy1FvungqDCMiLE
Then you public key would be 028b7f1ea5b1a092028e653916ab66d3cb5027d950a5b5d8ee1f3d8a579f1c266c

Start a bitcoin node
bitcoind

Run script a:
```
python script_a.py --network=regtest --public_key=028b7f1ea5b1a092028e653916ab66d3cb5027d950a5b5d8ee1f3d8a579f1c266c --timelock=150
```
Given the above public key and a timelock of 150 blocks the following P2SH address has has been created
2N7ZMhYhdKtvkkgR2nV6n9KaAcbgGy4tH5D


Get blockcount
bitcoin-cli getblockcount
If blockcount is smaller than the timelock set in blockheight then keep going else create a new PS2H address

Create or load a wallet
bitcoin-cli createwallet "mywallet" false false "" true
or
bitcoin-cli loadwallet "mywallet"

bitcoin-cli getwalletinfo

Crate an address to add some bitcoins to send to the PS2H address
bitcoin-cli getnewaddress "sender_address" legacy => mjE55wtCX2NV5DuVojW69T83o3vav16AvN

List addresses of a wallet
bitcoin-cli listreceivedbyaddress 1 true

Check account balalnce
bitcoin-cli getbalance

Get privatekey from address
bitcoin-cli dumpprivkey mjE55wtCX2NV5DuVojW69T83o3vav16AvN

Check if address isvalid
bitcoin-cli validateaddress mjE55wtCX2NV5DuVojW69T83o3vav16AvN

Generate blocks to the sender address (coinbase transaction)
bitcoin-cli generatetoaddress 120 mjE55wtCX2NV5DuVojW69T83o3vav16AvN

Create the destination P2PKH address
bitcoin-cli getnewaddress "destination_address" legacy => mm4r7DcUDMgErxV3rkAVWf93YcZ3MDzDUn

Send bitcoin to PS2H address from the sender_address
bitcoin-cli -named sendtoaddress address=2N7ZMhYhdKtvkkgR2nV6n9KaAcbgGy4tH5D amount=1 fee_rate=1

Check of transactions in mempool
bitcoin-cli getrawmempool

Get info for a txid
bitcoin-cli getmempoolentry {txid}

Send btc from P2SH to P2PKH address
python script_b.py --network=regtest --p2sh=2N7ZMhYhdKtvkkgR2nV6n9KaAcbgGy4tH5D --private_key=923zDqT2JS6ggmhWKXUsvaFnHTEFPd7XKGXQfy1FvungqDCMiLE --timelock=150 --p2pkh=mm4r7DcUDMgErxV3rkAVWf93YcZ3MDzDUn



Get the details of a transaction
bitcoin-cli decoderawtransaction {raw transaction hex}

Check UTXOs that you can spend
bitcoin-cli listunspent

Send bitcoins to the locked P2SH address
if first transaction fee rate must be set (sathoshis per vByte) (segwit transactions 1 vB = 4 bytes, else 1 vB=1 byte)
bitcoin-cli -named sendtoaddress address=2N7ZMhYhdKtvkkgR2nV6n9KaAcbgGy4tH5D amount=1 fee_rate=1
else
bitcoin-cli sendtoaddress 2N7ZMhYhdKtvkkgR2nV6n9KaAcbgGy4tH5D 1

txid = abe5ed0f7fd460d0c65b6efa681684e0e002b14d6202f12518a97fb0463aa5d2 στο mempool αφου δεν εχει κλεισει το block akoma
Get transactions in the mempool
bitcoin-cli getrawmempool

Get info for a txid
bitcoin-cli getmempoolentry {txid}
or because this is my transaction
bitcoin-cli gettransaction {txid}


If listreceivedbyaddress is used it will be empty because coinbase transactions are not listed there



Check transactions of a block
bitcoin-cli getblockhash {block count}
bitcoin-cli getblock {block hash}

Get transaction details
bitcoin-cli gettransaction {transaction hash}
if details category = immature 
To spend coinbase transactions 100 blocks have to pass until bitcoins earned can be spend

