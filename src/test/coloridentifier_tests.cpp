// Copyright (c) 2020 Chaintope Inc.
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.


#include <test/test_tapyrus.h>
#include <map>
#include <primitives/transaction.h>
#include <script/script.h>
#include <coloridentifier.h>
#include <boost/test/unit_test.hpp>

BOOST_FIXTURE_TEST_SUITE(coloridentifier_tests, BasicTestingSetup)

BOOST_AUTO_TEST_CASE(coloridentifier_valid_unserialize)
{
    //type NONE
    ColorIdentifier c0;
    uint8_t str[32] = {};
    CDataStream ss0(ParseHex("00"), SER_NETWORK, INIT_PROTO_VERSION);
    ss0 >> c0;
    BOOST_CHECK_EQUAL(TokenToUint(c0.type), TokenToUint(TokenTypes::NONE));
    BOOST_CHECK(memcmp(&c0.payload[0], &str[0], 32) == 0);

    //type REISSUABLE - insufficient data
    try {
        CDataStream ss00(ParseHex("c100"), SER_NETWORK, INIT_PROTO_VERSION);
        ss00 >> c0;
        BOOST_CHECK_MESSAGE(false, "We should have thrown");
    } catch (const std::ios_base::failure& e) {
    }

    //type NFT - insufficient data
    try {
        CDataStream ss00(ParseHex("c38282263212c609d9ea2a6e3e172de238d8c39cabd5ac1ca10646e23f"), SER_NETWORK, INIT_PROTO_VERSION);
        ss00 >> c0;
        BOOST_CHECK_MESSAGE(false, "We should have thrown");
    } catch (const std::ios_base::failure& e) {
    }

    //type NONE - 33 bytes
    ColorIdentifier c00;
    CDataStream ss01(ParseHex("008282263212c609d9ea2a6e3e172de238d8c39cabd5ac1ca10646e23fd5f51508"), SER_NETWORK, INIT_PROTO_VERSION);
    ss01 >> c00;
    BOOST_CHECK_EQUAL(TokenToUint(c00.type), TokenToUint(TokenTypes::NONE));
    BOOST_CHECK(memcmp(&c00.payload[0], &str[0], 32) == 0);

    //type unknown - 33 bytes, type byte '01'
    ColorIdentifier c01;
    CDataStream ss02(ParseHex("018282263212c609d9ea2a6e3e172de238d8c39cabd5ac1ca10646e23fd5f51508"), SER_NETWORK, INIT_PROTO_VERSION);
    ss02 >> c01;
    BOOST_CHECK_EQUAL(TokenToUint(c01.type), TokenToUint(TokenTypes::NONE));
    BOOST_CHECK(memcmp(&c01.payload[0], &str[0], 32) == 0);

    //type unknown - 33 bytes, type byte '02'
    CDataStream ss03(ParseHex("028282263212c609d9ea2a6e3e172de238d8c39cabd5ac1ca10646e23fd5f51508"), SER_NETWORK, INIT_PROTO_VERSION);
    ss03 >> c01;
    BOOST_CHECK_EQUAL(TokenToUint(c01.type), TokenToUint(TokenTypes::NONE));
    BOOST_CHECK(memcmp(&c01.payload[0], &str[0], 32) == 0);

    //type unknown - 33 bytes, type byte '03'
    CDataStream ss04(ParseHex("038282263212c609d9ea2a6e3e172de238d8c39cabd5ac1ca10646e23fd5f51508"), SER_NETWORK, INIT_PROTO_VERSION);
    ss04 >> c01;
    BOOST_CHECK_EQUAL(TokenToUint(c01.type), TokenToUint(TokenTypes::NONE));
    BOOST_CHECK(memcmp(&c01.payload[0], &str[0], 32) == 0);

    //type unknown - 33 bytes, type byte '04'
    CDataStream ss05(ParseHex("048282263212c609d9ea2a6e3e172de238d8c39cabd5ac1ca10646e23fd5f51508"), SER_NETWORK, INIT_PROTO_VERSION);
    ss05 >> c01;
    BOOST_CHECK_EQUAL(TokenToUint(c01.type), TokenToUint(TokenTypes::NONE));
    BOOST_CHECK(memcmp(&c01.payload[0], &str[0], 32) == 0);

    //type unknown - 33 bytes, type byte 'c4'
    CDataStream ss06(ParseHex("c48282263212c609d9ea2a6e3e172de238d8c39cabd5ac1ca10646e23fd5f51508"), SER_NETWORK, INIT_PROTO_VERSION);
    ss06 >> c01;
    BOOST_CHECK_EQUAL(TokenToUint(c01.type), TokenToUint(TokenTypes::NONE));
    BOOST_CHECK(memcmp(&c01.payload[0], &str[0], 32) == 0);

    //type REISSUABLE
    std::vector<unsigned char> scriptVector(ParseHex("c38282263212c609d9ea2a6e3e172de238d8c39cabd5ac1ca10646e23fd5f51508"));
    uint8_t scripthash[CSHA256::OUTPUT_SIZE];
    scriptVector.insert(scriptVector.begin(), 0x21);
    CSHA256().Write(scriptVector.data(), scriptVector.size()).Finalize(scripthash);
    
    ColorIdentifier c1;
    CDataStream ss1(ParseHex("c1f335bd3240ddfd87a2c2fc5a53210606460f19143f5e475729c46e06fcc9858f"), SER_NETWORK, INIT_PROTO_VERSION);
    ss1 >> c1;
    BOOST_CHECK_EQUAL(HexStr(&scripthash[0], &scripthash[32]), "f335bd3240ddfd87a2c2fc5a53210606460f19143f5e475729c46e06fcc9858f");
    BOOST_CHECK_EQUAL(HexStr(&c1.payload[0], &c1.payload[32]), "f335bd3240ddfd87a2c2fc5a53210606460f19143f5e475729c46e06fcc9858f");
    BOOST_CHECK_EQUAL(TokenToUint(c1.type), TokenToUint(TokenTypes::REISSUABLE));
    BOOST_CHECK(memcmp(&c1.payload[0], &scripthash[0], 32) == 0);

    //type NON_REISSUABLE
    uint256 hashMalFix(ParseHex("485273f6703f038a234400edadb543eb44b4af5372e8b207990beebc386e7954"));
    COutPoint out(hashMalFix, 0);
    CDataStream s(SER_NETWORK, INIT_PROTO_VERSION);
    s << out;
    CSHA256().Write((const unsigned char *)s.data(), s.size()).Finalize(scripthash);

    ColorIdentifier c2;
    CDataStream ss2(ParseHex("c29608951ee23595caa227e7668e39f9d3525a39e9dc30d7391f138576c07be84d"), SER_NETWORK, INIT_PROTO_VERSION);
    ss2 >> c2;
    BOOST_CHECK_EQUAL(HexStr(&scripthash[0], &scripthash[32]), "9608951ee23595caa227e7668e39f9d3525a39e9dc30d7391f138576c07be84d");
    BOOST_CHECK_EQUAL(HexStr(&c2.payload[0], &c2.payload[32], false), "9608951ee23595caa227e7668e39f9d3525a39e9dc30d7391f138576c07be84d");
    BOOST_CHECK_EQUAL(TokenToUint(c2.type), TokenToUint(TokenTypes::NON_REISSUABLE));
    BOOST_CHECK(memcmp(&c2.payload[0], &scripthash[0], 32) == 0);

    //type NFT - 33 bytes
    ColorIdentifier c04;
    CDataStream ss07(ParseHex("c38282263212c609d9ea2a6e3e172de238d8c39cabd5ac1ca10646e23fd5f51508"), SER_NETWORK, INIT_PROTO_VERSION);
    ss07 >> c04;
    BOOST_CHECK_EQUAL(TokenToUint(c04.type), TokenToUint(TokenTypes::NFT));
    BOOST_CHECK_EQUAL(HexStr(&c04.payload[0], &c04.payload[32]), "8282263212c609d9ea2a6e3e172de238d8c39cabd5ac1ca10646e23fd5f51508");
}

