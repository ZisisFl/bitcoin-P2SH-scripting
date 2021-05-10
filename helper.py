import warnings
from time import time
from datetime import datetime

from bitcoinutils.setup import setup


def setup_network(input_network):
    # check network chosen
    if input_network not in ['regtest', 'testnet', 'mainet']:
        parser.print_help()
        raise ValueError('Target network is invalid')
    else:
        setup(input_network)


def check_time_lock(timelock):
    # get current timestamp in unix
    current_timestamp_in_unix = int(time())

    if timelock > 500000000:
        if timelock < current_timestamp_in_unix:
            warnings.warn('Timelock set to a past timestamp')
        else:
            print('Timelock set to date {}'.format((datetime.utcfromtimestamp(timelock).strftime('%Y-%m-%d %H:%M:%S'))))
    elif timelock > 0:
        print('Timelock set to block height {}'.format(timelock))
    else:
        raise ValueError('Invalid timelock')


def handle_input_keys(public_key, private_key):
    if (public_key is None) and (private_key is None):
        raise ValueError('At least one of private or public key must to be provided')
    elif (public_key is not None) and (private_key is not None):
        warnings.warn('Both private and public key have been specified, public key will be used')