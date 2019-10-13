ccurl.interface.py
==================

A python interface to load `Ccurl
library <https://github.com/iotaledger/ccurl>`__ and perform proof of
work locally, without relying on a node. To be used together with
`PyOTA <https://github.com/iotaledger/iota.py>`__, the Python Client
Library for IOTA. For more info, `read the
docs <https://pyota.readthedocs.io/en/latest/>`__.

Motivation
----------

Currently, PyOTA doesn't support performing proof of work locally. The
``attach_to_tangle`` API command sends the prepared transaction trytes
to an IOTA node, that does the PoW by filling out
``attachment_timestamp*`` fields and calculating ``nonce`` with Curl
P-81. In case of bundles, transactions are chained together through
their ``transaction hash``.

Installation
------------

To use the module, follow the steps: - Clone the repo from GitHub:

``$ git clone https://github.com/lzpap/ccurl.interface.py.git``

-  Make sure you have `cmake <https://cmake.org/>`__ availabke on your
   system. This is a build dependecy for the ccurl library.
-  Build ccurl according to `build
   instructions <https://github.com/iotaledger/ccurl/blob/master/README.md>`__
   and put the ``.so`` library into the ``src`` folder, or run the
   ``init`` script in the main folder to build and initialize:

``$ ./init.sh``

-  Create a vitual environment / activate the one you use for PyOTA.
-  Install th python package from source by running:

``$ pip install -e .``

How to use?
-----------

Once installed, you can use the module to replace ``attach_to_tangle``
core api call in PyOTA. Just import the ``ccurl_interface`` module from
the ``pow`` package and you are good to go.

An example code below illustrates how to do PoW for a bundle consisting
of two transactions.

Code Example
------------

::

    import iota
    from pprint import *
    from pow import ccurl_interface

    # Generate seed
    myseed = iota.crypto.types.Seed.random()

    #Generate two addresses
    addres_generator = iota.crypto.addresses.AddressGenerator(myseed)
    addys = addres_generator.get_addresses(1, count=2)

    # preparing transactions
    pt = iota.ProposedTransaction(address = iota.Address(addys[0]),
                                  tag     = iota.Tag(b'LOCALATTACHINTERFACE99999'),
                                  value   = 0)

    pt2 = iota.ProposedTransaction(address = iota.Address(addys[1]),
                                   tag     = iota.Tag(b'LOCALATTACHINTERFACE99999'),
                                   value   = 0)

    # preparing bundle that consists of both transactions prepared in the previous example
    pb = iota.ProposedBundle(transactions=[pt2,pt])

    # generate bundle hash
    pb.finalize()

    # declare a api instance
    api = iota.Iota("https://nodes.thetangle.org:443") # selecting IOTA node

    # get tips to be approved by your bundle
    gta = api.get_transactions_to_approve(depth=3)

    minimum_weight_magnitude = 14 # target is mainnet

    # perform PoW locally
    bundle_trytes =\
        ccurl_interface.attach_to_tangle(
            pb.as_tryte_strings(),
            gta['trunkTransaction'],
            gta['branchTransaction'],
            mwm
        )
    
    # Broadcast transactions on the Tangle
    broadcasted = api.broadcast_and_store(bundle_trytes)

    bundle_broadcasted =iota.Bundle.from_tryte_strings(broadcasted['trytes'])

    pprint('Local pow broadcasted transactions are:')
    pprint(bundle_broadcasted.as_json_compatible())

Tests
-----

Run ``nosetests`` to test in current environment.
Run ``tox -v -p all`` to test in Python 2.7, 3.5, 3.6 and 3.8.

Contribute
----------

Raise issues:
https://github.com/lzpap/ccurl.interface.py/issues
