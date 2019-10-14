from ctypes import *
import iota
import math
import time
from iota.exceptions import with_context

from pkg_resources import resource_filename
libccurl_path = resource_filename("pow","libccurl.so")

# Calculate time in milliseconds (for timestamp)
get_current_ms = lambda : int(round(time.time() * 1000))

# Load ccurl lib
_libccurl = CDLL(libccurl_path)

# Return and argument types for our c functions
_libccurl.ccurl_pow.restype = POINTER(c_char)
_libccurl.ccurl_pow.argtypes = [c_char_p, c_int]

_libccurl.ccurl_digest_transaction.restype = POINTER(c_char)
_libccurl.ccurl_digest_transaction.argtypes = [c_char_p]

def check_tx_trytes_length(trytes):
    """
    Checks if trytes are exactly one transaction in length.
    """
    if len(trytes) != iota.TransactionTrytes.LEN:
        raise with_context(
            exc=ValueError('Trytes must be {len} trytes long.'.format(
                len= iota.TransactionTrytes.LEN
            )),

            context={
                'trytes': trytes,
            },
        )

# calling function in libccurl to calculate nonce
# based on transaction trytes
def get_powed_tx_trytes( trytes, mwm ):
    """
    Calls `ccurl_pow` function from ccurl
    library to calculate `nonce`. Returns transaction
    trytes with calucalted nonce included, in unicode
    string format.
    """
    # Make sure we supply the right size of tx trytes to ccurl
    check_tx_trytes_length(trytes)
    # Call of external C function
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
    """
    Calls `ccurl_digest_transaction` function from ccurl
    library to calculate `rtansaction hash`. Returns the
    81 trytes long hash in unicode string format.
    """
    # Make sure we supply the right size of tx trytes to ccurl
    check_tx_trytes_length(trytes)
    # Call of external C function
    hash_pointer = _libccurl.ccurl_digest_transaction(trytes.encode('utf-8'))
    # We know the length of the bytearray (c char array)
    hash_bytes = hash_pointer[:81]
    hash_unicode = hash_bytes.decode('utf-8')
    return hash_unicode

# Takes a bundle object, calculates the pow, attaches tx hash
def attach_to_tangle(bundle_trytes, # Iterable[TryteString]
                        trunk_transaction_hash, # TransactionHash
                        branch_transaction_hash, # TransactionHash
                        mwm=14):  # Int
    """
    Attaches the bundle to the Tangle by doing Proof-of-Work
    locally. No connection to the Tangle is needed in this step.

    :param bundle_trytes:
        List of TryteString(s) that contain raw transaction trytes.

    :param trunk_transaction_hash:
        Trunk transaction hash obtained from an iota node.
        Result of the tip selection process.

    :param branch_transaction_hash:
        Branch transaction hash obtained from an iota node.
        Result of the tip selection process.

    :param mwm:
        Minimum Weight Magnitude to be used during the PoW.
        Number of trailing zero trits in transaction hash.

    :returns:
        The bundle as a list of transaction trytes (TryteStrings).
        Attachment timestamp and nonce included.
    """
    previoustx = None

    # Construct bundle object
    bundle = iota.Bundle.from_tryte_strings(bundle_trytes)

    # reversed, beause pyota bundles look like [...tx2,tx1,tx0]
    # and we need the tail tx first (tx0)
    for txn in reversed(bundle.transactions):
        txn.attachment_timestamp = get_current_ms()
        txn.attachment_timestamp_upper_bound = (math.pow(3,27) - 1) // 2
        
        if (not previoustx): # this is the tail transaction
            if txn.current_index == txn.last_index:
                txn.branch_transaction_hash = branch_transaction_hash
                txn.trunk_transaction_hash = trunk_transaction_hash
            else:
                raise ValueError('Tail transaction is inconsistent in bundle')

        else: # It is not a tail transaction
            txn.branch_transaction_hash = trunk_transaction_hash
            txn.trunk_transaction_hash = previoustx # the previous transaction
        
        # Let's do the pow locally
        txn_string = txn.as_tryte_string().__str__()
        # returns a python unicode string
        powed_txn_string = get_powed_tx_trytes(txn_string, mwm)
        # construct trytestring from python string
        powed_txn_trytes = iota.TryteString(powed_txn_string)
        # compute transaction hash
        hash_string = get_hash_trytes(powed_txn_string)
        hash_trytes = iota.TryteString(hash_string)
        hash_= iota.TransactionHash(hash_trytes)

        # Create powed txn object
        powed_txn = iota.Transaction.from_tryte_string(
            trytes=powed_txn_trytes,
            hash=hash_
        )

        previoustx = powed_txn.hash
        # put that back in the bundle
        bundle.transactions[txn.current_index] = powed_txn
    return bundle.as_tryte_strings()
