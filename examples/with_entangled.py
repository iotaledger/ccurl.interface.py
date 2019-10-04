import iota
from pprint import *
from datetime import datetime
from pow import entangled_interface

# Generate seed
myseed = iota.crypto.types.Seed.random()
pprint('Generated seed is:')
pprint(myseed)

#Generate two addresses
addres_generator = iota.crypto.addresses.AddressGenerator(myseed)
addys = addres_generator.get_addresses(1, count=2)
pprint('Generated addresses are:')
pprint(addys)

NowIs = datetime.now() # get a actual date & time - just to have some meaningfull info

# preparing transactions
pt = iota.ProposedTransaction(address = iota.Address(addys[0]), # 81 trytes long address
                              message = iota.TryteString.from_unicode('Hey hey, trying to figure this thing out. This is tx1, now is %s' % (NowIs)),
                              tag     = iota.Tag(b'LOCALATTACHINTERFACE99999'), # Up to 27 trytes
                              value   = 0)

pt2 = iota.ProposedTransaction(address = iota.Address(addys[1]), # 81 trytes long address
                               message = iota.TryteString.from_unicode('Hey hey, trying to figure this thing out. This is tx2, now is %s' % (NowIs)),
                               tag     = iota.Tag(b'LOCALATTACHINTERFACE99999'), # Up to 27 trytes
                               value   = 0)
# besides the given attributes, library also adds a transaction timestamp

# preparing bundle that consists of both transactions prepared in the previous example
pb = iota.ProposedBundle(transactions=[pt2,pt]) # list of prepared transactions is needed at least

# generate bundle hash using sponge/absorb function + normalize bundle hash + copy bundle hash into each transaction / bundle is finalized
pb.finalize()

#bundle is finalized, let's print it
print("\nGenerated bundle hash: %s" % (pb.hash))
print("\nTail Transaction in the Bundle is a transaction #%s." % (pb.tail_transaction.current_index))
        
api = iota.Iota("https://nodes.thetangle.org:443") # selecting IOTA node

gta = api.get_transactions_to_approve(depth=3) # get tips to be approved by your bundle

mwm = 14 # target is mainnet

bundle = entangled_interface.local_attach_to_tangle(pb, gta['branchTransaction'],gta['trunkTransaction'],  mwm)

bundle_trytes = [ x.as_tryte_string() for x in pb._transactions ]

# Broadcast transactions on the Tangle
broadcasted = api.broadcast_and_store(bundle_trytes)

bundle_broadcasted =iota.Bundle.from_tryte_strings(broadcasted['trytes'])
pprint('Local pow broadcasted transactions are:')
pprint(bundle_broadcasted.as_json_compatible())
