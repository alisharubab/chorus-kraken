// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AgentIdentityRegistry
 * @notice ERC-8004 identity layer - registers each AI agent with a unique on-chain ID,
 *         wallet address, role, and metadata URI.
 */
contract AgentIdentityRegistry {

    struct AgentRecord {
        uint256 agentId;       // Unique incrementing ID
        address agentWallet;   // Ethereum address the agent signs with
        string  name;          // Human-readable name e.g. "TrendAgent"
        string  role;          // Role e.g. "trend_follower"
        string  metadataURI;   // IPFS/HTTP link to extended metadata JSON
        bool    active;        // Is this agent currently active?
        uint256 registeredAt;  // Unix timestamp of registration
    }

    uint256 public nextAgentId = 1;

    mapping(uint256 => AgentRecord) public agents;
    mapping(address => uint256)     public walletToAgentId;

    event AgentRegistered(uint256 indexed agentId, address wallet, string name);

    /**
     * @notice Register a new agent on-chain.
     * @param _wallet   The agent's signing wallet address
     * @param _name     Human-readable agent name
     * @param _role     Agent role descriptor
     * @param _metadataURI  URI pointing to full metadata JSON
     * @return The newly assigned agent ID
     */
    function registerAgent(
        address _wallet,
        string memory _name,
        string memory _role,
        string memory _metadataURI
    ) external returns (uint256) {
        uint256 id = nextAgentId++;
        agents[id] = AgentRecord(id, _wallet, _name, _role, _metadataURI, true, block.timestamp);
        walletToAgentId[_wallet] = id;
        emit AgentRegistered(id, _wallet, _name);
        return id;
    }

    /**
     * @notice Check if an agent is currently active.
     */
    function isActive(uint256 agentId) external view returns (bool) {
        return agents[agentId].active;
    }
}