BOOST_AUTO_TEST_CASE(coloridentifier_valid_serialize)
{
    //type NONE
    ColorIdentifier c0;
    CDataStream ss0(SER_NETWORK, INIT_PROTO_VERSION);
    ss0 << c0;
    BOOST_CHECK_EQUAL(HexStr(ss0.begin(), ss0.end(), false), "00");

    //type REISSUABLE
    std::vector<unsigned char> scriptVector(ParseHex("c38282263212c609d9ea2a6e3e172de238d8c39cabd5ac1ca10646e23fd5f51508"));
    ColorIdentifier c1(CScript() << scriptVector);
    CDataStream ss1(SER_NETWORK, INIT_PROTO_VERSION);
    ss1 << c1;
    BOOST_CHECK_EQUAL(HexStr(ss1.begin(), ss1.end(), false), "c1f335bd3240ddfd87a2c2fc5a53210606460f19143f5e475729c46e06fcc9858f");

    //type NON_REISSUABLE
    uint256 hashMalFix(ParseHex("485273f6703f038a234400edadb543eb44b4af5372e8b207990beebc386e7954"));
    COutPoint out(hashMalFix, 0);
    ColorIdentifier c2(out, TokenTypes::NON_REISSUABLE);
    CDataStream ss2(SER_NETWORK, INIT_PROTO_VERSION);
    ss2 << c2;
    BOOST_CHECK_EQUAL(HexStr(ss2.begin(), ss2.end()), "c29608951ee23595caa227e7668e39f9d3525a39e9dc30d7391f138576c07be84d");

    //type unknown
    ColorIdentifier c4;
    std::vector<unsigned char> bytes = ParseHex("048282263212c609d9ea2a6e3e172de238d8c39cabd5ac1ca10646e23fd5f51508");
    c4.type = UintToToken(bytes[0]);
    memcpy(c4.payload, bytes.data() + 1, CSHA256::OUTPUT_SIZE);
    CDataStream ss4(SER_NETWORK, INIT_PROTO_VERSION);
    ss4 << c4;
    BOOST_CHECK_EQUAL(HexStr(ss4.begin(), ss4.end(), false), "00");

}

