# CHORUS Sentinel AI

> A multi-agent AI trading system with on-chain identity, reputation-weighted voting, and validation artifacts on Base Sepolia.

---

## Live System Status
- CHORUS runs in recurring decision cycles (see [Decision Flow](#decision-flow)).
- Agent votes, risk checks, and meta-decisions are saved locally and anchored on-chain.
- A local dashboard is available at http://127.0.0.1:5000 when running the project environment.

---

## Problem
Most trading bots are black boxes:
- One model controls everything.
- Decisions are hard to audit.
- Risk controls are often weak or hidden.
- There is no durable record of why a trade happened.

In practice, this creates trust, explainability, and operational risk.

---

## Solution
CHORUS solves this by combining:
- A **senate of specialized agents** (not a single model)
- A **risk-veto layer** that can stop trading
- **Reputation-weighted consensus** for execution decisions
- **On-chain validation artifacts** for transparent auditability

Every key action is traceable:
- Who voted
- What they voted
- Why they voted
- What final decision was executed
- What was logged on-chain

---

## System Architecture
CHORUS has five core decision agents:

1. **TrendAgent**
   Uses SMA crossover logic to detect directional trend.

2. **ReversalAgent**
   Uses RSI to detect overbought/oversold reversal conditions.

3. **SentimentAgent**
   Uses market structure signals (volume/price behavior) to estimate sentiment.

4. **RiskSentinel**
   Defensive guardrail with veto power. If risk limits are breached, final decision is forced to `HOLD`.

5. **Meta-Agent**
   Collects all votes, applies reputation weighting, handles override rules, and executes trades.

Additional components:
- **Kraken Execution Layer**: paper/live command flow through Kraken CLI
- **Artifact Logger**: stores JSON artifact locally + logs hash to ValidationRegistry
- **Flask Dashboard**: displays votes, decisions, artifacts, contract info

---

## Decision Flow
1. Meta-Agent starts a cycle.
2. Sub-agents return signed votes (`BUY`/`SELL`/`HOLD` + confidence).
3. RiskSentinel veto is checked first.
4. Votes are weighted by on-chain reputation.
5. Consensus or trigger logic determines final action.
6. Trade intent/execution is processed.
7. Decision artifact is saved locally and hash is logged on-chain.

---

## Momentum Trigger Logic
CHORUS includes a momentum override in Meta-Agent:
- If **TrendAgent = SELL at 100% confidence for 3 consecutive cycles**, system can force a `SELL` even when normal consensus is not met.
- RiskSentinel veto still overrides all trade triggers.
- Trigger cause is explicitly written into the decision artifact.

---

## Deployed Contract Addresses & On-Chain Activity
Network: **Base Sepolia Testnet**

- **Identity Registry**: `0xc964Fc92AfE6cE988DC9D56Bf384FBc16235BdAa`
- **Reputation Registry**: `0xe0020De74c15b176C9cd8f1770437C89da428886`
- **Validation Registry**: `0xE4d30c7a4B3e31d52566bE57Ad3Db042361E3c13`
- **Explorer**: https://sepolia.basescan.org

---

## Validation Artifacts
CHORUS logs all critical actions as validation artifacts:
- Agent vote artifacts
- Risk check artifacts
- Meta decision artifacts
- Trade intent / trade confirmed artifacts

Each artifact is:
1. Saved as JSON in `/artifacts`
2. Hashed (SHA-256)
3. Logged on-chain with transaction metadata

Sample live trade TX hash:
- `0x18809fe48573e3f5c6796f19f68fe6f26cbdc6c85bc5f485fd3adf29cafdb2f0`

---

## Project Structure
```text
chorus-kraken/
├─ agents/
│  ├─ utils.py
│  ├─ trend_agent.py
│  ├─ reversal_agent.py
│  ├─ sentiment_agent.py
│  ├─ risk_sentinel.py
│  ├─ meta_agent.py
│  ├─ artifact_logger.py
│  └─ kraken_client.py
├─ dashboard/
│  ├─ app.py
│  ├─ templates/index.html
│  └─ static/
├─ contracts/
│  ├─ AgentIdentityRegistry.sol
│  ├─ ReputationRegistry.sol
│  └─ ValidationRegistry.sol
├─ scripts/
│  ├─ setup_kraken_config.py
│  └─ test_cycle.py
├─ artifacts/
├─ cache/
├─ requirements.txt
└─ README.md
```

---

## How to Run Locally

### 1. Prerequisites
- Python 3.11+
- Node.js (LTS)
- Kraken account + API key/secret
- Alchemy API key for Base Sepolia

### 2. Install Dependencies
```bash
pip install -r requirements.txt
npm install
```

### 3. Configure Environment
Create `.env` in project root:

```env
PRIVATE_KEY=your_private_key
ALCHEMY_API_KEY=your_alchemy_api_key
KRAKEN_API_KEY=your_kraken_api_key
KRAKEN_API_SECRET=your_kraken_api_secret
PRISM_API_KEY=your_prism_api_key
IDENTITY_CONTRACT=0xc964Fc92AfE6cE988DC9D56Bf384FBc16235BdAa
REPUTATION_CONTRACT=0xe0020De74c15b176C9cd8f1770437C89da428886
VALIDATION_CONTRACT=0xE4d30c7a4B3e31d52566bE57Ad3Db042361E3c13
```

### 4. Run in Correct Order
```bash
python scripts/setup_kraken_config.py
python agents/meta_agent.py
python dashboard/app.py
```

Dashboard URL:
- `http://127.0.0.1:5000`

### 5. Optional End-to-End Test
```bash
python scripts/test_cycle.py
```

---

## Sample Decision Artifact
```json
{
  "type": "META_DECISION",
  "pair": "XBTUSD",
  "votes": [
    {
      "agent_name": "TrendAgent",
      "direction": "SELL",
      "confidence": 100,
      "reason": "Bearish crossover: SMA10 < SMA30"
    }
  ],
  "decision": {
    "decision": "SELL",
    "reason": "MOMENTUM TRIGGER: TrendAgent SELL at 100% for 3 consecutive cycles."
  },
  "cycle_timestamp": "2026-04-13 12:15:00"
}
```

---

## Notes
- Use Kraken paper mode during testing.
- Keep Kraken withdraw permissions disabled.
- If contracts are already deployed, do not change deployed addresses.
