// Copyright (c) 2009-2010 Satoshi Nakamoto
// Copyright (c) 2009-2018 The Bitcoin Core developers
// Copyright (c) 2019-2020 Chaintope Inc.
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#ifndef BITCOIN_PRIMITIVES_BLOCK_H
#define BITCOIN_PRIMITIVES_BLOCK_H

#include <primitives/transaction.h>
#include <primitives/xfield.h>
#include <serialize.h>
#include <uint256.h>
#include <key.h>

/** Nodes collect new transactions into a block, hash them into a hash tree,
 * and scan through nonce values to make the block's hash satisfy proof-of-work
 * requirements.  When they solve the proof-of-work, they broadcast the block
 * to everyone and the block is added to the block chain.  The first transaction
 * in the block is a special one that creates a new coin owned by the creator
 * of the block.
 */
class CBlockHeaderWithoutProof
{
public:
    // header
    int32_t nFeatures;
    uint256 hashPrevBlock;
    uint256 hashMerkleRoot;
    uint256 hashImMerkleRoot;
    uint32_t nTime;
    CXField xfield;

    CBlockHeaderWithoutProof()
    {
        SetNull();
    }

    CBlockHeaderWithoutProof(CBlockHeaderWithoutProof&&) = default;
    CBlockHeaderWithoutProof(const CBlockHeaderWithoutProof& copy) = default;
    CBlockHeaderWithoutProof(CBlockHeaderWithoutProof& copy) = default;
    CBlockHeaderWithoutProof& operator=(const CBlockHeaderWithoutProof& copy) = default;
    CBlockHeaderWithoutProof& operator=(CBlockHeaderWithoutProof& copy) = default;

    ADD_SERIALIZE_METHODS;

    template <typename Stream, typename Operation>
    inline void SerializationOp(Stream& s, Operation ser_action) {
        READWRITE(this->nFeatures);
        READWRITE(hashPrevBlock);
        READWRITE(hashMerkleRoot);
        READWRITE(hashImMerkleRoot);
        READWRITE(nTime);
        READWRITE(xfield);
    }

    void SetNull()
    {
        nFeatures = 0;
        hashPrevBlock.SetNull();
        hashMerkleRoot.SetNull();
        hashImMerkleRoot.SetNull();
        nTime = 0;
        xfield.clear();
    }

    bool IsNull() const
    {
        return (nTime == 0);
    }

    // Return BlockHash for proof of Signed Blocks
    uint256 GetHashForSign() const;

    int64_t GetBlockTime() const
    {
        return (int64_t)nTime;
    }

};

class CBlockHeader : public CBlockHeaderWithoutProof
{
public:
    static constexpr int32_t TAPYRUS_BLOCK_FEATURES = 1;
    std::vector<unsigned char> proof{CPubKey::SCHNORR_SIGNATURE_SIZE};

    CBlockHeader():CBlockHeaderWithoutProof(),proof() {}

    CBlockHeader(CBlockHeader&& copy) = default;
    CBlockHeader(const CBlockHeader& copy) = default;
    CBlockHeader(CBlockHeader& copy) = default;
    CBlockHeader& operator=(const CBlockHeader& copy) = default;
    CBlockHeader& operator=(CBlockHeader& copy) = default;
    ADD_SERIALIZE_METHODS;

    template <typename Stream, typename Operation>
    inline void SerializationOp(Stream& s, Operation ser_action) {
        CBlockHeaderWithoutProof::SerializationOp(s, ser_action);
        READWRITE(proof);
    }

    uint256 GetHash() const;
    std::string ToString() const;
    bool AbsorbBlockProof(const std::vector<unsigned char>& blockproof, const CPubKey& aggregatePubkey);
};

class CBlock : public CBlockHeader
{
public:
    // network and disk
    std::vector<CTransactionRef> vtx;

    // memory only
    mutable bool fChecked;

    CBlock()
    {
        SetNull();
    }

    CBlock(const CBlockHeader &header)
    {
        SetNull();
        *(static_cast<CBlockHeader*>(this)) = header;
    }

    ADD_SERIALIZE_METHODS;

    template <typename Stream, typename Operation>
    inline void SerializationOp(Stream& s, Operation ser_action) {
        READWRITEAS(CBlockHeader, *this);
        READWRITE(vtx);
    }

    void SetNull()
    {
        CBlockHeader::SetNull();
        vtx.clear();
        fChecked = false;
    }

    CBlockHeader GetBlockHeader() const
    {
        CBlockHeader block;
        block.nFeatures         = nFeatures;
        block.hashPrevBlock     = hashPrevBlock;
        block.hashMerkleRoot    = hashMerkleRoot;
        block.hashImMerkleRoot  = hashImMerkleRoot;
        block.nTime             = nTime;
        block.xfield            = xfield;
        block.proof             = proof;
        return block;
    }

    std::string ToString() const;

    uint32_t GetHeight() const;
};

/** Describes a place in the block chain to another node such that if the
 * other node doesn't have the same branch, it can find a recent common trunk.
 * The further back it is, the further before the fork it may be.
 */
struct CBlockLocator
{
    std::vector<uint256> vHave;

    CBlockLocator() {}

    explicit CBlockLocator(const std::vector<uint256>& vHaveIn) : vHave(vHaveIn) {}

    ADD_SERIALIZE_METHODS;

    template <typename Stream, typename Operation>
    inline void SerializationOp(Stream& s, Operation ser_action) {
        int nVersion = s.GetVersion();
        if (!(s.GetType() & SER_GETHASH))
            READWRITE(nVersion);
        READWRITE(vHave);
    }

    void SetNull()
    {
        vHave.clear();
    }

    bool IsNull() const
    {
        return vHave.empty();
    }
};

#endif // BITCOIN_PRIMITIVES_BLOCK_H
