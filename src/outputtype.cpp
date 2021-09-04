// Copyright (c) 2009-2010 Satoshi Nakamoto
// Copyright (c) 2009-2018 The Bitcoin Core developers
// Copyright (c) 2019 Chaintope Inc.
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <outputtype.h>

#include <keystore.h>
#include <pubkey.h>
#include <script/script.h>
#include <script/standard.h>

#include <assert.h>
#include <string>


CTxDestination GetDestinationForKey(const CPubKey& key, OutputType type)
{
    switch (type) {
    case OutputType::CHANGE_AUTO:
    case OutputType::LEGACY: return key.GetID();
    default: assert(false);
    }
}

std::vector<CTxDestination> GetAllDestinationsForKey(const CPubKey& key)
{
    CKeyID keyid = key.GetID();
    if (key.IsCompressed()) {
        CTxDestination p2sh = CScriptID(GetScriptForDestination(keyid));
        return std::vector<CTxDestination>{std::move(keyid), std::move(p2sh)};
    } else {
        return std::vector<CTxDestination>{std::move(keyid)};
    }
}

CTxDestination AddAndGetDestinationForScript(CKeyStore& keystore, const CScript& script, OutputType type)
{
    // Add script to keystore
    keystore.AddCScript(script);
    // Note that scripts over 520 bytes are not yet supported.
    switch (type) {
    case OutputType::LEGACY:
        return CScriptID(script);
    default: assert(false);
    }
}

