// Copyright (c) 2018-2020 Chaintope Inc.
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <chainparams.h>
#include <crypto/sha256.h>
#include <validation.h>
#include <script/sigcache.h>
#include <test/test_tapyrus.h>
#include <test/test_keys_helper.h>

#include <boost/test/unit_test.hpp>
#include <consensus/validation.h>

extern void noui_connect();

struct ChainParamsTestingSetup {

    ECCVerifyHandle globalVerifyHandle;

    explicit ChainParamsTestingSetup(const std::string& chainName= TAPYRUS_MODES::PROD)
        : m_path_root(fs::temp_directory_path() / "test_tapyrus" / strprintf("%lu_%i", (unsigned long)GetTime(), (int)(InsecureRandRange(1 << 30))))
    {
        SHA256AutoDetect();
        RandomInit();
        ECC_Start();
        SetupEnvironment();
        SetupNetworking();
        InitSignatureCache();
        InitScriptExecutionCache();
        fCheckBlockIndex = true;
        SetDataDir("tempdir");
        writeTestGenesisBlockToFile(GetDataDir());
        noui_connect();
    }

    ~ChainParamsTestingSetup()
    {
        ClearDatadirCache();
        gArgs.ClearOverrideArgs();
        fs::remove_all(m_path_root);
        ECC_Stop();
    }

    fs::path SetDataDir(const std::string& name)
    {
        fs::path ret = m_path_root / name;
        fs::create_directories(ret);
        gArgs.ForceSetArg("-datadir", ret.string());
        return ret;
    }

    fs::path GetDataDir()
    {
        return gArgs.GetArg("-datadir", "");
    }
private:
    const fs::path m_path_root;
};

BOOST_FIXTURE_TEST_SUITE(chainparams_tests, ChainParamsTestingSetup)

BOOST_AUTO_TEST_CASE(default_params_prod)
{
    //prod net
    BOOST_CHECK_NO_THROW(SelectParams(TAPYRUS_OP_MODE::PROD));
    
    BOOST_CHECK(Params().GetRPCPort() == 2377);
    BOOST_CHECK(Params().GetDefaultPort() == 2357);
}

BOOST_AUTO_TEST_CASE(default_params_dev)
{
    //dev
    gArgs.ForceSetArg("-dev", "1");
    BOOST_CHECK_NO_THROW(SelectParams(TAPYRUS_OP_MODE::DEV));

    BOOST_CHECK(Params().GetRPCPort() == 12381);
    BOOST_CHECK(Params().GetDefaultPort() == 12383);
}

BOOST_AUTO_TEST_CASE(unknown_mode_test)
{
    BOOST_CHECK_EXCEPTION(SelectParams((TAPYRUS_OP_MODE)5), std::runtime_error, [] (const std::runtime_error& ex) {
        BOOST_CHECK_EQUAL(ex.what(), "CreateChainParams: Unknown mode.");
        return true;
    });
}

BOOST_AUTO_TEST_CASE(custom_networkid_prod)
{
    //prod net
    gArgs.ForceSetArg("-networkid", "2");
    BOOST_CHECK_NO_THROW(SelectParams(TAPYRUS_OP_MODE::PROD));
    
    BOOST_CHECK(Params().GetRPCPort() == 2377);
    BOOST_CHECK(Params().GetDefaultPort() == 2357);
}

BOOST_AUTO_TEST_CASE(custom_networkid_dev)
{
    //dev
    gArgs.ForceSetArg("-dev", "1");
    gArgs.ForceSetArg("-networkid", "1939510133");
    BOOST_CHECK_NO_THROW(SelectParams(TAPYRUS_OP_MODE::DEV));

    BOOST_CHECK(Params().GetRPCPort() == 12381);
    BOOST_CHECK(Params().GetDefaultPort() == 12383);
}

BOOST_AUTO_TEST_CASE(default_base_params_tests)
{
    //prod net
    gArgs.ForceSetArg("-networkid", "1");
    writeTestGenesisBlockToFile(GetDataDir(), "genesis.1");
    BOOST_CHECK_NO_THROW(SelectParams(TAPYRUS_OP_MODE::PROD));
    BOOST_CHECK_NO_THROW(SelectFederationParams(TAPYRUS_OP_MODE::PROD));
    BOOST_CHECK(FederationParams().NetworkIDString() == "1");
    BOOST_CHECK(FederationParams().getDataDir() == "prod-1");

    CMessageHeader::MessageStartChars pchMessageStart = {0x01, 0xFF, 0xF0, 0x00};
    BOOST_CHECK(memcmp( FederationParams().MessageStart(), pchMessageStart, sizeof(pchMessageStart)) == 0);

    //dev
    gArgs.ForceSetArg("-dev", "1");
    gArgs.ForceSetArg("-networkid", "1905960821");
    writeTestGenesisBlockToFile(GetDataDir(), "genesis.1905960821");
    BOOST_CHECK_NO_THROW(SelectParams(TAPYRUS_OP_MODE::DEV));
    BOOST_CHECK_NO_THROW(SelectFederationParams(TAPYRUS_OP_MODE::DEV));
    BOOST_CHECK(FederationParams().NetworkIDString() == "1905960821");
    BOOST_CHECK(FederationParams().getDataDir() == "dev-1905960821");

    CMessageHeader::MessageStartChars pchMessageStart1 = {0x73, 0x9A, 0x97, 0x74};
    BOOST_CHECK(memcmp(FederationParams().MessageStart(), pchMessageStart1, sizeof(pchMessageStart1)) == 0);
}

