// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ReputationRegistry
 * @notice Tracks each agent's reputation score, updated after every trade resolution.
 *         Score starts at 50. +5 for correct predictions, -3 for wrong ones.
 *         The meta-agent reads these scores to weight votes.
 */
contract ReputationRegistry {

    struct ReputationRecord {
        uint256 agentId;
        int256  score;          // Can go negative if agent is consistently wrong
        uint256 totalVotes;     // Total votes cast
        uint256 correctVotes;   // How many were correct
        uint256 lastUpdated;    // Unix timestamp of last update
    }

    mapping(uint256 => ReputationRecord) public reputation;

    address public owner;

    event ReputationUpdated(uint256 indexed agentId, int256 newScore);

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }

    /**
     * @notice Initialize an agent's reputation to 50 (starting score).
     * @param agentId  The agent's on-chain ID from the Identity Registry
     */
    function initAgent(uint256 agentId) external onlyOwner {
        reputation[agentId] = ReputationRecord(agentId, 50, 0, 0, block.timestamp);
    }

    /**
     * @notice Update an agent's reputation after a trade resolves.
     * @param agentId     The agent's on-chain ID
     * @param wasCorrect  Whether the agent's vote matched the actual outcome
     */
    function updateReputation(uint256 agentId, bool wasCorrect) external onlyOwner {
        ReputationRecord storage r = reputation[agentId];
        r.totalVotes += 1;
        if (wasCorrect) {
            r.correctVotes += 1;
            r.score += 5;   // +5 for correct prediction
        } else {
            r.score -= 3;   // -3 for wrong prediction
        }
        r.lastUpdated = block.timestamp;
        emit ReputationUpdated(agentId, r.score);
    }

    /**
     * @notice Get an agent's current reputation score.
     */
    function getScore(uint256 agentId) external view returns (int256) {
        return reputation[agentId].score;
    }

    /**
     * @notice Get full reputation record for an agent.
     */
    function getRecord(uint256 agentId) external view returns (
        int256 score, uint256 totalVotes, uint256 correctVotes, uint256 lastUpdated
    ) {
        ReputationRecord storage r = reputation[agentId];
        return (r.score, r.totalVotes, r.correctVotes, r.lastUpdated);
    }
}
