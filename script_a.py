import argparse
from bitcoinutils.transactions import Sequence, Locktime
from bitcoinutils.constants import TYPE_ABSOLUTE_TIMELOCK, TYPE_RELATIVE_TIMELOCK
from bitcoinutils.keys import P2pkhAddress, P2shAddress, PrivateKey, PublicKey
from bitcoinutils.script import Script
from helper import check_time_lock, handle_input_keys, setup_network

from automated_tests import test_timelock


def parse_command_line_arguments():
    # python script_a.py -h will print usage info in the console
    parser = argparse.ArgumentParser(description='Generate a P2SH address with absolute timelock')

    parser.add_argument('--network', help='Network to use', type=str, required=True)
    parser.add_argument('--public_key', help='Public key', type=str)
    parser.add_argument('--private_key', help='Private key', type=str)
    parser.add_argument('--timelock', help='Lock until specific block height or Unix Epoch timestamp (absolute)', type=int, required=True)

    return parser.parse_args()


def create_timelocked_p2sh_address(public_key, private_key, timelock):
    if public_key:
        p2pkh_addr = PublicKey(public_key).get_address()
    elif private_key:
        p2pkh_addr = PrivateKey(private_key).get_public_key().get_address()

    # create sequence
    seq = Sequence(TYPE_ABSOLUTE_TIMELOCK, timelock)

    # create the redeem script
    redeem_script = Script([seq.for_script(), 'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP', 'OP_DUP', 'OP_HASH160', p2pkh_addr.to_hash160(), 'OP_EQUALVERIFY', 'OP_CHECKSIG'])

    # create a P2SH address from the redeem script
    p2sh_addr = P2shAddress.from_script(redeem_script)

    return p2sh_addr, seq, redeem_script


def main():
    # parse input script arguments
    args = parse_command_line_arguments()

    # check if timelock is valid
    check_time_lock(args.timelock)

    # check keys provided
    handle_input_keys(args.public_key, args.private_key)
    
    # check network input and setup
    setup_network(args.network)
    
    # create P2SH address
    p2sh_addr, seq, redeem_script = create_timelocked_p2sh_address(args.public_key, args.private_key, args.timelock)
    print('Created P2SH address: {}'.format(p2sh_addr.to_string()))


if __name__ == "__main__":
    # For testing
    # PRIVATE KEY (wif compressed) 923zDqT2JS6ggmhWKXUsvaFnHTEFPd7XKGXQfy1FvungqDCMiLE
    # PUBLIC KEY (hex) 028b7f1ea5b1a092028e653916ab66d3cb5027d950a5b5d8ee1f3d8a579f1c266c

    # execute script
    # python script_a.py --network=regtest --public_key=028b7f1ea5b1a092028e653916ab66d3cb5027d950a5b5d8ee1f3d8a579f1c266c --timelock=150

    main()