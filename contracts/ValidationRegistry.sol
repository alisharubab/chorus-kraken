// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ValidationRegistry
 * @notice Stores cryptographic hashes of validation artifacts on-chain.
 *         Each vote, trade, and risk check produces a signed receipt whose
 *         SHA-256 hash is logged here for permanent auditability.
 *
 *         Artifact types: VOTE, META_DECISION, TRADE_INTENT, TRADE_CONFIRMED,
 *                         RISK_CHECK, REPUTATION_UPDATE, CHECKPOINT
 */
contract ValidationRegistry {

    struct ValidationArtifact {
        uint256 artifactId;
        uint256 agentId;
        string  artifactType;   // e.g. "VOTE", "TRADE_CONFIRMED"
        bytes32 dataHash;       // SHA-256 hash of the full artifact JSON
        uint256 timestamp;
    }

    uint256 public nextArtifactId = 1;

    mapping(uint256 => ValidationArtifact) public artifacts;
    mapping(uint256 => uint256[]) public agentArtifacts;  // agentId => list of artifact IDs

    event ArtifactLogged(uint256 indexed artifactId, uint256 indexed agentId, string artifactType);

    /**
     * @notice Log a validation artifact hash on-chain.
     * @param agentId       The agent that produced this artifact
     * @param artifactType  Category string (VOTE, TRADE_INTENT, etc.)
     * @param dataHash      SHA-256 hash of the complete artifact JSON
     * @return The newly assigned artifact ID
     */
    function logArtifact(
        uint256 agentId,
        string memory artifactType,
        bytes32 dataHash
    ) external returns (uint256) {
        uint256 id = nextArtifactId++;
        artifacts[id] = ValidationArtifact(id, agentId, artifactType, dataHash, block.timestamp);
        agentArtifacts[agentId].push(id);
        emit ArtifactLogged(id, agentId, artifactType);
        return id;
    }

    /**
     * @notice Get the number of artifacts logged by an agent.
     */
    function getArtifactCount(uint256 agentId) external view returns (uint256) {
        return agentArtifacts[agentId].length;
    }
}
