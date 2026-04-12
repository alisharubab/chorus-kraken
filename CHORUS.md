## **CHORUS — Multi-Agent Senate**

N specialized agents vote before capital moves

**The idea**: Instead of one agent making all the decisions, you have a small committee of specialized agents — one that follows trends, one that looks for reversals, one that's purely focused on risk, maybe one scanning news. Each one has its own identity and reputation score on-chain. When a trade opportunity comes up, they all vote. The vote is weighted by how well each agent has performed historically. So if the risk sentinel has been right a lot lately, its vote counts more. The final decision and the full vote record get logged as a validation artifact. It's like a decentralized investment committee, but fully automated and fully auditable.

**ERC alignment:** Deploy 3–5 lightweight sub-agents (a trend-follower, a mean-reversion agent, a risk sentinel, a macro news scanner) each with their own ERC-8004 identity and reputation score. Before any trade executes, they submit signed votes through the Risk Router. The **meta-agent tallies votes weighted by each sub-agent's historical Sharpe ratio** on-chain. Minority dissent is logged as a validation artifact.

**Why it wins:** Multi-agent coordination is a hot research area. The on-chain vote record is a genuinely novel trust signal. Very demo-friendly too.

## **CHORUS \+ Kraken**

**How it works**

We deploy 4-5 small AI agents, each with a different personality and job:

* One only looks at **price trends** — is the market going up or down?  
* One looks for **reversals** — is an asset oversold or overbought?  
* One is purely a **risk cop** — is this trade too risky given our current drawdown?  
* One scans **market sentiment** — what's the broader crypto market doing right now?

When a trading opportunity comes up, each agent independently analyzes it and casts a **signed vote** — yes or no, with a confidence score. The votes are weighted by each agent's historical track record. If the risk cop has been right 80% of the time lately, its vote carries more weight than an agent that's been wrong.

The **meta-agent** (the committee chair) tallies the votes, makes the final call, and fires the trade through **Kraken CLI** — a real trading interface that connects directly to Kraken exchange.

**Where ERC-8004 comes in**

Every agent has a registered **on-chain identity** — think of it like a verifiable resume on the blockchain. Every vote, every trade, every risk check gets logged as a **validation artifact** — basically a cryptographically signed receipt that says "this agent made this decision at this time for these reasons."

Over time, each agent builds a **reputation score** based on objective outcomes. Good calls improve your score, bad calls hurt it. Recent mistakes hurt more than old ones. This is all happening transparently on-chain, so anyone — judges, other teams, the public — can audit exactly how our system made every single decision.

**Why this is different from what other teams will build**

Most teams will build a single agent that trades and logs its actions. We're building a **committee with checks and balances**, where the decision-making process itself is the product. The judges are explicitly scoring validation quality, not just PnL — and our system produces richer, more meaningful validation artifacts than any single-agent approach.

**What we each need to build**

* Smart contracts for agent identity, reputation, and vote logging (ERC-8004 layer)  
* The sub-agents themselves with their trading logic (AI layer)  
* Kraken CLI integration for actual trade execution (execution layer)  
* A simple dashboard showing votes, reputation scores, and trade history in real time (demo layer)

**Timeline rough cut**

* Days 1–3: Smart contracts and on-chain identity setup  
* Days 4–8: Sub-agents, voting logic, and reputation scoring  
* Days 9–12: Kraken integration and end-to-end testing  
* Days 13–14: Dashboard, cleanup, and social posts  
  **Full Documentation**

# **0\. How to Use This Document**

This document is written assuming we know basic programming but nothing about crypto, smart contracts, or trading APIs.

Each section is written so either teammate can follow it independently. Sections marked with 🔗 are where our work connects together — those are the moments we need to sync up online.

**Document Structure:**

* Section 1 — Project Overview: What we are building and why

* Section 2 — Architecture: How all the pieces connect

* Section 3 — Environment Setup: Install everything you need

* Section 4 — Smart Contracts (ERC-8004): The blockchain layer

* Section 5 — The Sub-Agents: The AI trading logic

* Section 6 — Voting \+ Meta-Agent: The decision engine

* Section 7 — Kraken CLI Integration: Executing real trades

* Section 8 — Validation Artifacts: Producing on-chain receipts

* Section 9 — Testing End-to-End: Running the whole system

* Section 10 — Submission Guide: How to submit and what to post

* Section 11 — Team Coordination: How to split work remotely

# **1\. Project Overview**

## **1.1 What is CHORUS?**

CHORUS is a multi-agent AI trading system where multiple specialized AI agents collaborate to make trading decisions, and every single decision is recorded on the blockchain permanently and transparently.

Think of it like a company board meeting. Instead of one person deciding whether to buy or sell, a committee of specialists debates the decision, votes, and the vote record is filed permanently so anyone can audit it. Except here, the board members are AI agents, and the filing system is a blockchain.

## **1.2 The Five Agents**

Our system has five agents, each with one job:

| Agent Name | What It Does |
| :---- | :---- |
| Trend Agent | Looks at price history and decides if the market is going up, down, or sideways |
| Reversal Agent | Looks for overbought or oversold conditions — signals that a price is about to reverse |
| Risk Sentinel | Purely focused on protecting capital — votes NO if a trade would risk too much |
| Sentiment Agent | Scans market-wide signals like Bitcoin dominance, fear/greed index, volume spikes |
| Meta-Agent | The committee chair — collects all votes, weighs them by reputation, makes final call |

## **1.3 Why This Wins**