BOOST_AUTO_TEST_CASE(coloridentifier_compare)
{
    //type REISSUABLE
    std::vector<unsigned char> scriptVector(ParseHex("c38282263212c609d9ea2a6e3e172de238d8c39cabd5ac1ca10646e23fd5f51508"));
    ColorIdentifier c1(CScript() << scriptVector);

    uint8_t scripthash[CSHA256::OUTPUT_SIZE];
    scriptVector.insert(scriptVector.begin(), 0x21);
    CSHA256().Write(scriptVector.data(), scriptVector.size()).Finalize(scripthash);
    ColorIdentifier c2;
    c2.type = TokenTypes::REISSUABLE;
    memcpy(&c2.payload[0], &scripthash[0], 32);

    BOOST_CHECK_EQUAL(HexStr(&scripthash[0], &scripthash[32]), "f335bd3240ddfd87a2c2fc5a53210606460f19143f5e475729c46e06fcc9858f");
    BOOST_CHECK_EQUAL(HexStr(&c1.payload[0], &c1.payload[32]), "f335bd3240ddfd87a2c2fc5a53210606460f19143f5e475729c46e06fcc9858f");
    BOOST_CHECK_EQUAL(HexStr(&c2.payload[0], &c2.payload[32]), "f335bd3240ddfd87a2c2fc5a53210606460f19143f5e475729c46e06fcc9858f");

    BOOST_CHECK(c1.operator==(c2));

    //type NON_REISSUABLE
    uint256 hashMalFix(ParseHex("485273f6703f038a234400edadb543eb44b4af5372e8b207990beebc386e7954"));
    COutPoint out(hashMalFix, 0);
    ColorIdentifier c3(out, TokenTypes::NON_REISSUABLE);

    ColorIdentifier c4;
    CDataStream s(SER_NETWORK, INIT_PROTO_VERSION);
    s << out;
    CSHA256().Write((const unsigned char *)s.data(), s.size()).Finalize(scripthash);
    c4.type = TokenTypes::NON_REISSUABLE;
    memcpy(&c4.payload[0], &scripthash[0], 32);

    BOOST_CHECK(c3.operator==(c4));

    BOOST_CHECK(!c1.operator==(c3));
    BOOST_CHECK(!c2.operator==(c4));

    //type NONE
    ColorIdentifier c0;
    BOOST_CHECK(!c0.operator==(c1));
    BOOST_CHECK(!c0.operator==(c2));
    BOOST_CHECK(!c0.operator==(c3));
    BOOST_CHECK(!c0.operator==(c4));

    //type unknown
    ColorIdentifier c5;
    std::vector<unsigned char> bytes = ParseHex("048282263212c609d9ea2a6e3e172de238d8c39cabd5ac1ca10646e23fd5f51508");
    c5.type = UintToToken(bytes[0]);
    memcpy(c5.payload, bytes.data() + 1, CSHA256::OUTPUT_SIZE);

    BOOST_CHECK(!c5.operator==(c0));
    BOOST_CHECK(!c5.operator==(c1));
    BOOST_CHECK(!c5.operator==(c2));
    BOOST_CHECK(!c5.operator==(c3));
    BOOST_CHECK(!c5.operator==(c4));
}

