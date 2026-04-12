# CHORUS ✨ Sentinel AI

> **A Multi-Agent Senate for AI-Powered Crypto Trading with ERC-8004 Identity & On-Chain Validation**

---


## Live System Status
- CHORUS is actively running in live 15-minute decision cycles.
- Agent votes, risk checks, and meta-decisions are being generated continuously.
- Validation artifacts are being logged on-chain on Base Sepolia with transaction hashes for auditability.
- Dashboard is available locally at `http://127.0.0.1:5000` for real-time monitoring.

---

## 📖 What is CHORUS?
**CHORUS** is a decentralized, multi-agent AI trading system. Instead of relying on a single "black-box" trading bot to hold capital, CHORUS orchestrates a "senate" of specialized AI agents that debate and vote on market positioning. 

Every vote, decision, and risk-veto is cryptographically signed and logged permanently on the Ethereum blockchain (Base Sepolia) as an **ERC-8004 Validation Artifact**. This guarantees 100% transparency, an auditable track record, and a quantifiable "Reputation Score" that dynamically weights each agent's future voting power based on their historical accuracy.

---

## 🏛️ How the Voting System Works
Our system utilizes 5 interconnected components:
1. **Trend Agent**: Analyzes simple moving averages (SMA) to determine if the market is trending bullish or bearish.
2. **Reversal Agent**: Monitors RSI oscillators to identify overbought or oversold conditions.
3. **Sentiment Agent**: Scans market-wide PRISM signals like volume spikes and price deltas.
4. **Risk Sentinel**: A specialized defensive agent. Instead of looking for profit, it strictly protects capital. It possesses overarching **veto power** and forces a `HOLD` if downside limits are breached.
5. **Meta-Agent (The Chairman)**: Collects all votes, checks for a Risk veto, and mathematically aggregates the decisions weighted by each agent's **On-Chain Reputation Score**. If consensus passes a 60% threshold, it natively fires the trade directly through the **Kraken CLI/API**.

---

## 🔗 Deployed Contract Addresses
CHORUS relies on three separate smart contracts handling ERC-8004 identity verification, reputation math, and receipt logging. 

* **Network**: Base Sepolia Testnet
* **Identity Registry**: `0xc964Fc92AfE6cE988DC9D56Bf384FBc16235BdAa`
* **Reputation Registry**: `0xe0020De74c15b176C9cd8f1770437C89da428886`
* **Validation Registry**: `0xE4d30c7a4B3e31d52566bE57Ad3Db042361E3c13`

---


## Leaderboard & On-Chain Activity
Use these deployed contracts for hackathon leaderboard verification and on-chain activity review:

- **Identity Registry**: `0xc964Fc92AfE6cE988DC9D56Bf384FBc16235BdAa`
- **Reputation Registry**: `0xe0020De74c15b176C9cd8f1770437C89da428886`
- **Validation Registry**: `0xE4d30c7a4B3e31d52566bE57Ad3Db042361E3c13`
- **Block Explorer**: https://sepolia.basescan.org

---

## ⚙️ How to Run Locally

### 1. Prerequisites
- **Node.js** (LTS) for Hardhat smart-contract dependencies.
- **Python 3.11+** for AI Agent execution logic and the Flask Web Dashboard.
- **Kraken Account & API Keys** (with Query & Order execution enabled, **Withdraw Disabled**).
- **Alchemy API Key** for connecting the system to the Base Sepolia blockchain.

### 2. Environment Setup
Clone the repository and install dependencies:
```bash
# Install Python Requirements
pip install -r requirements.txt

# Install Node modules 
npm install
```

Create a `.env` file in the root directory mirroring these keys exactly:
```env
PRIVATE_KEY=your_metamask_private_key_here
ALCHEMY_API_KEY=your_alchemy_api_key_here
KRAKEN_API_KEY=your_kraken_api_key_here
KRAKEN_API_SECRET=your_kraken_api_secret_here
PRISM_API_KEY=your_prism_api_key_here
```

### 3. Application Commands
Once you have your `.env` configured, hook your credentials natively into the Kraken CLI configuration format:
```bash
python scripts/setup_kraken_config.py
```


Run the core system in this command order:
```bash
python scripts/setup_kraken_config.py
python agents/meta_agent.py
python dashboard/app.py
```


**To start the Automated Trading Suite:**
This runs the full polling strategy check, fetching live data on 15 minute cycles.
```bash
python agents/meta_agent.py
```

**To start the Sentinel AI Web Dashboard:**
View your agents' live consensus, UI breakdown, and contract signatures natively! Run this in a separate terminal:
```bash
python dashboard/app.py
```
*Navigate to `http://127.0.0.1:5000` in your web browser!*

**To run the full E2E System Test Suite:**
```bash
python scripts/test_cycle.py
```

---


## Validation Artifacts
CHORUS logs every critical decision artifact for full auditability:

- Every **agent vote** is serialized and signed.
- Every **risk check** from Risk Sentinel is logged.
- Every **trade decision** (including holds, intents, and confirmations) is written to local artifacts and anchored on-chain with a transaction hash.

Sample first live trade transaction hash:

- `0x18809fe48573e3f5c6796f19f68fe6f26cbdc6c85bc5f485fd3adf29cafdb2f0`

All transaction activity can be verified on Base Sepolia via:

- https://sepolia.basescan.org

---

## 📜 Sample Validation Artifact
Whenever a trade executes or is aborted, a cryptographic signature is generated, stored in `/artifacts/` locally, and the hash is securely logged on-chain. Here is an example of the output payload:

```json
{
  "type": "META_DECISION",
  "pair": "XBTUSD",
  "votes": [
    {
      "agent_name": "TrendAgent",
      "direction": "SELL",
      "confidence": 100,
      "reason": "Bearish crossover: SMA10 < SMA30",
      "signature": "0xb821681f8f7341654ddd5fb4..."
    }
  ],
  "decision": {
    "decision": "HOLD",
    "reason": "No consensus. BUY:0.0% SELL:33.3% (need 60%)",
    "vote_breakdown": {
      "TrendAgent": {
        "confidence": 100,
        "reputation": 50,
        "weight": 50.0
      }
    }
  },
  "cycle_timestamp": "2026-04-02 22:21:37"
}
```

---
### Let's Build Decentralized Trust 🤝
Built for the **AI Trading Hackathon**. 
Special shoutout to our ecosystem resources! 
* `@krakenfx` 
* `@lablabai` 
* `@Surgexyz_`
