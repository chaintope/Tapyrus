#!/usr/bin/env python3
# Copyright (c) 2016-2018 The Bitcoin Core developers
# Copyright (c) 2019 Chaintope Inc.
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test label RPCs.

RPCs tested are:
    - getaddressesbylabel
    - listaddressgroupings
    - setlabel

"""
from time import sleep
import math
from decimal import Decimal
from collections import defaultdict
from test_framework.blocktools import create_colored_transaction

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal, assert_raises_rpc_error, assert_array_result

class WalletLabelsTest(BitcoinTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 1

    def setup_network(self):
        """Don't connect nodes."""
        self.setup_nodes()

    def run_test(self):
        """Run the test using the labels API."""
        node = self.nodes[0]

        # Check that there's no UTXO on any of the nodes
        assert_equal(len(node.listunspent()), 0)

        # Note each time we call generate, all generated coins go into
        # the same address, so we call twice to get two addresses w/50 each
        node.generate(1, self.signblockprivkey_wif)
        node.generate(1, self.signblockprivkey_wif)
        assert_equal(node.getbalance(), 100)
        assert_equal(len(node.listunspent()), 2)

        # there should be 2 address groups
        # each with 1 address with a balance of 50 TPC
        address_groups = node.listaddressgroupings()
        assert_equal(len(address_groups), 2)
        # the addresses aren't linked now, but will be after we send to the
        # common address
        linked_addresses = set()
        for address_group in address_groups:
            assert_equal(len(address_group), 1)
            assert_equal(len(address_group[0]), 2)
            assert_equal(address_group[0][1], 50)
            linked_addresses.add(address_group[0][0])

        # send 50 from each address to a third address not in this wallet
        # There's some fee that will come back to us when the miner reward
        # matures.
        common_address = "msf4WtN1YQKXvNtvdFYt9JBnUD2FB41kjr"
        txid = node.sendmany(
            amounts={common_address: 100},
            subtractfeefrom=[common_address]
        )
        tx_details = node.gettransaction(txid)
        fee = -tx_details['details'][0]['fee']
        # there should be 1 address group, with the previously
        # unlinked addresses now linked (they both have 0 balance)
        address_groups = node.listaddressgroupings()
        assert_equal(len(address_groups), 1)
        assert_equal(len(address_groups[0]), 2)
        assert_equal(set([a[0] for a in address_groups[0]]), linked_addresses)
        assert_equal([a[1] for a in address_groups[0]], [0, 0])

        node.generate(1, self.signblockprivkey_wif)

        amount_to_send = 1.0

        self.log.debug("Checking lables with TPC")
        # Create labels and make sure subsequent label API calls
        # recognize the label/address associations.
        labels = [Label(name) for name in ("a", "b", "c", "d", "e")]
        for label in labels:
            address = node.getnewaddress(label.name)
            label.add_address(address)
            label.verify(node)

        # Check all labels are returned by listlabels.
        assert_equal(node.listlabels(), [label.name for label in labels])

        # Send a transaction to each label, and make sure this forces
        # getaccountaddress to generate a new receiving address.
        for label in labels:
            node.sendtoaddress(label.addresses[0], amount_to_send)
            label.verify(node)

        # Check the amounts received.
        node.generate(1, self.signblockprivkey_wif)
        for label in labels:
            assert_equal(
                node.getreceivedbyaddress(label.addresses[0]), amount_to_send)
            assert_equal(node.getreceivedbylabel(label.name), {'TPC': Decimal('1.00000000')})

        self.log.debug("Checking lables with tokens")
        colorId = create_colored_transaction(1, 10, node)['color']
        for label in labels:
            address = node.getnewaddress(label.name, colorId)
            label.add_coloraddress(address)
            #add sleep to avoid race conditin in getaddressinfo that causes lable to be seen as ''
            sleep(1)
            label.verify(node, colorId)

        # Send a transaction to each label, and make sure this forces
        # getaccountaddress to generate a new receiving address.
        for label in labels:
            node.sendtoaddress(label.caddresses[0], 1)
            label.verify(node, colorId)

        # Check the amounts received.
        node.generate(1, self.signblockprivkey_wif)
        for label in labels:
            assert_equal(
                node.getreceivedbyaddress(label.caddresses[0]), 1)
            assert_equal(node.getreceivedbylabel(label.name), {'TPC': Decimal('1.00000000'), colorId : 1})


        self.log.debug("Check that sendfrom label reduces listaccounts balances in TPC")
        for i, label in enumerate(labels):
            to_label = labels[(i + 1) % len(labels)]
            node.sendtoaddress(to_label.addresses[0], amount_to_send)
        node.generate(1, self.signblockprivkey_wif)
        for label in labels:
            address = node.getnewaddress(label.name)
            label.add_address(address)
            label.verify(node)
            assert_equal(node.getreceivedbylabel(label.name), {'TPC': Decimal('2.00000000'), colorId: 1})
            label.verify(node)
        node.generate(3, self.signblockprivkey_wif)
        expected_account_balances = {"": 300}
        for label in labels:
            expected_account_balances[label.name] = 0
        assert_equal(math.floor(node.getbalance()), 350)

        self.log.debug("Check that sendfrom label reduces listaccounts balances in tokens")
        for i, label in enumerate(labels):
            to_label = labels[(i + 1) % len(labels)]
            node.sendtoaddress(to_label.caddresses[0], 1)
        node.generate(1, self.signblockprivkey_wif)
        for label in labels:
            address = node.getnewaddress(label.name, colorId)
            label.add_coloraddress(address)
            label.verify(node, colorId)
            assert_equal(node.getreceivedbylabel(label.name), {'TPC': Decimal('2.0000000'), colorId : 2})
            label.verify(node, colorId)
        node.generate(3, self.signblockprivkey_wif)
        expected_account_balances = {"": 400}
        for label in labels:
            expected_account_balances[label.name] = 0
        assert_equal(math.floor(node.getbalance()), 550)

        # Check that setlabel can assign a label to a new unused address.
        for label in labels:
            address = node.getnewaddress()
            node.setlabel(address, label.name)
            label.add_address(address)
            label.verify(node)
            #colored coin issue txs are without labels.
            assert_equal(len(node.getaddressesbylabel("")), 2)

        # Check that addmultisigaddress can assign labels.
        for label in labels:
            addresses = []
            for x in range(10):
                addresses.append(node.getnewaddress())
            multisig_address = node.addmultisigaddress(5, addresses, label.name)['address']
            label.add_address(multisig_address)
            label.purpose[multisig_address] = "send"
            label.verify(node)

        node.generate(1, self.signblockprivkey_wif)

        # Check that setlabel can change the label of an address from a
        # different label.
        change_label(node, labels[0].addresses[0], labels[0], labels[1])

        # Check that setlabel can set the label of an address already
        # in the label. This is a no-op.
        change_label(node, labels[2].addresses[0], labels[2], labels[2])