The hackathon judges score three things: risk-adjusted profit, drawdown control, and validation quality. Most teams will build a single agent that trades and logs its trades. We are building a committee with checks and balances, which naturally produces richer, more meaningful on-chain records (validation artifacts). The Risk Sentinel alone means our drawdown should be better than average. And the voting record on-chain is exactly what 'validation quality' means to the judges.

## **1.4 Which Challenges We Are Entering**

* ERC-8004 Challenge: Each agent has a registered on-chain identity and accumulates reputation based on how accurate its votes are.

* Kraken Challenge: The Meta-Agent executes trades through Kraken CLI, so our PnL is tracked on the Kraken leaderboard too.

* We are eligible for prizes from BOTH challenges with a single submission.

# **2\. System Architecture**

## **2.1 The Big Picture**

Here is the full flow of the system from start to finish:

**Step 1 — Market Data Comes In**

Every few minutes (or on a schedule), each sub-agent pulls market data from Kraken and the PRISM API.

**Step 2 — Each Sub-Agent Votes**

Each of the four sub-agents independently analyzes the data and produces a signed vote: BUY, SELL, or HOLD, with a confidence score from 0 to 100\.

**Step 3 — Votes Are Signed and Logged**

Each vote is signed using EIP-712 (a standard for signing typed data on Ethereum) and logged on-chain as a validation artifact.

**Step 4 — Meta-Agent Tallies Votes**

The Meta-Agent collects all four votes and weighs them by each agent's current reputation score. If the Trend Agent has been right 70% of the time recently, its vote counts more than an agent with 40% accuracy.

**Step 5 — Trade Decision**

If the weighted vote clears a threshold (e.g. 60% consensus), the Meta-Agent fires a trade through Kraken CLI. If it doesn't clear the threshold, it logs a HOLD decision and waits.

**Step 6 — Reputation Updates**

After the trade closes (or a time window passes), each agent's vote is evaluated against the actual outcome. Correct votes improve the agent's on-chain reputation score. Incorrect votes reduce it.

## **2.2 Technology Stack**

| Layer | Technology |
| :---- | :---- |
| On-chain identity & reputation | ERC-8004 smart contracts on a testnet (e.g. Base Sepolia or Polygon Mumbai) |
| Vote signing | EIP-712 typed data signatures (standard Ethereum signing) |
| Trade execution | Kraken CLI (command-line tool that talks to Kraken exchange) |
| Market data | Kraken REST API \+ PRISM API (from hackathon partner Strykr) |
| Agent logic | Python (using web3.py for blockchain, requests for APIs) |
| Blockchain network | Base Sepolia testnet (free test funds, fast, cheap) |
| Wallet | MetaMask browser extension \+ a generated agent wallet |
| Development tools | Node.js, Hardhat (for smart contracts), Python 3.10+ |

# **3\. Environment Setup**

Both teammates need to complete this section on their own machines before doing anything else. This is the foundation. Do not skip steps.

## **3.1 Accounts to Create**

Create these accounts before touching any code. They are all free.

1. Kraken Account

Go to kraken.com and create a free account. Complete basic verification (email \+ phone). You do NOT need to deposit real money — we will use Kraken's paper trading sandbox.

2. MetaMask Wallet

Go to metamask.io and install the browser extension. Create a new wallet. IMPORTANT: Write down your 12-word seed phrase on paper and keep it somewhere safe. This is your only way to recover the wallet. Never share it with anyone.

After creating your wallet, go to Settings \> Networks \> Add Network and add the Base Sepolia testnet:

Network Name: Base Sepolia

RPC URL: https://sepolia.base.org

Chain ID: 84532

Currency Symbol: ETH

Block Explorer: https://sepolia.basescan.org

3. Get Free Test ETH

To deploy contracts and sign transactions, you need test ETH (it is fake, has no value, but the blockchain still requires it for fees). Go to the Base Sepolia faucet:

https://www.alchemy.com/faucets/base-sepolia

Connect your MetaMask wallet and request test ETH. You may need to create a free Alchemy account. Request 0.5 ETH — this is more than enough for all our transactions.

4. Alchemy Account (for blockchain connection)

Go to alchemy.com and create a free account. Create a new app, select Base Sepolia as the network. Copy your API key — you will need this later when your Python agents need to talk to the blockchain.

5. PRISM API Key

Go to the Strykr PRISM API documentation (linked in hackathon resources) and register for a free API key. This gives your agents access to cross-asset financial data.

6. GitHub Repository

One teammate creates a private GitHub repository called chorus-kraken. Add the other teammate as a collaborator under Settings \> Collaborators. Both teammates clone the repository to their local machine.

## **3.2 Software to Install**

Install these in order. All are free and open source.

### **Install Node.js**

Go to nodejs.org and download the LTS version (the one labeled 'Recommended for Most Users'). Install it. Verify by opening your terminal and typing:

node \--version

You should see something like v20.x.x. If you see a version number, Node.js is installed correctly.

### **Install Python**

Go to python.org and download Python 3.11 or newer. During installation on Windows, check the box that says 'Add Python to PATH'. Verify:

python \--version

### **Install Hardhat (Smart Contract Development Tool)**

Hardhat is the tool we use to write, test, and deploy Solidity smart contracts. Inside your project folder, run:

npm install \--save-dev hardhat

npx hardhat init

When it asks what type of project, choose 'Create a JavaScript project'. Accept all defaults.

### **Install Python Libraries**

Create a file called requirements.txt in your project with these contents:

web3==6.11.1

eth-account==0.10.0

requests==2.31.0

python-dotenv==1.0.0

schedule==1.2.0

pandas==2.1.0

Then install them all at once:

pip install \-r requirements.txt

### **Install Kraken CLI**