BOOST_AUTO_TEST_CASE(coloridentifier_map_compare)
{
    //type REISSUABLE
    std::vector<unsigned char> scriptVector(ParseHex("c38282263212c609d9ea2a6e3e172de238d8c39cabd5ac1ca10646e23fd5f51508"));
    ColorIdentifier c1(CScript() << scriptVector);

    uint8_t scripthash[CSHA256::OUTPUT_SIZE];
    scriptVector.insert(scriptVector.begin(), 0x21);
    CSHA256().Write(scriptVector.data(), scriptVector.size()).Finalize(scripthash);
    ColorIdentifier c2;
    c2.type = TokenTypes::REISSUABLE;
    memcpy(&c2.payload[0], &scripthash[0], 32);

    BOOST_CHECK_EQUAL(c1 < c2, false);

    //type NON_REISSUABLE
    uint256 hashMalFix(ParseHex("485273f6703f038a234400edadb543eb44b4af5372e8b207990beebc386e7954"));
    COutPoint out(hashMalFix, 0);
    ColorIdentifier c3(out, TokenTypes::NON_REISSUABLE);

    ColorIdentifier c4;
    CDataStream s(SER_NETWORK, INIT_PROTO_VERSION);
    s << out;
    CSHA256().Write((const unsigned char *)s.data(), s.size()).Finalize(scripthash);
    c4.type = TokenTypes::NON_REISSUABLE;
    memcpy(&c4.payload[0], &scripthash[0], 32);
    BOOST_CHECK_EQUAL(c3 < c4, false);

    BOOST_CHECK_EQUAL(c1 < c3, true);
    BOOST_CHECK_EQUAL(c2 < c4, true);

    //type NONE
    ColorIdentifier c0;
    BOOST_CHECK_EQUAL(c0 < c1, true);
    BOOST_CHECK_EQUAL(c0 < c2, true);
    BOOST_CHECK_EQUAL(c0 < c3, true);
    BOOST_CHECK_EQUAL(c0 < c4, true);

    //type unknown
    ColorIdentifier c5;
    std::vector<unsigned char> bytes = ParseHex("048282263212c609d9ea2a6e3e172de238d8c39cabd5ac1ca10646e23fd5f51508");
    c5.type = UintToToken(bytes[0]);
    memcpy(c5.payload, bytes.data() + 1, CSHA256::OUTPUT_SIZE);

    BOOST_CHECK_EQUAL(c5 < c0, false);
    BOOST_CHECK_EQUAL(c5 < c1, true);
    BOOST_CHECK_EQUAL(c5 < c2, true);
    BOOST_CHECK_EQUAL(c5 < c3, true);
    BOOST_CHECK_EQUAL(c5 < c4, true);
}

BOOST_AUTO_TEST_CASE(coloridentifier_string_conversion)
{
    //type REISSUABLE
    std::vector<unsigned char> scriptVector(ParseHex("c38282263212c609d9ea2a6e3e172de238d8c39cabd5ac1ca10646e23fd5f51508"));
    ColorIdentifier c1(CScript() << scriptVector);

    BOOST_CHECK_EQUAL(c1.toHexString(), "c1f335bd3240ddfd87a2c2fc5a53210606460f19143f5e475729c46e06fcc9858f");

    //type NON_REISSUABLE
    uint256 hashMalFix(ParseHex("485273f6703f038a234400edadb543eb44b4af5372e8b207990beebc386e7954"));
    COutPoint out(hashMalFix, 0);
    ColorIdentifier c2(out, TokenTypes::NON_REISSUABLE);

    BOOST_CHECK_EQUAL(c2.toHexString(), "c29608951ee23595caa227e7668e39f9d3525a39e9dc30d7391f138576c07be84d");

    //type NONE
    ColorIdentifier c3;
    BOOST_CHECK_EQUAL(c3.toHexString(), "TPC");

    //type unknown
    ColorIdentifier c4;
    std::vector<unsigned char> bytes = ParseHex("048282263212c609d9ea2a6e3e172de238d8c39cabd5ac1ca10646e23fd5f51508");
    c4.type = UintToToken(bytes[0]);
    memcpy(c4.payload, bytes.data() + 1, CSHA256::OUTPUT_SIZE);

    BOOST_CHECK_EQUAL(c4.toHexString(), "TPC");

}
BOOST_AUTO_TEST_SUITE_END()