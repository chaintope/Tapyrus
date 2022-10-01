#!/usr/bin/env python3
# Copyright (c) 2017-2018 The Bitcoin Core developers
# Copyright (c) 2019 Chaintope Inc.
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test various command line arguments and configuration file parameters."""

import os

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import NetworkDirName

class ConfArgsTest(BitcoinTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 1

    def test_config_file_parser(self):
        # Assume node is stopped

        inc_conf_file_path = os.path.join(self.nodes[0].datadir, 'include.conf')
        with open(os.path.join(self.nodes[0].datadir, 'tapyrus.conf'), 'a', encoding='utf-8') as conf:
            conf.write('includeconf={}\n'.format(inc_conf_file_path))

        with open(inc_conf_file_path, 'w', encoding='utf-8') as conf:
            conf.write('-dash=1\n')
        self.nodes[0].assert_start_raises_init_error(expected_msg='Error reading configuration file: parse error on line 1: -dash=1, options in configuration file must be specified without leading -')

        with open(inc_conf_file_path, 'w', encoding='utf-8') as conf:
            conf.write('nono\n')
        self.nodes[0].assert_start_raises_init_error(expected_msg='Error reading configuration file: parse error on line 1: nono, if you intended to specify a negated option, use nono=1 instead')

        with open(inc_conf_file_path, 'w', encoding='utf-8') as conf:
            conf.write('')  # clear

    def run_test(self):
        self.stop_node(0)

        self.test_config_file_parser()

        self.log.info("unsupported options(removed in tapyrus only)")
        self.nodes[0].assert_start_raises_init_error(['-enablebip61=0'], 'Error parsing command line arguments: Invalid parameter -enablebip61')
        self.nodes[0].assert_start_raises_init_error(['-permitbaremultisig=0'], 'Error parsing command line arguments: Invalid parameter -permitbaremultisig')
        self.nodes[0].assert_start_raises_init_error(['-rpcserialversion'], 'Error parsing command line arguments: Invalid parameter -rpcserialversion')

        self.log.info("-dnsseeder and -dnsseed tests")
        # -dnsseeder and -dnsseed tests
        self.start_node(0, ['-addseeder=seed.tapyrus.dev.chaintope.com','-addseeder=static-seed.tapyrus.dev.chaintope.com'])
        self.stop_node(0)

        self.nodes[0].assert_start_raises_init_error(['-addseeder=seed.tapyrus.dev.chaintope.com','-addseeder=static-seed.tapyrus.dev.chaintope.com',  '-dnsseed=0'], 'Error: DNS seeding is disabled. But DNS seeders are configured in -addseeder.')

        self.start_node(0, ['-addseeder=seed.tapyrus.dev.chaintope.com','-addseeder=static-seed.tapyrus.dev.chaintope.com', '-dnsseed=1'])
        self.stop_node(0)

        self.log.info("-networkid tests")
        conf_file = os.path.join(self.nodes[0].datadir, "tapyrus.conf")

        #backup config file
        conf_file_contents = open(conf_file, encoding='utf8').read()

        # conf file with -networkid = 4
        with open(conf_file, 'w', encoding='utf8') as f:
            f.write("networkid=4\n")
            f.write("rpcuser=rpcuser\n")
            f.write("rpcpassword=pass\n")
            f.write(conf_file_contents)

        self.writeGenesisBlockToFile(self.nodes[0].datadir, networkid=4)
        self.start_node(0, ['-datadir=%s' % self.nodes[0].datadir])
        assert os.path.exists(os.path.join(self.nodes[0].datadir, "dev-4", "blocks"))
        self.stop_node(0)

        # -networkid = 10 cmd line parameter
        #os.mkdir(os.path.join(self.nodes[0].datadir,"dev-10"))
        self.writeGenesisBlockToFile(self.nodes[0].datadir, networkid=10)
        self.start_node(0, ['-networkid=10', '-datadir=%s' % self.nodes[0].datadir])
        assert os.path.exists(os.path.join(self.nodes[0].datadir, "dev-10", "blocks"))
        self.stop_node(0)

        #restore config file
        with open(conf_file, 'w', encoding='utf8') as f:
            f.write(conf_file_contents)

        self.log.info("-datadir tests")
        # Remove the -datadir argument so it doesn't override the config file
        self.nodes[0].args = [arg for arg in self.nodes[0].args if not arg.startswith("-datadir")]

        self.writeGenesisBlockToFile(self.nodes[0].datadir)
        default_data_dir = self.nodes[0].datadir
        new_data_dir = os.path.join(default_data_dir, 'newdatadir')
        new_data_dir_2 = os.path.join(default_data_dir, 'newdatadir2')

        # Check that using -datadir argument on non-existent directory fails
        self.nodes[0].datadir = new_data_dir
        self.nodes[0].assert_start_raises_init_error(['-datadir=' + new_data_dir], 'Error: Specified data directory "' + new_data_dir + '" does not exist.')

        # datadir needs to be set before [regtest] section
        with open(conf_file, 'w', encoding='utf8') as f:
            f.write("datadir=" + new_data_dir + "\n")
            f.write(conf_file_contents)

        # Temporarily disabled, because this test would access the user's home dir (~/.bitcoin)
        #self.nodes[0].assert_start_raises_init_error(['-conf=' + conf_file], 'Error reading configuration file: specified data directory "' + new_data_dir + '" does not exist.')

        # Create the directory and ensure the config file now works
        os.mkdir(new_data_dir)
        # Temporarily disabled, because this test would access the user's home dir (~/.bitcoin)
        #self.start_node(0, ['-conf='+conf_file, '-wallet=w1'])
        #self.stop_node(0)
        #assert os.path.exists(os.path.join(new_data_dir, 'regtest', 'wallets', 'w1'))

        # Ensure command line argument overrides datadir in conf
        os.mkdir(new_data_dir_2)
        self.writeGenesisBlockToFile(new_data_dir_2)
        self.nodes[0].datadir = new_data_dir_2
        self.start_node(0, ['-datadir='+new_data_dir_2, '-conf='+conf_file, '-wallet=w2'])
        assert os.path.exists(os.path.join(new_data_dir_2, NetworkDirName(), 'wallets', 'w2'))
        self.stop_node(0)

if __name__ == '__main__':
    ConfArgsTest().main()
