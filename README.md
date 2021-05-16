## Project description
This project consists of two different scripts. The first one creates a P2SH Bitcoin address 
where all funds sent to it are locked until a specific time, specified either by block height, 
or UNIX Epoch time; other than the time locking the redeem script is equivalent to P2PKH.
The second program spends all funds from this address.

## Dependencies
In order to reproduce this project it is highly recommended to create a dedicated Python 3 virtual environment
```sh
python3 -m venv bitcoin_venv
source bitcoin_venv/bin/activate
pip install -r /path/to/requirements.txt
```

### Script a (P2SH creator)
Script a creates (and prints in the console) a P2SH address with an absolute time lock expressed either in block height, 
or UNIX Epoch time

#### Arguments
script_a.py expects as input:
- network: the network to run this script, it can be 'regtest' or 'testnet' (is required to setup network in bitcoin-utils library)
- timelock: positive integer that refers to the specific time until when btcs sent to the P2SH addres will be locked
- private or public key: in order to create the P2SH address

Execution example
```sh
python script_a.py --network=regtest \
                   --public_key=028b7f1ea5b1a092028e653916ab66d3cb5027d950a5b5d8ee1f3d8a579f1c266c \
                   --timelock=150
```

### Script b (P2SH spender)
Script b sends all unspent UTXOs from a P2SH address (can be one created from script a) to a P2PKH address

#### Arguments
script_b.py expects as input:
- network: the network to run this script, it can be 'regtest' or 'testnet' (is required to setup network in bitcoin-utils library)
- p2sh: the address created with the script_a
- private_key: the one that P2SH address belongs to
- timelock: same integer value used to create the P2SH address with script_a
- p2pkh: A P2PKH address that will receive all the UTXOs send to the P2SH (destination address)
- rpc_user: RPC user of running bitcoin node in order to init proxy
- rpc_pass: RPC password of running bitcoin node in order to init proxy

Execution example
```sh
python script_b.py --network=regtest \
                   --p2sh=2N7ZMhYhdKtvkkgR2nV6n9KaAcbgGy4tH5D \ 
                   --private_key=923zDqT2JS6ggmhWKXUsvaFnHTEFPd7XKGXQfy1FvungqDCMiLE \ 
                   --timelock=150 \
                   --p2pkh={destination_address} \ 
                   --rpc_user={rpcuser} \
                   --rpc_pass={rpcpassword}
```

## Reproduction scenario
In order to replicate the use case scenario of these 2 scripts you can find bellow
a sequence of bitcoin-cli commands used on regtest network starting at blockheight 0.

Assume your private key is 923zDqT2JS6ggmhWKXUsvaFnHTEFPd7XKGXQfy1FvungqDCMiLE  
Then your public key would be 028b7f1ea5b1a092028e653916ab66d3cb5027d950a5b5d8ee1f3d8a579f1c266c

- Start a bitcoin node (regtest)  
```sh
bitcoind
```

- Execute script a:
```sh
python script_a.py --network=regtest \
                   --public_key=028b7f1ea5b1a092028e653916ab66d3cb5027d950a5b5d8ee1f3d8a579f1c266c \
                   --timelock=150
```
Given the above public key and an absolute timelock of 150 blocks the following P2SH address should be creted
2N7ZMhYhdKtvkkgR2nV6n9KaAcbgGy4tH5D

- Get blockcount
```sh
bitcoin-cli getblockcount
```

- Create or load a wallet
```sh
bitcoin-cli createwallet "mywallet" false false "" true
```
or
```sh
bitcoin-cli loadwallet "mywallet"
```

- Get wallet info
```sh
bitcoin-cli getwalletinfo
```

- Crate an address (sender address) and generate some bitcoins, in order to send them to the PS2H address
```sh
bitcoin-cli getnewaddress "sender_address" legacy
```

- List addresses of wallet
```sh
bitcoin-cli listreceivedbyaddress 1 true
```

- Generate blocks to the sender address (coinbase transaction)
```sh
bitcoin-cli generatetoaddress 120 {sender_address}
```

- Create the destination P2PKH address where we will send the UTXOs received by the P2SH address
```sh
bitcoin-cli getnewaddress "destination_address" legacy
```

- Check again addresses of wallet
```sh
bitcoin-cli listreceivedbyaddress 1 true
```

- Send bitcoin to PS2H address from the sender_address
if first transaction fee rate must be set (sathoshis per vByte) (segwit transactions 1 vB = 4 bytes, else 1 vB=1 byte)
```sh
bitcoin-cli -named sendtoaddress address=2N7ZMhYhdKtvkkgR2nV6n9KaAcbgGy4tH5D amount=1 fee_rate=100
```
else
```sh
bitcoin-cli sendtoaddress 2N7ZMhYhdKtvkkgR2nV6n9KaAcbgGy4tH5D 1
```

- Check of transactions in mempool
```sh
bitcoin-cli getrawmempool
```

Generate 1 block to complete transactions made above
```sh
bitcoin-cli generatetoaddress 1 {sender_address}
```

- Spend UTXOs from P2SH to P2PKH address (this should fail as the current blockcount is < that the one set in the timelock)
```sh
python script_b.py --network=regtest \
                   --p2sh=2N7ZMhYhdKtvkkgR2nV6n9KaAcbgGy4tH5D \ 
                   --private_key=923zDqT2JS6ggmhWKXUsvaFnHTEFPd7XKGXQfy1FvungqDCMiLE \ 
                   --timelock=150 \
                   --p2pkh={destination_address} \ 
                   --rpc_user={rpcuser} \
                   --rpc_pass={rpcpassword}
```

- Get blockcount
```sh
bitcoin-cli getblockcount
```

- Generate 29 more blocks (to reach 150 blockcount)
```sh
bitcoin-cli generatetoaddress 29 {sender_address}
```

- Retry spending UTXOs from P2SH address by executing the script_b with same parameters

- See the details of the raw transaction
```sh
bitcoin-cli decoderawtransaction {raw transaction hex}
```

- Check for the transaction in the mempool
```sh
bitcoin-cli getrawmempool
```

### Other useful bitcoin cli commands
- Check if address isvalid
```sh
bitcoin-cli validateaddress {sender_address}
```

- Check UTXOs that you can spend
```sh
bitcoin-cli listunspent
```

- Check transactions of a block
```sh
bitcoin-cli getblockhash {block count}
bitcoin-cli getblock {block hash}
```

- Check transaction details
```sh
bitcoin-cli gettransaction {transaction hash}
```
*If details category = immature the transaction was coinbase so 100 blocks have to pass until bitcoins earned can be spend