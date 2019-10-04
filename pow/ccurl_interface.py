from ctypes import *
import iota
import math
import time

from pkg_resources import resource_filename
libccurl_path = resource_filename("pow","libccurl.so")

_libccurl = CDLL(libccurl_path)

# calling function in helpers.dll to calculate nonce based on transaction trytes 
def get_powed_tx_trytes( trytes, mwm ):
    return _libccurl.ccurl_pow(c_char_p(trytes.encode('utf-8')), c_int(mwm))

# calling function in helpers.dll to calculate tx hash based on transaction trytes (with nonce included)
def get_hash_trytes(trytes):
    return _libccurl.ccurl_digest_transaction(c_char_p(trytes.encode('utf-8')))

# Takes a bundle object, calculates the pow, attaches tx hash
def local_attach_to_tangle(bundle,
                        trunk_transaction_hash,
                        branch_transaction_hash,
                        mwm):
    previoustx = None

    for txn in reversed(bundle._transactions):
        txn.attachment_timestamp = int(round(time.time() * 1000))
        txn.attachment_timestamp_upper_bound = (math.pow(3,27) - 1) // 2
        
        if (not previoustx): # this is the tail transaction
            if txn.current_index == txn.last_index:
                txn.branch_transaction_hash = branch_transaction_hash
                txn.trunk_transaction_hash = trunk_transaction_hash
            else:
                raise ValueError('Something is not right, the last this should be the last tx in the bundle')

        else: # It is not a tail transaction
            txn.branch_transaction_hash = trunk_transaction_hash
            txn.trunk_transaction_hash = previoustx # the previous transaction
        
        # Let's do the pow locally
        txn_string = txn.as_tryte_string().__str__()
        # returns a reference to a char array
        powed_pointer = get_powed_tx_trytes(txn_string, mwm)
        # derive char array values
        powed_txn_string = c_char_p(powed_pointer).value.decode('utf-8')
        # construct trytestring from python string
        powed_txn_trytes = iota.TryteString(powed_txn_string)
        # Create powed txn object
        powed_txn = iota.Transaction.from_tryte_string(powed_txn_trytes)

        hash_pointer = get_hash_trytes(powed_txn_string)
        hash_string = c_char_p(hash_pointer).value.decode('utf-8')
        hash_trytes = iota.TryteString(hash_string)
        powed_txn.hash = iota.TransactionHash(hash_trytes)
        powed_txn.hash_ = iota.TransactionHash(hash_trytes)
        previoustx = powed_txn.hash
        # put that back in the bundle
        bundle._transactions[txn.current_index] = powed_txn
    return bundle