Go to the Kraken CLI GitHub repository (linked in the hackathon resources page). Download the binary for your operating system (Windows, Mac, or Linux). It is a single file — no installation needed, just download it. Put it in your project folder or somewhere on your PATH.

Verify it works:

kraken-cli \--version

## **3.3 Project Folder Structure**

Set up your project folder like this. Create these folders now, even if they are empty:

chorus-kraken/

  contracts/          ← Solidity smart contracts

  agents/             ← Python AI agent files

    trend\_agent.py

    reversal\_agent.py

    risk\_sentinel.py

    sentiment\_agent.py

    meta\_agent.py

  scripts/            ← Deployment and utility scripts

  tests/              ← Contract tests

  artifacts/          ← Generated validation artifact JSONs

  .env                ← Secret keys (NEVER commit this to GitHub)

  requirements.txt

  README.md

**⚠️ Important:** Create a file called .gitignore in your project root and add .env to it. This prevents your secret keys from being accidentally uploaded to GitHub.

## **3.4 Environment Variables**

Create a file called .env in your project root. This file stores all your secret keys. Never share this file or commit it to GitHub.

PRIVATE\_KEY=your\_metamask\_private\_key\_here

ALCHEMY\_API\_KEY=your\_alchemy\_api\_key\_here

KRAKEN\_API\_KEY=your\_kraken\_api\_key\_here

KRAKEN\_API\_SECRET=your\_kraken\_api\_secret\_here

PRISM\_API\_KEY=your\_prism\_api\_key\_here

To get your MetaMask private key: Open MetaMask \> Click the three dots next to your account \> Account Details \> Export Private Key. Enter your MetaMask password. Copy the key into .env.

**⚠️ Important:** Your private key gives full access to your wallet. Only put test wallets with test funds in here. Never use your real wallet private key.

# **4\. Smart Contracts (ERC-8004 Layer)**

Smart contracts are programs that run on the blockchain. Once deployed, they cannot be changed and run automatically. We need three contracts for our system.

## **4.1 What ERC-8004 Actually Is**

ERC-8004 is a standard for giving AI agents a verifiable on-chain identity. Think of it like a passport system for AI agents. Each agent gets a unique ID registered on the blockchain, along with a reputation score that updates over time based on real outcomes.

For our project, we need to implement three registries from the ERC-8004 specification:

* Identity Registry: Registers each agent with a unique ID, wallet address, and metadata

* Reputation Registry: Tracks each agent's score, updated after every trade

* Validation Registry: Stores signed receipts (validation artifacts) for every vote and trade

## **4.2 Contract 1: Agent Identity Registry**

Create a file at contracts/AgentIdentityRegistry.sol with the following code. Read each comment carefully to understand what each part does.

// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

contract AgentIdentityRegistry {

    // Each agent has an AgentRecord stored here

    struct AgentRecord {

        uint256 agentId;      // Unique number for this agent

        address agentWallet;  // Ethereum address the agent signs with

        string name;          // Human-readable name e.g. 'TrendAgent'

        string role;          // Role e.g. 'trend\_follower'

        string metadataURI;   // Link to a JSON file with more details

        bool active;          // Is this agent currently active?

        uint256 registeredAt; // Unix timestamp when registered

    }

    uint256 public nextAgentId \= 1;

    mapping(uint256 \=\> AgentRecord) public agents;

    mapping(address \=\> uint256) public walletToAgentId;

    event AgentRegistered(uint256 indexed agentId, address wallet, string name);

    function registerAgent(

        address \_wallet,

        string memory \_name,

        string memory \_role,

        string memory \_metadataURI

    ) external returns (uint256) {

        uint256 id \= nextAgentId++;

        agents\[id\] \= AgentRecord(id, \_wallet, \_name, \_role, \_metadataURI, true, block.timestamp);

        walletToAgentId\[\_wallet\] \= id;

        emit AgentRegistered(id, \_wallet, \_name);

        return id;

    }

}

## **4.3 Contract 2: Reputation Registry**

Create contracts/ReputationRegistry.sol:

// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

contract ReputationRegistry {

    struct ReputationRecord {

        uint256 agentId;

        int256 score;          // Can go negative if agent is consistently wrong

        uint256 totalVotes;    // How many votes this agent has cast

        uint256 correctVotes;  // How many were correct

        uint256 lastUpdated;

    }

    mapping(uint256 \=\> ReputationRecord) public reputation;

    address public owner;

    event ReputationUpdated(uint256 indexed agentId, int256 newScore);

    constructor() { owner \= msg.sender; }

    modifier onlyOwner() {

        require(msg.sender \== owner, 'Not authorized');

        \_;

    }

    function initAgent(uint256 agentId) external onlyOwner {

        reputation\[agentId\] \= ReputationRecord(agentId, 50, 0, 0, block.timestamp);

    }

    // Call this after each trade resolves

    function updateReputation(uint256 agentId, bool wasCorrect) external onlyOwner {

        ReputationRecord storage r \= reputation\[agentId\];

        r.totalVotes \+= 1;

        if (wasCorrect) {

            r.correctVotes \+= 1;

            r.score \+= 5;  // \+5 for correct prediction

        } else {

            r.score \-= 3;  // \-3 for wrong prediction

        }

        r.lastUpdated \= block.timestamp;

        emit ReputationUpdated(agentId, r.score);

    }

    function getScore(uint256 agentId) external view returns (int256) {

        return reputation\[agentId\].score;

    }

}

## **4.4 Contract 3: Validation Registry**

Create contracts/ValidationRegistry.sol:

// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

