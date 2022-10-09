#!/usr/bin/env python3
# Copyright (c) 2015-2018 The Bitcoin Core developers
# Copyright (c) 2019 Chaintope Inc.
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test max block size change in the blockchain.
xfield type 2 is max block size

B0 -- Genesis block -- aggpubkey1
B1 - B10 -- Generate 10 blocks with no aggpubkey -- chain becomes longer
B11 - B15-- Create block - block size 1MB - sign with aggpubkey1 -- success
B -- Create block - block size 1MB + 1, MAX_SIGOP_COUNT  -- failure - max bloxk size exceeded
B16 -- Create block with aggpubkey2 - sign with aggpubkey1 -- success - aggpubkey2 is added to list 
B -- Create block with 0 maxblock size - sign with aggpubkey2 -- failure - block serialization fails
B -- Create block with invalid maxblock size - sign with aggpubkey2 -- failure - max block size invalid
B17 -- Create block - new max block size 0.5MB - sign with aggpubkey2 -- success
B -- Create block - block size 1MB - sign with aggpubkey2 -- failure - max block size exceeded
B18 -- Create block - block size 0.5B -- success
B19 - B28 -- Generate 10 blocks - no change in aggpubkey or block size -- chain becomes longer
B29 -- Create block - new  maxblocksize 4MB - sign with aggpubkey2 -- success
B30 - B39 -- Generate 10 blocks - no change in aggpubkey or block size -- chain becomes longer
B -- Create block - block size 4MB + 1 - sign with aggpubkey2 -- failure - max block size exceeded
B40 -- Create block - block size 1MB + 1 - sign with aggpubkey2 -- success
B41 -- Create block - block size 0.5MB - sign with aggpubkey2 -- success
call invalidate block rpc on B41 -- success - B21 is removed from the blockchain. tip is B40
B41 -- Re Create a new block B41 -- success
B -- - Create block with 1 invalid transaction - sign with aggpubkey2 -- failure
B -- - Create block with 1 invalid transaction and new maxblocksize - sign with aggpubkey2 -- failure and new maxblocksize is not added to the list : verify that block with new maxblocksize is rejected
B42 -- Create block with 1 valid transaction and aggpubkey3 - sign with aggpubkey2 -- success
B43 - B47 -- Generate 5 blocks - no change in aggpubkey or block size - sign with aggpubkey3 -- chain becomes longer

Simulate Blockchain Reorg  - After the last federation block
B44 -- Create block with previous block hash = B43 - sign with aggpubkey3 -- success - block is accepted but there is no re-org
B45 -- Create block with previous block hash = B44 - sign with aggpubkey3 -- success - block is accepted but there is no re-org
B46 -- Create block with previous block hash = B45 - sign with aggpubkey3 -- success - block is accepted but there is no re-org
B47 -- Create block with previous block hash = B46 - sign with aggpubkey3 -- success - block is accepted but there is no re-org
B48 -- Create block with previous block hash = B47 - sign with aggpubkey3 -- success - block is accepted and re-org happens

Simulate Blockchain Reorg - Before the last federation block
B42 -- Create block with previous block hash = B41 - sign with aggpubkey2 -- failure - block is in invalid chain
B43 -- Create block with previous block hash = B42 - sign with aggpubkey2 -- success - block is in invalid chain
there are 3 tips in the current blockchain

B49 -- Create block - new maxblocksize 1000B - sign with aggpubkey3 -- success
call invalidate block rpc on B49 -- failure - B49 is a federation block
B50 - Create block of size 1000B - sign using aggpubkey3 -- success
B51 - Create block of size 100B - sign using aggpubkey3 -- success
B - Create block of size 10B - sign using aggpubkey3 -- failure - too small
B - Create block of size 1001B - sign using aggpubkey3 -- failure - max block size exceeded
B - Create block of size 1000B with more sigops - sign using aggpubkey3 -- failure - max sig ops exceeded

test the output of RPC Getblockchaininfo before reorg and after reorg. Verify block aggpubkey and maxblock size changes against block height

aggpubkey1 = 0
aggpubkey2 = 16
aggpubkey3 = 42

maxblocksize 1MB = 0
maxblocksize 0.5MB = 17
maxblocksize 4MB = 29
maxblocksize 1000B = 49

