from ctypes import *
import iota
import math
import time

# Load the compiled C library
from pkg_resources import resource_filename
libpow_path = resource_filename("pow","helpers.dll")

_libpow = CDLL(libpow_path)

# calling function in helpers.dll to calculate nonce based on transaction trytes 
def get_nonce( trytes, mwm ):
    return _libpow.iota_pow_trytes(c_char_p(trytes.encode('utf-8')), c_int(mwm))

# calling function in helpers.dll to calculate tx hash based on transaction trytes (with nonce included)
def get_hash(trytes):
    return _libpow.iota_digest(c_char_p(trytes.encode('utf-8')))

# Takes a bundle object, calculates the pow, attaches tx hash
def attach_to_tangle(bundle_trytes,
                        branch_transaction_hash,
                        trunk_transaction_hash,
                        mwm):
    previoustx = None

    # Construct bundle object
    bundle = iota.Bundle.from_tryte_strings(bundle_trytes)

    # Iterate thorugh transactions in the bundle, starting from the tail
    for txn in reversed(bundle.transactions):
        # Fill out attachment timestamp, field is used to calculate nonce
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
        
        # Let's do the pow locally (calculate nonce)
        txn_string = txn.as_tryte_string().__str__()
        # returns a reference to a char array
        nonce_pointer = get_nonce(txn_string, mwm)
        # derive char array values
        nonce_string = c_char_p(nonce_pointer).value.decode('utf-8')
        # construct trytestring from python string
        nonce_trytes = iota.TryteString(nonce_string)
        # assign it to the tx
        txn.nonce = iota.Nonce(nonce_trytes)

        # Calculate transaction hash
        hash_pointer = get_hash(txn.as_tryte_string().__str__())
        hash_string = c_char_p(hash_pointer).value.decode('utf-8')
        hash_trytes = iota.TryteString(hash_string)
        # Assign hash to transaction object
        txn.hash = iota.TransactionHash(hash_trytes)
        txn.hash_ = iota.TransactionHash(hash_trytes)

        previoustx = txn.hash
        # put that back in the bundle
        bundle.transactions[txn.current_index] = txn
    return bundle.as_tryte_strings()