contract ValidationRegistry {

    struct ValidationArtifact {

        uint256 artifactId;

        uint256 agentId;

        string artifactType;  // 'VOTE', 'TRADE', 'RISK\_CHECK', 'CHECKPOINT'

        bytes32 dataHash;     // Hash of the full artifact JSON

        uint256 timestamp;

    }

    uint256 public nextArtifactId \= 1;

    mapping(uint256 \=\> ValidationArtifact) public artifacts;

    mapping(uint256 \=\> uint256\[\]) public agentArtifacts; // agentId \-\> list of artifact IDs

    event ArtifactLogged(uint256 indexed artifactId, uint256 indexed agentId, string artifactType);

    function logArtifact(

        uint256 agentId,

        string memory artifactType,

        bytes32 dataHash

    ) external returns (uint256) {

        uint256 id \= nextArtifactId++;

        artifacts\[id\] \= ValidationArtifact(id, agentId, artifactType, dataHash, block.timestamp);

        agentArtifacts\[agentId\].push(id);

        emit ArtifactLogged(id, agentId, artifactType);

        return id;

    }

}

## **4.5 Deploying the Contracts**

Create a deployment script at scripts/deploy.js:

const { ethers } \= require('hardhat');

async function main() {

  const \[deployer\] \= await ethers.getSigners();

  console.log('Deploying with:', deployer.address);

  const Identity \= await ethers.getContractFactory('AgentIdentityRegistry');

  const identity \= await Identity.deploy();

  await identity.waitForDeployment();

  console.log('Identity Registry:', await identity.getAddress());

  const Reputation \= await ethers.getContractFactory('ReputationRegistry');

  const reputation \= await Reputation.deploy();

  await reputation.waitForDeployment();

  console.log('Reputation Registry:', await reputation.getAddress());

  const Validation \= await ethers.getContractFactory('ValidationRegistry');

  const validation \= await Validation.deploy();

  await validation.waitForDeployment();

  console.log('Validation Registry:', await validation.getAddress());

  // Save addresses to a file so Python agents can find them

  const fs \= require('fs');

  fs.writeFileSync('./contract\_addresses.json', JSON.stringify({

    identity: await identity.getAddress(),

    reputation: await reputation.getAddress(),

    validation: await validation.getAddress()

  }, null, 2));

  console.log('Addresses saved to contract\_addresses.json');

}

main().catch(console.error);

Configure Hardhat to use Base Sepolia. In hardhat.config.js, replace the contents with:

require('@nomicfoundation/hardhat-toolbox');

require('dotenv').config();

