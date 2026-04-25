// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AdhahiSupplyChain
 * @notice Anchors SHA-256 hashes of off-chain sheep lifecycle events.
 *         The contract intentionally stores ONLY hashes (bytes32) and metadata
 *         (timestamp, sender). All business data lives off-chain.
 */
contract AdhahiSupplyChain {
    struct Record {
        uint256 timestamp;
        address sender;
        bool exists;
    }

    // hash => record
    mapping(bytes32 => Record) private records;

    event SheepRegistered(bytes32 indexed dataHash, address indexed sender, uint256 timestamp);
    event EventAdded(bytes32 indexed dataHash, address indexed sender, uint256 timestamp);

    /// @notice Anchors the registration hash of a new sheep.
    function registerSheep(bytes32 dataHash) external {
        require(!records[dataHash].exists, "Hash already anchored");
        records[dataHash] = Record({
            timestamp: block.timestamp,
            sender: msg.sender,
            exists: true
        });
        emit SheepRegistered(dataHash, msg.sender, block.timestamp);
    }

    /// @notice Anchors the hash of a lifecycle event (quarantine, transport, ...).
    function addEvent(bytes32 dataHash) external {
        require(!records[dataHash].exists, "Hash already anchored");
        records[dataHash] = Record({
            timestamp: block.timestamp,
            sender: msg.sender,
            exists: true
        });
        emit EventAdded(dataHash, msg.sender, block.timestamp);
    }

    /// @notice Returns true if `dataHash` was previously anchored.
    function verifyEvent(bytes32 dataHash) external view returns (bool) {
        return records[dataHash].exists;
    }

    /// @notice Returns full record metadata (timestamp + sender).
    function getRecord(bytes32 dataHash)
        external
        view
        returns (uint256 timestamp, address sender, bool exists)
    {
        Record memory r = records[dataHash];
        return (r.timestamp, r.sender, r.exists);
    }
}
