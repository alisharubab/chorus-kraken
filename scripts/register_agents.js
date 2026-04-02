/**
 * Register all 4 sub-agents on-chain and initialize their reputation scores.
 * Run AFTER deploy.js has been executed and contract_addresses.json exists.
 *
 * Usage: npx hardhat run scripts/register_agents.js --network baseSepolia
 */
const { ethers } = require('hardhat');
const fs = require('fs');

async function main() {
  const [deployer] = await ethers.getSigners();
  const addresses = JSON.parse(fs.readFileSync('./contract_addresses.json', 'utf8'));

  // --- Load deployed contracts ---
  const Identity = await ethers.getContractAt('AgentIdentityRegistry', addresses.identity);
  const Reputation = await ethers.getContractAt('ReputationRegistry', addresses.reputation);

  // --- Define our 4 agents ---
  const agents = [
    { name: 'TrendAgent',     role: 'trend_follower',     metadataURI: 'ipfs://chorus/trend' },
    { name: 'ReversalAgent',  role: 'mean_reversion',     metadataURI: 'ipfs://chorus/reversal' },
    { name: 'RiskSentinel',   role: 'risk_sentinel',      metadataURI: 'ipfs://chorus/risk' },
    { name: 'SentimentAgent', role: 'sentiment_scanner',  metadataURI: 'ipfs://chorus/sentiment' },
  ];

  console.log('Registering agents with wallet:', deployer.address);
  console.log('');

  for (let i = 0; i < agents.length; i++) {
    const a = agents[i];
    const expectedId = i + 1;

    // Register identity
    console.log(`--- Registering ${a.name} (expected ID: ${expectedId}) ---`);
    const regTx = await Identity.registerAgent(deployer.address, a.name, a.role, a.metadataURI);
    await regTx.wait();
    console.log(`  [OK] Identity registered. TX: ${regTx.hash}`);

    // Initialize reputation to 50
    const repTx = await Reputation.initAgent(expectedId);
    await repTx.wait();
    console.log(`  [OK] Reputation initialized (score=50). TX: ${repTx.hash}`);
    console.log('');
  }

  console.log('[DONE] All 4 agents registered and initialized!');
  console.log('Agent IDs: TrendAgent=1, ReversalAgent=2, RiskSentinel=3, SentimentAgent=4');
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