module.exports \= {

  solidity: '0.8.20',

  networks: {

    baseSepolia: {

      url: \`https://base-sepolia.g.alchemy.com/v2/${process.env.ALCHEMY\_API\_KEY}\`,

      accounts: \[process.env.PRIVATE\_KEY\]

    }

  }

};

Install the required Hardhat plugin:

npm install \--save-dev @nomicfoundation/hardhat-toolbox dotenv

Now deploy:

npx hardhat run scripts/deploy.js \--network baseSepolia

You will see three contract addresses printed in your terminal. These are also saved to contract\_addresses.json. Copy these addresses into your .env file:

IDENTITY\_CONTRACT=0x...

REPUTATION\_CONTRACT=0x...

VALIDATION\_CONTRACT=0x...

**📝 Note:** *You can verify your deployment by going to sepolia.basescan.org and searching for your contract address. If it shows up, you're live on the blockchain.*

# **5\. The Sub-Agents (AI Logic)**

Each sub-agent is a Python file that does one thing: pull market data, analyze it, and produce a vote. Every agent follows the same structure so they are easy to understand and extend.

## **5.1 Shared Utilities**

Create agents/utils.py — this file is used by all agents:

import json, hashlib, os, requests

from web3 import Web3

from eth\_account import Account

from eth\_account.messages import encode\_defunct

from dotenv import load\_dotenv

load\_dotenv()

\# Connect to Base Sepolia blockchain

w3 \= Web3(Web3.HTTPProvider(

    f"https://base-sepolia.g.alchemy.com/v2/{os.getenv('ALCHEMY\_API\_KEY')}"

))

\# Load contract addresses

with open('contract\_addresses.json') as f:

    CONTRACTS \= json.load(f)

def get\_kraken\_price(pair='XBTUSD'):

    """Fetch current price from Kraken REST API"""

    url \= f'https://api.kraken.com/0/public/Ticker?pair={pair}'

    r \= requests.get(url).json()

    \# Kraken returns the last trade price inside result\[pair\]\[c\]\[0\]

    key \= list(r\['result'\].keys())\[0\]

    return float(r\['result'\]\[key\]\['c'\]\[0\])

def get\_kraken\_ohlcv(pair='XBTUSD', interval=60):

    """Fetch hourly OHLCV candles from Kraken"""

    url \= f'https://api.kraken.com/0/public/OHLC?pair={pair}\&interval={interval}'

    r \= requests.get(url).json()

    key \= list(r\['result'\].keys())\[0\]

    candles \= r\['result'\]\[key\]

    \# Each candle: \[time, open, high, low, close, vwap, volume, count\]

    return candles

def sign\_vote(vote\_data: dict, private\_key: str) \-\> str:

    """Sign a vote dict and return the signature"""

    msg \= json.dumps(vote\_data, sort\_keys=True)

    msg\_hash \= encode\_defunct(text=msg)

    signed \= Account.sign\_message(msg\_hash, private\_key=private\_key)

    return signed.signature.hex()

def hash\_artifact(artifact: dict) \-\> str:

    """Create a deterministic hash of an artifact for on-chain logging"""

    content \= json.dumps(artifact, sort\_keys=True)

    return hashlib.sha256(content.encode()).hexdigest()

## **5.2 The Trend Agent**

Create agents/trend\_agent.py. This agent uses a simple moving average crossover — when the 10-period moving average crosses above the 30-period moving average, it signals BUY. When it crosses below, it signals SELL.

import os, json, time

from utils import get\_kraken\_ohlcv, sign\_vote, hash\_artifact

from dotenv import load\_dotenv

load\_dotenv()

AGENT\_ID \= 1  \# Set after registering on-chain

PRIVATE\_KEY \= os.getenv('PRIVATE\_KEY')

def compute\_sma(candles, period):

    """Simple Moving Average: average of the last N closing prices"""

    closes \= \[float(c\[4\]) for c in candles\[-period:\]\]

    return sum(closes) / len(closes)

def analyze(pair='XBTUSD') \-\> dict:

    candles \= get\_kraken\_ohlcv(pair=pair, interval=60)

    sma\_10 \= compute\_sma(candles, 10\)

    sma\_30 \= compute\_sma(candles, 30\)

    if sma\_10 \> sma\_30 \* 1.002:  \# 10-period above 30-period by 0.2%

        direction \= 'BUY'

        confidence \= min(100, int((sma\_10 / sma\_30 \- 1\) \* 10000))

    elif sma\_10 \< sma\_30 \* 0.998:

        direction \= 'SELL'

        confidence \= min(100, int((1 \- sma\_10 / sma\_30) \* 10000))

    else:

        direction \= 'HOLD'

        confidence \= 50

    vote \= {

        'agent\_id': AGENT\_ID,

        'agent\_name': 'TrendAgent',

        'pair': pair,

        'direction': direction,

        'confidence': confidence,

        'sma\_10': round(sma\_10, 2),

        'sma\_30': round(sma\_30, 2),

        'timestamp': int(time.time())

    }

    vote\['signature'\] \= sign\_vote(vote, PRIVATE\_KEY)

    return vote

if \_\_name\_\_ \== '\_\_main\_\_':

    result \= analyze()

    print(json.dumps(result, indent=2))

## **5.3 The Risk Sentinel**

Create agents/risk\_sentinel.py. This is the most important agent — it acts as a veto. If the potential loss exceeds our daily limit, it always votes HOLD regardless of what other agents say.

import os, json, time

from utils import get\_kraken\_price, sign\_vote

from dotenv import load\_dotenv

load\_dotenv()

AGENT\_ID \= 3

PRIVATE\_KEY \= os.getenv('PRIVATE\_KEY')

MAX\_DAILY\_LOSS\_PERCENT \= 2.0   \# Stop trading if down 2% today

MAX\_POSITION\_SIZE \= 0.10       \# Never use more than 10% of capital in one trade

\# In a real system this would come from your actual account balance

\# For sandbox, we track it in a local file

def get\_daily\_pnl():

    try:

        with open('daily\_pnl.json') as f:

            return json.load(f).get('pnl\_percent', 0.0)

    except:

        return 0.0

def analyze(pair='XBTUSD') \-\> dict:

    daily\_pnl \= get\_daily\_pnl()

    if daily\_pnl \< \-MAX\_DAILY\_LOSS\_PERCENT:

        direction \= 'HOLD'

        reason \= f'Daily loss limit hit: {daily\_pnl:.2f}%'

        confidence \= 100  \# Very confident we should not trade

    else:

        direction \= 'PROCEED'  \# Not a veto

        reason \= f'Risk OK. Daily PnL: {daily\_pnl:.2f}%'

        confidence \= 80

    vote \= {

        'agent\_id': AGENT\_ID,

        'agent\_name': 'RiskSentinel',

        'pair': pair,

        'direction': direction,

        'confidence': confidence,

        'reason': reason,

        'daily\_pnl': daily\_pnl,

        'timestamp': int(time.time())

    }

    vote\['signature'\] \= sign\_vote(vote, PRIVATE\_KEY)

    return vote

Build the Reversal Agent and Sentiment Agent following the same template. The Reversal Agent should use RSI (Relative Strength Index) — RSI above 70 \= overbought \= SELL, RSI below 30 \= oversold \= BUY. The Sentiment Agent can use Bitcoin dominance from the PRISM API and the Kraken volume data.

**📝 Note:** *For the hackathon, having two fully working agents (Trend \+ Risk) and two simpler ones is better than having all four broken. Focus on Trend and Risk first.*

# **6\. The Meta-Agent (Voting \+ Decision Engine)**

The Meta-Agent is the brain of CHORUS. It collects votes from all sub-agents, weighs them by reputation, and decides whether to fire a trade or hold.

## **6.1 How Vote Weighting Works**

Every sub-agent starts with a reputation score of 50 out of 100\. The Meta-Agent fetches the current score for each agent from the on-chain Reputation Registry, then weighs each vote proportionally.

Example: If Trend Agent has score 70 and Reversal Agent has score 30, and both vote BUY with 80% confidence, the weighted BUY signal is: (70×80 \+ 30×80) / (70+30) \= 80\. But if Trend votes BUY at 80% and Reversal votes SELL at 80%, the net signal is: (70×80 \- 30×80) / 100 \= 32 — a weak BUY that probably doesn't clear the threshold.

## **6.2 Meta-Agent Code**

Create agents/meta\_agent.py:

import os, json, time, subprocess

from web3 import Web3

from utils import w3, CONTRACTS, hash\_artifact

from dotenv import load\_dotenv

load\_dotenv()

\# Load ABIs (simplified — just the functions we need)

REPUTATION\_ABI \= \[

    {'inputs': \[{'name': 'agentId', 'type': 'uint256'}\],

     'name': 'getScore', 'outputs': \[{'name': '', 'type': 'int256'}\],

     'stateMutability': 'view', 'type': 'function'}

\]

reputation\_contract \= w3.eth.contract(

    address=CONTRACTS\['reputation'\],

    abi=REPUTATION\_ABI

)

TRADE\_THRESHOLD \= 60  \# Need 60% weighted signal to execute a trade

RISK\_VETO\_ID \= 3      \# Agent ID of the Risk Sentinel

def get\_reputation\_score(agent\_id: int) \-\> int:

    score \= reputation\_contract.functions.getScore(agent\_id).call()

    return max(1, int(score))  \# Minimum weight of 1

def tally\_votes(votes: list) \-\> dict:

    \# First check for Risk Sentinel veto

    for v in votes:

        if v\['agent\_id'\] \== RISK\_VETO\_ID and v\['direction'\] \== 'HOLD':

            return {'decision': 'HOLD', 'reason': 'Risk Sentinel veto', 'signal': 0}

    buy\_weight \= 0

    sell\_weight \= 0

    total\_weight \= 0

    for v in votes:

        if v\['agent\_id'\] \== RISK\_VETO\_ID:

            continue  \# Skip risk sentinel in normal tally

        rep \= get\_reputation\_score(v\['agent\_id'\])

        weight \= rep \* v\['confidence'\] / 100

        total\_weight \+= rep

        if v\['direction'\] \== 'BUY':

            buy\_weight \+= weight

        elif v\['direction'\] \== 'SELL':

            sell\_weight \+= weight

    if total\_weight \== 0:

        return {'decision': 'HOLD', 'reason': 'No valid votes', 'signal': 0}

    buy\_pct \= (buy\_weight / total\_weight) \* 100

    sell\_pct \= (sell\_weight / total\_weight) \* 100

    if buy\_pct \>= TRADE\_THRESHOLD:

        return {'decision': 'BUY', 'signal': round(buy\_pct), 'reason': f'BUY consensus {buy\_pct:.1f}%'}

    elif sell\_pct \>= TRADE\_THRESHOLD:

        return {'decision': 'SELL', 'signal': round(sell\_pct), 'reason': f'SELL consensus {sell\_pct:.1f}%'}

    else:

        return {'decision': 'HOLD', 'signal': 0, 'reason': f'No consensus. BUY:{buy\_pct:.1f}% SELL:{sell\_pct:.1f}%'}

def run\_cycle(pair='XBTUSD'):

    print(f'\\n--- CHORUS Cycle at {time.strftime("%H:%M:%S")} \---')

    \# Import and run each agent

    from trend\_agent import analyze as trend\_analyze

    from risk\_sentinel import analyze as risk\_analyze

    \# Add reversal and sentiment agents when ready

    votes \= \[

        trend\_analyze(pair),

        risk\_analyze(pair),

    \]

    print('Votes collected:')

    for v in votes: print(f'  {v\["agent\_name"\]}: {v\["direction"\]} ({v\["confidence"\]}%)')

    result \= tally\_votes(votes)

    print(f'Decision: {result\["decision"\]} | Reason: {result\["reason"\]}')

    \# Log this decision cycle to a file (will be sent on-chain in section 8\)

    artifact \= {

        'type': 'META\_DECISION',

        'pair': pair,

        'votes': votes,

        'decision': result,

        'timestamp': int(time.time())

    }

    with open(f'artifacts/decision\_{int(time.time())}.json', 'w') as f:

        json.dump(artifact, f, indent=2)

    \# If decision is BUY or SELL, send to Kraken (Section 7\)

    if result\['decision'\] in \['BUY', 'SELL'\]:

        execute\_trade(pair, result\['decision'\])

    return result

def execute\_trade(pair, direction):

    """This calls the Kraken CLI \- see Section 7"""

    print(f'Sending {direction} order for {pair} via Kraken CLI...')

    \# Implementation in Section 7

    pass

if \_\_name\_\_ \== '\_\_main\_\_':

    \# Run one cycle immediately, then every 15 minutes

    import schedule

    run\_cycle()

    schedule.every(15).minutes.do(run\_cycle)

    while True:

        schedule.run\_pending()

        time.sleep(60)

# **7\. Kraken CLI Integration**

Kraken CLI is how our agent actually executes trades on the Kraken exchange. It is a command-line tool, meaning we control it by running terminal commands from our Python code.

## **7.1 Setting Up Your Kraken API Key**

7. Log into your Kraken account at kraken.com

8. Go to Settings \> API (or Security \> API)

9. Click 'Create API Key'

10. Give it a name like 'chorus-agent'

11. Under permissions, enable: Query Funds, Query Open Orders, Query Closed Orders, Create & Modify Orders

12. Do NOT enable Withdraw Funds — we never need that

13. Copy both the API Key and API Secret into your .env file

## **7.2 Configuring Kraken CLI**

Kraken CLI reads your API credentials from a config file. Create a file at \~/.kraken/config.toml (create the .kraken folder in your home directory if it does not exist):

\[auth\]

api\_key \= "your\_api\_key\_here"

api\_secret \= "your\_api\_secret\_here"

Test your connection:

kraken-cli account balance

If it returns your account balance (even $0 is fine), you are connected correctly.

## **7.3 Kraken CLI Commands You Will Use**

| What You Want To Do | Kraken CLI Command |
| :---- | :---- |
| Check your balance | kraken-cli account balance |
| Get current BTC price | kraken-cli market ticker \--pair XBTUSD |
| Place a paper trade BUY | kraken-cli order create \--type buy \--pair XBTUSD \--volume 0.001 |
| Place a paper trade SELL | kraken-cli order create \--type sell \--pair XBTUSD \--volume 0.001 |
| List open orders | kraken-cli order list \--open |
| Cancel an order | kraken-cli order cancel \--txid ORDER\_ID |
| View trade history | kraken-cli order history |

**📝 Note:** *Start with \--volume 0.001 (0.001 BTC is about $60-90 at current prices). Small volumes mean small losses if something goes wrong during testing.*

## **7.4 Calling Kraken CLI From Python**

Python can run terminal commands using the subprocess module. Update the execute\_trade function in meta\_agent.py:

import subprocess, json

def execute\_trade(pair, direction):

    volume \= '0.001'  \# Start small during testing

    order\_type \= 'buy' if direction \== 'BUY' else 'sell'

    cmd \= \[

        'kraken-cli', 'order', 'create',

        '--type', order\_type,

        '--pair', pair,

        '--volume', volume,

        '--output', 'json'  \# Get response as JSON

    \]

    try:

        result \= subprocess.run(cmd, capture\_output=True, text=True, timeout=30)

        response \= json.loads(result.stdout)

        print(f'Order placed: {response}')

        return response

    except subprocess.TimeoutExpired:

        print('Kraken CLI timed out')

        return None

    except Exception as e:

        print(f'Trade execution error: {e}')

        return None

## **7.5 Using Paper Trading Mode**

Kraken has a built-in paper trading (demo) mode so you can test without risking real money. The Kraken CLI sandbox runs against this automatically. To confirm you are in paper trading mode, check your Kraken account on the website — there should be a 'Demo' toggle in the trading interface.

**⚠️ Important:** During the hackathon, confirm whether the organizers want real trades or paper trades. The ERC-8004 challenge uses the hackathon sandbox vault. Only switch to real trades if explicitly required and after thorough testing.

# **8\. Validation Artifacts**

Validation artifacts are the receipts our system produces for every important action. The judges explicitly score 'validation quality' — this is our chance to shine over other teams who just log trades.

## **8.1 What to Log and When**

| Artifact Type | When to Create It |
| :---- | :---- |
| VOTE | Every time a sub-agent produces a vote |
| META\_DECISION | Every time the Meta-Agent tallies votes and decides |
| TRADE\_INTENT | Right before a trade is sent to Kraken |
| TRADE\_CONFIRMED | After Kraken confirms the order |
| RISK\_CHECK | Every time Risk Sentinel runs (even if it says PROCEED) |
| REPUTATION\_UPDATE | After each trade resolves and reputation is updated |

## **8.2 Logging Artifacts On-Chain**

Create agents/artifact\_logger.py:

import os, json

from web3 import Web3

from eth\_account import Account

from utils import w3, CONTRACTS, hash\_artifact

from dotenv import load\_dotenv

load\_dotenv()

VALIDATION\_ABI \= \[

    {'inputs': \[

        {'name': 'agentId', 'type': 'uint256'},

        {'name': 'artifactType', 'type': 'string'},

        {'name': 'dataHash', 'type': 'bytes32'}

     \],

     'name': 'logArtifact',

     'outputs': \[{'name': '', 'type': 'uint256'}\],

     'stateMutability': 'nonpayable', 'type': 'function'}

\]

validation\_contract \= w3.eth.contract(

    address=CONTRACTS\['validation'\],

    abi=VALIDATION\_ABI

)

def log\_artifact\_onchain(agent\_id: int, artifact\_type: str, artifact\_data: dict):

    \# 1\. Save the full artifact to a local JSON file

    filename \= f'artifacts/{artifact\_type}\_{int(time.time())}\_{agent\_id}.json'

    with open(filename, 'w') as f:

        json.dump(artifact\_data, f, indent=2)

    \# 2\. Hash the artifact

    h \= hash\_artifact(artifact\_data)

    data\_hash \= bytes.fromhex(h)\[:32\]  \# bytes32 for contract

    \# 3\. Send the hash to the on-chain registry

    account \= Account.from\_key(os.getenv('PRIVATE\_KEY'))

    nonce \= w3.eth.get\_transaction\_count(account.address)

    txn \= validation\_contract.functions.logArtifact(

        agent\_id, artifact\_type, data\_hash

    ).build\_transaction({

        'from': account.address,

        'nonce': nonce,

        'gas': 200000,

        'gasPrice': w3.eth.gas\_price

    })

    signed \= account.sign\_transaction(txn)

    tx\_hash \= w3.eth.send\_raw\_transaction(signed.raw\_transaction)

    receipt \= w3.eth.wait\_for\_transaction\_receipt(tx\_hash)

    print(f'Artifact logged on-chain. TX: {tx\_hash.hex()}')

    return tx\_hash.hex()

**📝 Note:** *Every on-chain transaction costs a tiny amount of test ETH (gas). With 0.5 test ETH you can log hundreds of artifacts. If you run low, get more from the faucet.*

# **9\. Testing End-to-End**

Before submitting, run the full system and verify every part works. Follow this checklist in order.

## **9.1 Test Checklist**

**Phase 1: Contracts (Day 3-4)**

14. Deploy contracts to Base Sepolia and verify addresses show up on sepolia.basescan.org

15. Call registerAgent for each of the 4 sub-agents and confirm the transaction succeeds

16. Call initAgent for each agent in the Reputation Registry (sets starting score to 50\)

17. Call logArtifact manually with a test artifact and verify it appears on-chain

**Phase 2: Individual Agents (Day 5-7)**

18. Run trend\_agent.py directly and verify it prints a vote with a signature

19. Run risk\_sentinel.py directly and verify it correctly vetoes when daily loss exceeds 2%

20. Run each agent with fake data to confirm the logic works before connecting to live data

**Phase 3: Voting System (Day 8-9)**

21. Run meta\_agent.py and confirm it collects votes from both agents

22. Manually set different reputation scores and confirm the weighting changes the output

23. Confirm the Risk Sentinel veto works — set daily PnL to \-3% and verify decision is always HOLD

**Phase 4: Kraken Integration (Day 10-11)**

24. Run kraken-cli account balance and confirm connection

25. Manually trigger execute\_trade('XBTUSD', 'BUY') and confirm the order appears in Kraken

26. Run a full cycle in meta\_agent.py and confirm it goes all the way to a Kraken order

**Phase 5: End-to-End (Day 12-13)**

27. Run meta\_agent.py for 1 hour and watch it cycle every 15 minutes

28. Verify artifacts are being created in the artifacts/ folder after each cycle

29. Verify artifact hashes are being logged on-chain (check sepolia.basescan.org)

30. Verify reputation is updating after trades resolve

# **10\. Submission Guide**

## **10.1 What to Submit**

The hackathon requires you to submit at early.surge.xyz (credentials are in the hackathon description). You will need:

* Your GitHub repository link (make it public before submitting)

* Your Kraken read-only API key (for leaderboard verification — this is read-only, no risk)

* Your deployed contract addresses on Base Sepolia

* A short project description (use the CHORUS explanation from earlier in this doc)

* Links to your social posts (for the social engagement score)

## **10.2 Your README Must Include**

Write a clear README.md in your GitHub repo with:

31. What CHORUS is (2-3 sentences)

32. How the voting system works

33. Your deployed contract addresses

34. How to run the system locally (installation \+ commands)

35. A sample validation artifact JSON

36. Link to your social posts

## **10.3 Social Engagement**

This is a separately scored category — do not skip it. You need public posts on Twitter/X, YouTube, or a blog throughout the competition. Tag @krakenfx, @lablabai, and @Surgexyz\_.

Post ideas (one per day or every other day):

* Day 1-2: 'We are building a multi-agent AI trading system for the @krakenfx x @lablabai hackathon. Each agent votes before a trade fires. Here is how it works...' (with a diagram)

* Day 4: 'Just deployed our first smart contracts on Base Sepolia — 4 AI agents now have on-chain identities and reputation scores. Here is the contract address...'

* Day 7: 'The Risk Sentinel just vetoed a trade. Daily drawdown hit 2% so it overruled the other 3 agents. This is exactly how trust works in AI finance.'

* Day 10: 'First live vote: Trend Agent BUY 74%, Reversal Agent HOLD 50%, Risk Sentinel PROCEED. Weighted result: BUY at 63%. Order fired through Kraken CLI.'

* Day 14: 'Final submission for CHORUS — a multi-agent AI trading committee where every vote is signed, every decision is on-chain, and reputation scores evolve with every trade.'

# **11\. Team Coordination (Working Remotely)**

## **11.1 How to Split the Work**

| Role | Responsibility | Who Does It |
| :---- | :---- | :---- |
| Smart Contracts \+ ERC-8004 | Deploy identity registry, reputation contracts, write Solidity | Teammate A (or split) |
| AI Sub-Agents \+ Voting Logic | Python agents that analyze market data and produce votes | Teammate B (or split) |
| Kraken CLI Integration | Connect agents to Kraken API for live trade execution | Either |
| Dashboard (Optional) | Simple web page showing votes, trades, reputation scores | Either |
| Social Posts | Tweet/post build progress daily for social engagement score | Both |

## **11.2 The Three Sync Points (🔗 Where Your Work Connects)**

You only need to actively coordinate at three moments. Everything else can be done independently.

**🔗 Sync Point 1 — After Contracts Are Deployed (Day 3-4)**

One teammate deploys the contracts and shares the contract\_addresses.json file with the other. Both teammates put the addresses in their .env files. After this sync, both can work independently again.

**🔗 Sync Point 2 — Connecting Agents to Contracts (Day 8-9)**

When the voting system is ready, both teammates run it together to verify that on-chain reputation updates are actually happening. One person watches the terminal output, the other watches sepolia.basescan.org to confirm transactions appear.

**🔗 Sync Point 3 — End-to-End Test (Day 12-13)**

Both teammates run the full system together for at least one full cycle, verify a Kraken order fires, and confirm the artifact is logged on-chain. This is your final integration test before submission.

## **11.3 Shared Tools**

* Code: GitHub repository (both push and pull regularly)

* Communication: WhatsApp for quick questions

* Shared secrets: Use the same .env values — share the contract addresses and Alchemy key so both can talk to the blockchain. Each teammate uses their own Kraken API key.

* Artifact folder: Commit the artifacts/ folder to GitHub so both can see validation artifacts generated during testing

## **11.4 If You Get Stuck**

**Blockchain/Solidity issues:**

* Check sepolia.basescan.org for failed transactions (they show the revert reason)

* Use Remix IDE (remix.ethereum.org) to test contracts in your browser with no setup

* Hardhat errors are usually missing dependencies — run npm install again

**Python/Agent issues:**

* Run each agent file directly (python trend\_agent.py) before wiring everything together

* Use print() liberally — print every vote, every API response, every decision

* If Kraken API returns errors, check their status page at status.kraken.com

**Kraken CLI issues:**

* Run kraken-cli \--help for a full list of available commands

* Check the official Kraken CLI GitHub repository for up-to-date command syntax

* If authentication fails, regenerate your API key in the Kraken dashboard

**Good luck. Build something real.**

*CHORUS — where every vote is on-chain and every agent earns its reputation.*