Restart the node with -reindex, -reindex-chainstate and -loadblock options. This triggers a full rewind of block index. Verify that the tip reaches B51 at the end.
"""
import time
import shutil, os

from test_framework.blocktools import create_block, create_coinbase, createTestGenesisBlock, create_colored_transaction, generate_blocks
from test_framework.key import CECKey
from test_framework.schnorr import Schnorr
from test_framework.mininode import P2PDataStore
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal, bytes_to_hex_str, hex_str_to_bytes, NetworkDirName
from test_framework.script import CScript, OP_CHECKSIG, OP_TRUE, SignatureHash, SIGHASH_ALL
from test_framework.messages import CTransaction, MAX_BLOCK_BASE_SIZE, CTxOut, CTxIn, COutPoint, uint256_from_str, ser_compact_size

MAX_BLOCK_SIGOPS = 20000
MAX_SCRIPT_SIZE = 10000

reverse_bytes = (lambda txid  : txid[-1: -len(txid)-1: -1])

# TestP2PConn: A peer we use to send messages to bitcoind, and store responses.
class TestP2PConn(P2PDataStore):
    def __init__(self):
        super().__init__()
        self.last_sendcmpct = []
        self.block_announced = False
        # Store the hashes of blocks we've seen announced.
        # This is for synchronizing the p2p message traffic,
        # so we can eg wait until a particular block is announced.
        self.announced_blockhashes = set()

    def on_sendcmpct(self, message):
        self.last_sendcmpct.append(message)

    def on_inv(self, message):
        for x in self.last_message["inv"].inv:
            if x.type == 2:
                self.block_announced = True
                self.announced_blockhashes.add(x.hash)

class MaxBloxkSizeInXFieldTest(BitcoinTestFramework):
    def set_test_params(self):
        self.aggpubkeys = ["025700236c2890233592fcef262f4520d22af9160e3d9705855140eb2aa06c35d3",
        "03831a69b8009833ab5b0326012eaf489bfea35a7321b1ca15b11d88131423fafc",
        "02bf2027c8455800c7626542219e6208b5fe787483689f1391d6d443ec85673ecf",]
        
        self.aggprivkey = ["67ae3f5bfb3464b9704d7bd3a134401cc80c3a172240ebfca9f1e40f51bb6d37",
        "dbb9d19637018267268dfc2cc7aec07e7217c1a2d6733e1184a0909273bf078b",
        "aa2c70c4b85a09be514292d04b27bbb0cc3f86d306d58fe87743d10a095ada07",]

        self.aggprivkey_wif = ["cR4F4fGuKjDWxiYDtGtyM77WkrVhTgokVyM2ERxoxp7R4RQP9dgE",
        "cUwpWhH9CbYwjUWzfz1UVaSjSQm9ALXWRqeFFiZKnn8cV6wqNXQA",
        "cTHVmjaAwKtU75t89fg42SLx43nRxhsri6YY1Eynvs1V1tPRCfae",]

        self.blocks = []

        self.coinbase_key = CECKey()
        self.coinbase_key.set_secretbytes(bytes.fromhex("12b004fff7f4b69ef8650e767f18f11ede158148b425660723b9f9a66e61f747"))
        self.coinbase_pubkey = self.coinbase_key.get_pubkey()

        self.schnorr_key = Schnorr()
        self.schnorr_key.set_secretbytes(bytes.fromhex("12b004fff7f4b69ef8650e767f18f11ede158148b425660723b9f9a66e61f747"))

        self.num_nodes = 1
        self.sig_scheme = 0
        self.setup_clean_chain = True
        self.mocktime = int(time.time() - 50)
        self.genesisBlock = createTestGenesisBlock(self.aggpubkeys[0], self.aggprivkey[0], int(time.time() - 100))

    def reconnect_p2p(self, node):
        node.disconnect_p2ps()
        node.add_p2p_connection(TestP2PConn())
        node.p2p.wait_for_getheaders(timeout=5)

    def run_test(self):
        node = self.nodes[0]
        self.address = node.getnewaddress()
        self.reconnect_p2p(node)

        self.log.info("Test starting...")

        #genesis block (B0)
        self.blocks = [node.getblock(self.genesisBlock.hash) ]
        self.blockhash = []
        self.block_time = int(time.time())

        # Create new blocks B1 - B10
        self.unspent = generate_blocks(11, node, self.coinbase_pubkey, self.aggprivkey[0])
        self.tip  = node.getbestblockhash()
        assert_equal(self.tip, node.getbestblockhash())

        #B11 - B15-- Create block - block size 1MB - sign with aggpubkey1 -- success
        self.block_time += 1
        blocknew = self.new_block(11, spend=self.unspent[0], coinbase_pubkey=self.coinbase_pubkey)
        blocknew.solve(self.aggprivkey[0])
        self.expand_block(blocknew, 20000)
        node.p2p.send_blocks_and_test([blocknew], node, success=True)
        self.tip = blocknew.hash
        assert_equal(self.tip, node.getbestblockhash())

        self.block_time += 1
        blocknew = self.new_block(12, spend=self.unspent[1])
        blocknew.solve(self.aggprivkey[0])
        self.expand_block(blocknew, MAX_BLOCK_BASE_SIZE)
        node.p2p.send_blocks_and_test([blocknew], node, success=True)
        self.tip = blocknew.hash
        assert_equal(self.tip, node.getbestblockhash())

        self.log.info("Reject a block of size MAX_BLOCK_BASE_SIZE + 1")
        self.block_time += 1
        blocknew = self.new_block(13, spend=self.unspent[2])
        blocknew.solve(self.aggprivkey[0])
        self.expand_block(blocknew, MAX_BLOCK_BASE_SIZE + 1)
        node.p2p.send_blocks_and_test([blocknew], node, success=False, reject_code=16, reject_reason="bad-blk-length")
        assert_equal(self.tip, node.getbestblockhash())

        self.reconnect_p2p(node)

        self.log.info("Accept a block with MAX_BLOCK_SIGOPS checksigs")
        self.block_time += 1
        blocknew = self.new_block(13, spend=self.unspent[2], script=CScript([OP_CHECKSIG] * (MAX_BLOCK_SIGOPS - 1)))
        blocknew.solve(self.aggprivkey[0])
        node.p2p.send_blocks_and_test([blocknew], node, success=True)
        self.tip = blocknew.hash
        assert_equal(self.tip, node.getbestblockhash())

        self.log.info("Reject a block with too many checksigs")
        self.block_time += 1
        blocknew = self.new_block(14, spend=self.unspent[3], script=CScript([OP_CHECKSIG] * (MAX_BLOCK_SIGOPS + 1)))
        blocknew.solve(self.aggprivkey[0])
        node.p2p.send_blocks_and_test([blocknew], node, success=False, reject_code=16, reject_reason="bad-blk-sigops")
        assert_equal(self.tip, node.getbestblockhash())

        self.reconnect_p2p(node)
        self.block_time += 1
        blocknew = self.new_block(14, spend=self.unspent[3])
        blocknew.solve(self.aggprivkey[0])
        self.expand_block(blocknew, MAX_BLOCK_BASE_SIZE)
        node.p2p.send_blocks_and_test([blocknew], node, success=True)
        self.tip = blocknew.hash
        assert_equal(self.tip, node.getbestblockhash())

        self.block_time += 1
        blocknew = self.new_block(15, spend=self.unspent[4])
        blocknew.solve(self.aggprivkey[0])
        self.expand_block(blocknew, MAX_BLOCK_BASE_SIZE)
        node.p2p.send_blocks_and_test([blocknew], node, success=True)
        self.tip = blocknew.hash
        assert_equal(self.tip, node.getbestblockhash())

        #B16 -- Create block with aggpubkey2 - sign with aggpubkey1 -- success - aggpubkey2 is added to list 
        self.log.info("Accept block which changes aggpubkey")
        self.block_time += 1
        blocknew = self.new_block(16, spend=self.unspent[5], signblockpubkey=self.aggpubkeys[1])
        blocknew.solve(self.aggprivkey[0])
        node.p2p.send_blocks_and_test([blocknew], node, success=True)
        self.tip = blocknew.hash
        assert_equal(self.tip, node.getbestblockhash())

        #B -- Create block with 0 maxblock size - sign with aggpubkey2 -- failure - block serialization fails
        self.log.info("Reject blocks with invalid max block size")
        self.block_time += 1
        blocknew = self.new_block(17, spend=self.unspent[6])
        blocknew.xfieldType = 2
        blocknew.xfield = 0
        blocknew.solve(self.aggprivkey[1])
        node.p2p.send_blocks_and_test([blocknew], node, success=False, reject_code=16, reject_reason="bad-xfieldType-xfield")
        assert_equal(self.tip, node.getbestblockhash())

        #B -- Create block with small maxblock size - sign with aggpubkey2 -- failure - max block size invalid
        self.reconnect_p2p(node)

        self.block_time += 1
        blocknew = self.new_block(17, spend=self.unspent[6])
        blocknew.xfieldType = 2
        blocknew.xfield = 100
        blocknew.solve(self.aggprivkey[1])
        node.p2p.send_blocks_and_test([blocknew], node, success=False, reject_code=16, reject_reason="bad-xfieldType-xfield")
        assert_equal(self.tip, node.getbestblockhash())

        #B -- Create block with negative maxblock size - sign with aggpubkey2 -- failure - max block size invalid
        self.reconnect_p2p(node)

        self.block_time += 1
        blocknew = self.new_block(17, spend=self.unspent[6])
        blocknew.xfieldType = 2
        blocknew.xfield = 0
        blockhex = blocknew.serialize()
        blockhex=blockhex.replace(b'\x02\x00\x00\x00\x00', b'\x02\x80\x80\x80\x80')
        blocknew.solve(self.aggprivkey[1])
        node.p2p.send_blocks_and_test([blocknew], node, success=False, reject_code=16, reject_reason="bad-xfieldType-xfield")
        assert_equal(self.tip, node.getbestblockhash())

        #B17 -- Create block - new max block size 0.5MB - sign with aggpubkey2 -- success
        self.log.info("Accept block which changes max block size to 0.5MB")
        self.reconnect_p2p(node)
        self.block_time += 1
        blocknew = self.new_block(17, spend=self.unspent[7])
        blocknew.xfieldType = 2
        blocknew.xfield = int(MAX_BLOCK_BASE_SIZE/2)
        blocknew.solve(self.aggprivkey[1])
        node.p2p.send_blocks_and_test([blocknew], node, success=True)
        self.tip = blocknew.hash
        assert_equal(self.tip, node.getbestblockhash())

        #B -- Create block - block size 1MB - sign with aggpubkey2 -- failure - max block size exceeded
        self.block_time += 1
        blocknew = self.new_block(18, spend=self.unspent[8])
        self.expand_block(blocknew, MAX_BLOCK_BASE_SIZE)
        blocknew.solve(self.aggprivkey[1])
        node.p2p.send_blocks_and_test([blocknew], node, success=False, reject_code=16, reject_reason="bad-blk-size")
        assert_equal(self.tip, node.getbestblockhash())

        #B18 -- Create block - block size 0.5B -- success
        self.reconnect_p2p(node)
        self.block_time += 1
        blocknew = self.new_block(18, spend=self.unspent[8])
        self.expand_block(blocknew, int(MAX_BLOCK_BASE_SIZE/2))
        blocknew.solve(self.aggprivkey[1])
        node.p2p.send_blocks_and_test([blocknew], node, success=True)
        self.tip = blocknew.hash
        assert_equal(self.tip, node.getbestblockhash())

        #B19 - B27 -- Generate 10 blocks - no change in aggpubkey or block size -- chain becomes longer
        self.unspent = self.unspent + generate_blocks(10, node, self.coinbase_pubkey, self.aggprivkey[1])
        self.tip  = node.getbestblockhash()
        assert_equal(self.tip, node.getbestblockhash())

        #B -- Create block - block size 3MB - sign with aggpubkey2 -- failure - max block size exceeded
        self.block_time += 1
        blocknew = self.new_block(28, spend=self.unspent[9])
        self.expand_block(blocknew, 3 * MAX_BLOCK_BASE_SIZE)
        blocknew.solve(self.aggprivkey[1])
        node.p2p.send_blocks_and_test([blocknew], node, success=False, reject_code=16, reject_reason="bad-blk-size")
        assert_equal(self.tip, node.getbestblockhash())

        #B28 -- Create block - new  maxblocksize 3MB - sign with aggpubkey2 -- success
        self.log.info("Accept block which changes max block size to 3MB")
        self.reconnect_p2p(node)
        self.block_time += 1
        blocknew = self.new_block(28, spend=self.unspent[9])
        blocknew.xfieldType = 2
        blocknew.xfield = int(3 * MAX_BLOCK_BASE_SIZE)
        blocknew.solve(self.aggprivkey[1])
        node.p2p.send_blocks_and_test([blocknew], node, success=True)
        self.tip = blocknew.hash
        assert_equal(self.tip, node.getbestblockhash())

        #B29 -- Create block - block size 3MB - sign with aggpubkey2 -- success
        self.block_time += 1
        blocknew = self.new_block(29, spend=self.unspent[10])
        self.expand_block(blocknew, 3 * MAX_BLOCK_BASE_SIZE)
        blocknew.solve(self.aggprivkey[1])
        node.p2p.send_blocks_and_test([blocknew], node, success=True)
        self.tip = blocknew.hash
        assert_equal(self.tip, node.getbestblockhash())

        #B30 - B34 -- Generate 5 blocks - no change in aggpubkey or block size -- chain becomes longer
        self.unspent = self.unspent + generate_blocks(5, node, self.coinbase_pubkey, self.aggprivkey[1])
        self.tip  = node.getbestblockhash()
        tip_after_invalidate = self.tip
        assert_equal(self.tip, node.getbestblockhash())

        #B -- Create block - block size 3MB + 1 - sign with aggpubkey2 -- failure - max block size exceeded
        self.block_time += 1
        blocknew = self.new_block(34, spend=self.unspent[11])
        self.expand_block(blocknew, (3 * MAX_BLOCK_BASE_SIZE) + 1)
        blocknew.solve(self.aggprivkey[1])
        node.p2p.send_blocks_and_test([blocknew], node, success=False, reject_code=16, reject_reason="bad-blk-size")
        assert_equal(self.tip, node.getbestblockhash())

        #B35 -- Create block - block size 1MB + 1 - sign with aggpubkey2 -- success
        self.reconnect_p2p(node)
        self.block_time += 1
        blocknew = self.new_block(34, spend=self.unspent[11])
        self.expand_block(blocknew, MAX_BLOCK_BASE_SIZE + 1)
        blocknew.solve(self.aggprivkey[1])
        node.p2p.send_blocks_and_test([blocknew], node, success=True)
        self.tip = blocknew.hash
        invalidate = blocknew.hash
        assert_equal(self.tip, node.getbestblockhash())

        #B36 -- Create block - block size 0.5MB - sign with aggpubkey2 -- success
        self.block_time += 1
        blocknew = self.new_block(35, spend=self.unspent[12])
        self.expand_block(blocknew, int(MAX_BLOCK_BASE_SIZE/2))
        blocknew.solve(self.aggprivkey[1])
        node.p2p.send_blocks_and_test([blocknew], node, success=True)
        self.tip = blocknew.hash
        invalid_tip = blocknew.hash
        assert_equal(self.tip, node.getbestblockhash())

        #call invalidate block rpc on B35 -- success - B36 is removed from the blockchain. tip is B35
        self.log.info("Test invalidate block")
        node.invalidateblock(invalidate)
        self.tip = tip_after_invalidate
        assert_equal(self.tip, node.getbestblockhash())

        #B34 -- Re Create a new block B34 -- success
        self.block_time += 1
        blocknew = self.new_block(34, spend=self.unspent[11])
        self.expand_block(blocknew, int(MAX_BLOCK_BASE_SIZE/2))
        blocknew.solve(self.aggprivkey[1])
        node.p2p.send_blocks_and_test([blocknew], node, success=True)
        self.tip = blocknew.hash
        new_valid_tip = blocknew.hash
        assert_equal(self.tip, node.getbestblockhash())

        #B36 -- Create a new block in invalid chain B36 -- Failure -- prev block invalid
        self.tip = invalid_tip
        self.block_time += 1
        blocknew = self.new_block(36, spend=self.unspent[13])
        blocknew.solve(self.aggprivkey[1])
        try:
            node.p2p.send_blocks_and_test([blocknew], node, success=False, timeout=20)
        except AssertionError:
            self.log.info("Block in invalidate chain rejected")
        self.tip = new_valid_tip
        assert_equal(self.tip, node.getbestblockhash())

        #B35 -- Re Create a new block B35 -- success
        self.reconnect_p2p(node)
        self.block_time += 1
        blocknew = self.new_block(35, spend=self.unspent[12])
        self.expand_block(blocknew, int(MAX_BLOCK_BASE_SIZE/2))
        blocknew.solve(self.aggprivkey[1])
        node.p2p.send_blocks_and_test([blocknew], node, success=True)
        self.tip = blocknew.hash
        assert_equal(self.tip, node.getbestblockhash())

        #B -- - Create block with 1 invalid transaction - sign with aggpubkey2 -- failure
        self.block_time += 1
        blocknew = self.new_block(35, spend=self.unspent[12])
        blocknew.vtx[1].vout[0].amount = 1000
        blocknew.solve(self.aggprivkey[1])
        node.p2p.send_blocks_and_test([blocknew], node, success=False)
        assert_equal(self.tip, node.getbestblockhash())

        #B -- - Create block with 1 invalid transaction and new maxblocksize - sign with aggpubkey2 -- failure and new maxblocksize is not added to the list
        self.reconnect_p2p(node)
        self.block_time += 1
        blocknew = self.new_block(35, spend=self.unspent[12])
        blocknew.vtx[1].vout[0].amount = 1000
        blocknew.xfieldType = 2
        blocknew.xfield = int(4 * MAX_BLOCK_BASE_SIZE)
        blocknew.solve(self.aggprivkey[1])
        node.p2p.send_blocks_and_test([blocknew], node, success=False)
        assert_equal(self.tip, node.getbestblockhash())

        #B36 - B39 -- Generate 5 blocks - no change in aggpubkey or block size -- chain becomes longer
        self.reconnect_p2p(node)
        self.unspent = self.unspent + generate_blocks(5, node, self.coinbase_pubkey, self.aggprivkey[1])
        self.tip  = node.getbestblockhash()

        self.log.info("Verifying getblockchaininfo")
        expectedAggPubKeys = [
            { self.aggpubkeys[0] : 0},
            { self.aggpubkeys[1] : 17}
        ]
        expectedblockheights = [
            { '500000' : 18},
            { '3000000' : 29}
        ]
        blockchaininfo = node.getblockchaininfo()
        assert_equal(blockchaininfo["aggregatePubkeys"], expectedAggPubKeys)
        assert_equal(blockchaininfo["blockSizeChanges"], expectedblockheights)

        self.log.info("Accept block which changes max block size to 3.99MB")
        #tapyrusd accepts only MAX_PROTOCOL_MESSAGE_LENGTH (4MB) messages in p2p protocol
        #create blocks with max capacity
        self.block_time += 1
        blocknew = self.new_block(40, spend=self.unspent[13])
        blocknew.xfieldType = 2
        blocknew.xfield = 3999900
        blocknew.solve(self.aggprivkey[1])
        node.p2p.send_blocks_and_test([blocknew], node, success=True)
        self.tip = blocknew.hash
        assert_equal(self.tip, node.getbestblockhash())

        self.block_time += 1
        blocknew = self.new_block(41, spend=self.unspent[14])
        self.expand_block(blocknew, 39999899)
        blocknew.solve(self.aggprivkey[1])
        node.p2p.send_blocks_and_test([blocknew], node, success=True, timeout=120)
        self.tip = blocknew.hash
        assert_equal(self.tip, node.getbestblockhash())

        self.block_time += 1
        blocknew = self.new_block(41, spend=self.unspent[15])
        self.expand_block(blocknew, 3999901)
        blocknew.solve(self.aggprivkey[1])
        node.p2p.send_blocks_and_test([blocknew], node, success=False, timeout=120)
        self.tip = blocknew.hash
        assert_equal(self.tip, node.getbestblockhash())

        self.log.info("Restarting node with '-reindex-chainstate'")
        self.stop_node(0)
        self.start_node(0, extra_args=["-reindex-chainstate"])
        self.sync_all()
        self.stop_node(0)

        self.log.info("Restarting node with '-loadblock'")
        shutil.copyfile(os.path.join(self.nodes[0].datadir, NetworkDirName(), 'blocks', 'blk00000.dat'), os.path.join(self.nodes[0].datadir, 'blk00000.dat'))
        os.remove(os.path.join(self.nodes[0].datadir, NetworkDirName(), 'blocks', 'blk00000.dat'))
        extra_args=["-loadblock=%s" % os.path.join(self.nodes[0].datadir, 'blk00000.dat'), "-reindex"]
        self.start_node(0, extra_args)


    def create_tx_with_script(self, prevtx, n, script_sig=b"", amount = 1, script_pub_key=CScript()):
        tx = CTransaction()
        tx.vin.append(CTxIn(COutPoint(prevtx, n), script_sig, 0xffffffff))
        tx.vout.append(CTxOut(amount, script_pub_key))
        tx.calc_sha256()
        return tx

    def update_block(self, block, new_transactions):
        [tx.rehash() for tx in new_transactions]
        block.vtx.extend(new_transactions)
        block.calc_sha256()
        block.hashMerkleRoot = block.calc_merkle_root()
        block.hashImMerkleRoot = block.calc_immutable_merkle_root()
        block.solve(self.signblockprivkey)
        assert(block.is_valid())
        return block

    def new_block(self, height, spend=None, script=CScript([OP_TRUE]), coinbase_pubkey= None, solve=True, signblockpubkey=""):
        bh = uint256_from_str(reverse_bytes(hex_str_to_bytes(self.tip)))
        block_time = self.block_time + 1
        # First create the coinbase
        coinbase = create_coinbase(height, coinbase_pubkey)
        coinbase.rehash()
        if spend is None:
            block = create_block(bh, coinbase, block_time, signblockpubkey)
        else:
            block = create_block(bh, coinbase, block_time, signblockpubkey)
            tx = self.create_tx_with_script(spend.malfixsha256, 0, script_pub_key=script, amount=1)
            self.sign_tx(tx, spend)
            self.update_block(block, [tx])
        if solve:
            block.solve(self.signblockprivkey)
        return block

    def expand_block(self, block, blocksize = MAX_BLOCK_BASE_SIZE):
        expand = blocksize - len(block.serialize())
        i = 1
        scr_size = len(ser_compact_size(MAX_SCRIPT_SIZE))
        while expand > MAX_SCRIPT_SIZE:
            tx = CTransaction()
            tx.vin.append(CTxIn(COutPoint(block.vtx[i].malfixsha256, 0)))
            tx.vout.append(CTxOut(1, CScript([b'\x51'])))

            script_output = CScript([b'\x6a', b'\x51' * (MAX_SCRIPT_SIZE - scr_size - 1)])
            tx.vout.append(CTxOut(0, script_output))

            spend = {}
            spend['scriptPubKey'] = bytes_to_hex_str(block.vtx[i].vout[0].scriptPubKey)
            expand = expand - len(tx.serialize())
            block = self.update_block(block, [tx])
            i = i + 1

        if expand > 0:
            tx = CTransaction()
            tx.vin.append(CTxIn(COutPoint(block.vtx[i].malfixsha256, 0)))
            tx.vout.append(CTxOut(1, CScript([b'\x51'])))
            script_output = CScript([b'\x6a'])
            tx.vout.append(CTxOut(0, script_output))

            spend = {}
            spend['scriptPubKey'] = bytes_to_hex_str(block.vtx[i].vout[0].scriptPubKey)
            expand = expand - len(tx.serialize()) - len(ser_compact_size(expand))
            if len(block.serialize()) < 1048576:
                expand = expand - 2
            elif len(block.serialize()) < 16777216:
                expand = expand - 4
            script_output = CScript([b'\x6a', b'\x51'* expand])
            tx.vout[1].scriptPubKey = script_output
            block = self.update_block(block, [tx])
        assert_equal(len(block.serialize()), blocksize)
        return block

    def sign_tx(self, tx, spend):
        scriptPubKey = CScript(spend.vout[0].scriptPubKey)
        if (scriptPubKey[0] == OP_TRUE):  # an anyone-can-spend
            tx.vin[0].scriptSig = CScript()
            return
        (sighash, err) = SignatureHash(scriptPubKey, tx, 0, SIGHASH_ALL)
        if self.sig_scheme == 1:
            tx.vin[0].scriptSig = CScript([self.coinbase_key.sign(sighash) + bytes(bytearray([SIGHASH_ALL]))])
            self.sig_scheme = 0
        else:
            tx.vin[0].scriptSig = CScript([self.schnorr_key.sign(sighash) + bytes(bytearray([SIGHASH_ALL]))])
            self.sig_scheme = 1

if __name__ == '__main__':
    MaxBloxkSizeInXFieldTest().main()