BOOST_AUTO_TEST_CASE(custom_networkId_test)
{
    gArgs.ForceSetArg("-networkid", "2");
    writeTestGenesisBlockToFile(GetDataDir(), "genesis.2");

    BOOST_CHECK_NO_THROW(SelectParams(TAPYRUS_OP_MODE::PROD));
    BOOST_CHECK_NO_THROW(SelectFederationParams(TAPYRUS_OP_MODE::PROD));
    BOOST_CHECK(FederationParams().NetworkIDString() == "2");
    BOOST_CHECK(FederationParams().getDataDir() == "prod-2");
    
    CMessageHeader::MessageStartChars pchMessageStart = {0x01, 0xFF, 0xF0, 0x01};
    BOOST_CHECK(memcmp(FederationParams().MessageStart(), pchMessageStart, sizeof(pchMessageStart)) == 0);

    gArgs.ForceSetArg("-dev", "1");
    gArgs.ForceSetArg("-networkid", "1939510133");
    writeTestGenesisBlockToFile(GetDataDir(), "genesis.1939510133");

    BOOST_CHECK_NO_THROW(SelectParams(TAPYRUS_OP_MODE::DEV));
    BOOST_CHECK_NO_THROW(SelectFederationParams(TAPYRUS_OP_MODE::DEV));
    BOOST_CHECK(FederationParams().NetworkIDString() == "1939510133");
    BOOST_CHECK(FederationParams().getDataDir() == "dev-1939510133");
    
    CMessageHeader::MessageStartChars pchMessageStart1 = {0x75, 0x9A, 0x83, 0x74};
    BOOST_CHECK(memcmp(FederationParams().MessageStart(), pchMessageStart1, sizeof(pchMessageStart1)) == 0);
}

BOOST_AUTO_TEST_CASE(custom_networkId_range_test)
{
    //netowrk id 1 - 1 (0x00000001)
    gArgs.ForceSetArg("-networkid", "1");
    writeTestGenesisBlockToFile(GetDataDir(), "genesis.1");
    BOOST_CHECK_NO_THROW(CreateFederationParams(TAPYRUS_OP_MODE::PROD, true));

    BOOST_CHECK_NO_THROW(SelectParams(TAPYRUS_OP_MODE::PROD));
    BOOST_CHECK_NO_THROW(SelectFederationParams(TAPYRUS_OP_MODE::PROD));
    BOOST_CHECK(FederationParams().NetworkIDString() == "1");
    BOOST_CHECK(FederationParams().getDataDir() == "prod-1");

    //netowrk id of 4 bytes - 4294967295 (0xFFFFFFFF)
    gArgs.ForceSetArg("-networkid", "4294967295");
    writeTestGenesisBlockToFile(GetDataDir(), "genesis.4294967295");
    BOOST_CHECK_NO_THROW(CreateFederationParams(TAPYRUS_OP_MODE::PROD, true));

    BOOST_CHECK_NO_THROW(SelectParams(TAPYRUS_OP_MODE::PROD));
    BOOST_CHECK_NO_THROW(SelectFederationParams(TAPYRUS_OP_MODE::PROD));
    BOOST_CHECK(FederationParams().NetworkIDString() == "4294967295");
    BOOST_CHECK(FederationParams().getDataDir() == "prod-4294967295");

    //netowrk id 0 - (0x0)
    gArgs.ForceSetArg("-networkid", "0");
    writeTestGenesisBlockToFile(GetDataDir(), "genesis.0");
    BOOST_CHECK_THROW(CreateFederationParams(TAPYRUS_OP_MODE::PROD, true), std::runtime_error);//("Network Id [0] was out of range. Expected range is 1 to 4294967295."));

     //netowrk id of 4 bytes + 1 - 4294967296 (0x100000000)
    gArgs.ForceSetArg("-networkid", "4294967296");
    writeTestGenesisBlockToFile(GetDataDir(), "genesis.4294967296");
    BOOST_CHECK_THROW(CreateFederationParams(TAPYRUS_OP_MODE::PROD, true), std::runtime_error);//("Network Id [4294967296] was out of range. Expected range is 1 to 4294967295."));

     //netowrk id of 8 bytes - 18446744073709551615 (0xFFFFFFFF FFFFFFFF)
    gArgs.ForceSetArg("-networkid", "18446744073709551615");
    writeTestGenesisBlockToFile(GetDataDir(), "genesis.18446744073709551615");
    BOOST_CHECK_THROW(CreateFederationParams(TAPYRUS_OP_MODE::PROD, true), std::runtime_error);//("Network Id [18446744073709551615] was out of range. Expected range is 1 to 4294967295."));

    //netowrk id -1
    gArgs.ForceSetArg("-networkid", "-1");
    writeTestGenesisBlockToFile(GetDataDir(), "genesis.-1");
    BOOST_CHECK_THROW(CreateFederationParams(TAPYRUS_OP_MODE::PROD, true), std::runtime_error);

    //netowrk id -4294967295
    gArgs.ForceSetArg("-networkid", "-4294967295");
    writeTestGenesisBlockToFile(GetDataDir(), "genesis.-4294967295");
    BOOST_CHECK_THROW(CreateFederationParams(TAPYRUS_OP_MODE::PROD, true), std::runtime_error);
}
BOOST_AUTO_TEST_SUITE_END()