class Label:
    def __init__(self, name):
        # Label name
        self.name = name
        # Current receiving address associated with this label.
        self.receive_address = None
        # List of all addresses assigned with this label
        self.addresses = []
        # List of all colored addresses assigned with this label
        self.caddresses = []
        # Map of address to address purpose
        self.purpose = defaultdict(lambda: "receive")

    def add_coloraddress(self, address):
        assert_equal(address not in self.caddresses, True)
        self.caddresses.append(address)

    def add_address(self, address):
        assert_equal(address not in self.addresses, True)
        self.addresses.append(address)

    def verify(self, node, colorid=None):
        address_to_use = []
        if colorid != None:
            address_to_use = self.addresses
        else:
            address_to_use = self.caddresses

        for address in address_to_use:
            assert_equal(
                node.getaddressinfo(address)['labels'][0],
                {"name": self.name,
                 "purpose": self.purpose[address]})
            assert_equal(node.getaddressinfo(address)['label'], self.name)

        assert((node.getaddressesbylabel(self.name)[address] ==  {"purpose": self.purpose[address]}) for address in address_to_use)


def change_label(node, address, old_label, new_label):
    assert_equal(address in old_label.addresses, True)
    node.setlabel(address, new_label.name)

    old_label.addresses.remove(address)
    new_label.add_address(address)

    old_label.verify(node)
    new_label.verify(node)


if __name__ == '__main__':
    WalletLabelsTest().main()
