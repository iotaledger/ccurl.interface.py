from __future__ import absolute_import, division, print_function, \
    unicode_literals

from ctypes import *
from iota import Bundle, TransactionTrytes, TransactionHash, TryteString, \
    Transaction
import math
import time
from iota.exceptions import with_context
import logging
from sys import stderr

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

# Create a logger
logger = logging.getLogger(__name__)
logging.basicConfig(stream=stderr, level=logging.INFO)

def check_tx_trytes_length(trytes):
    """
    Checks if trytes are exactly one transaction in length.
    """
    if len(trytes) != TransactionTrytes.LEN:
        raise with_context(
            exc=ValueError('Trytes must be {len} trytes long.'.format(
                len= TransactionTrytes.LEN
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
    library to calculate `transaction hash`. Returns the
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
    bundle = Bundle.from_tryte_strings(bundle_trytes)

    # Used for checking hash
    trailing_zeros = [0] * mwm

    # reversed, beause pyota bundles look like [tx0,tx1,...]
    # and we need the head (last) tx first
    for txn in reversed(bundle.transactions):
        # Ccurl lib sometimes needs a kick to return the correct powed trytes.
        # We can check the correctness by examining trailing zeros of the
        # transaction hash. If that fails, we try calculating the pow again.
        # Use `max_iter` to prevent infinite loop. Calculation error appears
        # rarely, and usually the second try yields correct result. If we reach
        # `max_iter`, we raise a ValueError.
        max_iter = 5
        i = 0

        # If calculation is successful, we break out from the while loop.
        while i != max_iter:
            # Fill timestamps
            txn.attachment_timestamp = get_current_ms()
            txn.attachment_timestamp_upper_bound = (math.pow(3,27) - 1) // 2

            # Determine correct trunk and branch transaction
            if (not previoustx): # this is the head transaction
                if txn.current_index == txn.last_index:
                    txn.branch_transaction_hash = branch_transaction_hash
                    txn.trunk_transaction_hash = trunk_transaction_hash
                else:
                    raise ValueError('Head transaction is inconsistent in bundle')

            else: # It is not the head transaction
                txn.branch_transaction_hash = trunk_transaction_hash
                txn.trunk_transaction_hash = previoustx # the previous transaction

            # Let's do the pow locally
            txn_string = txn.as_tryte_string().__str__()
            # returns a python unicode string
            powed_txn_string = get_powed_tx_trytes(txn_string, mwm)
            # construct trytestring from python string
            powed_txn_trytes = TryteString(powed_txn_string)

            # Create powed txn object
            # This method calculates the hash for the transaction
            powed_txn = Transaction.from_tryte_string(
                trytes=powed_txn_trytes
            )
            previoustx = powed_txn.hash
            # put that back in the bundle
            bundle.transactions[txn.current_index] = powed_txn

            # Check for inconsistency in hash
            hash_trits = powed_txn.hash.as_trits()
            if hash_trits[-mwm:] == trailing_zeros:
                # We are good to go, exit from while loop
                break
            else:
                i = i + 1
                logger.info('Ooops, wrong hash detected in try'
                    ' #{rounds}. Recalculating pow... '.format(rounds= i))

        # Something really bad happened
        if i == max_iter:
            raise with_context(
                exc=ValueError('PoW calculation failed for {max_iter} times.'
                    ' Make sure that the transaction is valid: {tx}'.format(
                    max_iter=max_iter,
                    tx=powed_txn.as_json_compatible()
                    )
                ),
                context={
                    'original': txn,
                },
            )

    return bundle.as_tryte_strings()
