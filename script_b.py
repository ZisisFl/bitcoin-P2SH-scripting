import argparse
import requests
import json
from bitcoinutils.utils import to_satoshis
from bitcoinutils.transactions import Sequence, TxInput, TxOutput, Transaction, Locktime
from bitcoinutils.constants import TYPE_ABSOLUTE_TIMELOCK
from bitcoinutils.script import Script
from bitcoinutils.proxy import NodeProxy
from bitcoinutils.keys import PrivateKey, P2pkhAddress
from decimal import Decimal

from helper import setup_network


def parse_command_line_arguments():
    """Parse execution parameters

    Help: python script_b.py -h, will print usage info in the console
    """
    parser = argparse.ArgumentParser(description='Spend all UTXOs from P2SH address')

    parser.add_argument('--network', help='Network to use', type=str, required=True)
    parser.add_argument('--p2sh', help='P2SH address to send Bitcoins from (sender)', type=str, required=True)
    parser.add_argument('--private_key', help='Private key of P2SH address', type=str, required=True)
    parser.add_argument('--timelock', help='Locktime value used to generate P2SH address', type=int, required=True)
    parser.add_argument('--p2pkh', help='P2PKH address to send Bitcoins to (destination)', type=str, required=True)
    parser.add_argument('--rpc_user', help='RPC user of running node', type=str, required=True)
    parser.add_argument('--rpc_pass', help='RPC password of running node', type=str, required=True)

    return parser.parse_args()


def setup_node_proxy(user, password):
    """Create NodeProxy object to communicate with bitcoin node through RPC
    """

    return NodeProxy(user, password).get_proxy()


def get_recommended_fees():
    """Retrieves current recommended fastest fees from bitcoinfees API in satoshis
    """

    uri = 'https://bitcoinfees.earn.com/api/v1/fees/recommended'

    response = requests.get(uri)

    if response.status_code == 200:
        fees = json.loads(response.text) 
        return fees['fastestFee']

    elif response.status_code == 404:
        raise requests.exceptions.InvalidURL
    
    else:
        raise requests.exceptions.RequestExc


def calculate_transaction_size(n_of_txin, n_of_txout):
    """Transaction size in bytes based on inputs and outputs for non segwit addresses
    """

    return (n_of_txin * 180) + (n_of_txout * 34) + 10 + n_of_txin



def recreate_redeem_script(private_key, timelock):
    """Recreate redeem script as it was originally created in script_a
    """

    p2pkh_addr = private_key.get_public_key().get_address()

    seq = Sequence(TYPE_ABSOLUTE_TIMELOCK, timelock)

    redeem_script = Script([seq.for_script(), 'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP', 'OP_DUP', 'OP_HASH160', p2pkh_addr.to_hash160(), 'OP_EQUALVERIFY', 'OP_CHECKSIG'])
    
    return redeem_script, seq


def is_transaction_valid(proxy, raw_transaction_hex):
    """Check if transaction created is valid
    """

    assessment = proxy.testmempoolaccept(raw_transaction_hex)[0] 

    if not assessment['allowed']:
        exit('Invalid transaction: {}'.format(assessment['reject-reason']))
    else:
        return assessment['allowed']


def send_to_p2pkh_address(private_key, timelock, p2sh_unspent_transactions, p2pkh_address, proxy):
    """Sends all available UTXOs found in P2SH to a P2PKH address
    """

    redeem_script, seq = recreate_redeem_script(private_key, timelock)

    list_of_txin = []
    btc_unspent = 0

    for utxo in p2sh_unspent_transactions:
        # create a list of input transactions from the UTXOs found in the P2SH address
        list_of_txin.append(TxInput(utxo['txid'], utxo['vout'], sequence=seq.for_input_sequence()))

        # sum btc found in each UTXO
        btc_unspent = btc_unspent + utxo['amount']

    transaction_size = calculate_transaction_size(len(list_of_txin), 1)
    recommended_fees = get_recommended_fees()

    # get fees as transaction size in bytes * satoshis per byte recommended from API
    fees = transaction_size * recommended_fees 
    print('''Transaction size will be about {} bytes and current recommended fee rate in satoshis per byte is {}'''.format(transaction_size, recommended_fees))

    amount = int((Decimal(str(to_satoshis(btc_unspent))) - Decimal(str(fees))))
    print('\nAmount to be sent is {} satoshis'.format(amount))

    # create txout
    txout = TxOutput(amount, p2pkh_address.to_script_pub_key())

    # create locktime to use in transaction
    lock = Locktime(timelock)

    # create transaction from input(s) and output transactions and locktime object
    tx = Transaction(list_of_txin, [txout], lock.for_transaction())

    print('\nRaw unsigned transaction: {}'.format(tx.serialize()))
    
    # sign txins
    for index, txin in enumerate(list_of_txin):
        # create signature
        sig = private_key.sign_input(tx, index, redeem_script)

        txin.script_sig = Script([sig, private_key.get_public_key().to_hex(), redeem_script.to_hex()])

    signed_tx = tx.serialize()
    print('\nRaw signed transaction: {}'.format(signed_tx))
    print('\nTransaction id: {}'.format(tx.get_txid()))

    if is_transaction_valid(proxy, [signed_tx]):
        print('\nTransaction is valid!')

        # if transaction is valid send it to the blockchain
        proxy.sendrawtransaction(signed_tx)


def get_UTXOs(proxy, p2sh):
    """Parse unspent UTXOs of the provided P2SH address 
    """
    # add p2sh address to your wallet to watch its transactions
    proxy.importaddress(p2sh)

    # get unspent transactions of wallet
    unspent_transactions = proxy.listunspent()

    # keep unspent of p2sh address
    p2sh_unspent_transactions = list(filter(lambda utxo: utxo['address'] == p2sh, unspent_transactions))

    return p2sh_unspent_transactions


def main():
    # parse input script arguments
    args = parse_command_line_arguments()

    # setup network
    setup_network(args.network)

    # setup node proxy
    proxy = setup_node_proxy(args.rpc_user, args.rpc_pass)

    # init private key and destination P2PKH address objects
    private_key = PrivateKey(args.private_key)
    p2pkh = P2pkhAddress(args.p2pkh)

    # if P2SH address has no UTXOs terminate script else send all of them to destination address
    p2sh_unspent_transactions = get_UTXOs(proxy, args.p2sh)

    if len(p2sh_unspent_transactions) == 0:
        exit('P2SH address has no UTXOs available to be spent')
    else:
        send_to_p2pkh_address(private_key, args.timelock, p2sh_unspent_transactions, p2pkh, proxy)


if __name__ == "__main__":
    """Testing
    
    PRIVATE KEY (wif compressed) 923zDqT2JS6ggmhWKXUsvaFnHTEFPd7XKGXQfy1FvungqDCMiLE
    PUBLIC KEY (hex) 028b7f1ea5b1a092028e653916ab66d3cb5027d950a5b5d8ee1f3d8a579f1c266c

    Script execution example (using P2SH address created by script a)
    python script_b.py --network=regtest \
                       --p2sh=2N7ZMhYhdKtvkkgR2nV6n9KaAcbgGy4tH5D \ 
                       --private_key=923zDqT2JS6ggmhWKXUsvaFnHTEFPd7XKGXQfy1FvungqDCMiLE \ 
                       --timelock=150 \
                       --p2pkh={destination_address} \ 
                       --rpc_user={rpcuser} \
                       --rpc_pass={rpcpassword}
    """

    main()