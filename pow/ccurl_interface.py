from ctypes import *
import iota
import math
import time

from pkg_resources import resource_filename
libccurl_path = resource_filename("pow","libccurl.so")

# Load ccurl lib
_libccurl = CDLL(libccurl_path)

# Return and argument types for our c functions
_libccurl.ccurl_pow.restype = POINTER(c_char)
_libccurl.ccurl_pow.argtypes = [c_char_p, c_int]

_libccurl.ccurl_digest_transaction.restype = POINTER(c_char)
_libccurl.ccurl_digest_transaction.argtypes = [c_char_p]

# calling function in libccurl to calculate nonce
# based on transaction trytes
def get_powed_tx_trytes( trytes, mwm ):
    # TODO: raise error if
    powed_trytes = _libccurl.ccurl_pow(trytes.encode('utf-8'), mwm)
    # Return value is a c_char pointer,pointing
    # to the first character
    # (c_char_p return value doesn't work for 3.7, hence this tweak)
    # We know the length of the bytearray (c char array)
    powed_trytes_bytes = powed_trytes[:2673]
    # Let's decode into unicode
    powed_trytes_unicode = powed_trytes_bytes.decode('utf-8')
    return powed_trytes_unicode

# calling function in libccurl to calculate tx hash
# based on transaction trytes (with nonce included)
def get_hash_trytes(trytes):
    hash_pointer = _libccurl.ccurl_digest_transaction(trytes.encode('utf-8'))
    # We know the length of the bytearray (c char array)
    hash_bytes = hash_pointer[:81]
    hash_unicode = hash_bytes.decode('utf-8')
    return hash_unicode

# Takes a bundle object, calculates the pow, attaches tx hash
def attach_to_tangle(bundle_trytes, # Iterable[txtrytes]
                        trunk_transaction_hash,
                        branch_transaction_hash,
                        mwm):
    previoustx = None

    # Construct bundle object
    bundle = iota.Bundle.from_tryte_strings(bundle_trytes)

    for txn in reversed(bundle.transactions):
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
        # returns a python unicode string
        powed_txn_string = get_powed_tx_trytes(txn_string, mwm)
        # construct trytestring from python string
        powed_txn_trytes = iota.TryteString(powed_txn_string)
        # Create powed txn object
        powed_txn = iota.Transaction.from_tryte_string(powed_txn_trytes)

        hash_string = get_hash_trytes(powed_txn_string)
        hash_trytes = iota.TryteString(hash_string)
        powed_txn.hash = iota.TransactionHash(hash_trytes)
        powed_txn.hash_ = iota.TransactionHash(hash_trytes)

        previoustx = powed_txn.hash
        # put that back in the bundle
        bundle.transactions[txn.current_index] = powed_txn
    return bundle.as_tryte_strings()
