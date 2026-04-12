const { ethers } = require('hardhat');
const fs = require('fs');

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log('Deploying with account:', deployer.address);
  console.log('Account balance:', (await deployer.provider.getBalance(deployer.address)).toString());

  // --- 1. Deploy AgentIdentityRegistry ---
  console.log('\n--- Deploying AgentIdentityRegistry ---');
  const Identity = await ethers.getContractFactory('AgentIdentityRegistry');
  const identity = await Identity.deploy();
  await identity.waitForDeployment();
  const identityAddr = await identity.getAddress();
  console.log('Identity Registry deployed at:', identityAddr);

  // --- 2. Deploy ReputationRegistry ---
  console.log('\n--- Deploying ReputationRegistry ---');
  const Reputation = await ethers.getContractFactory('ReputationRegistry');
  const reputation = await Reputation.deploy();
  await reputation.waitForDeployment();
  const reputationAddr = await reputation.getAddress();
  console.log('Reputation Registry deployed at:', reputationAddr);

  // --- 3. Deploy ValidationRegistry ---
  console.log('\n--- Deploying ValidationRegistry ---');
  const Validation = await ethers.getContractFactory('ValidationRegistry');
  const validation = await Validation.deploy();
  await validation.waitForDeployment();
  const validationAddr = await validation.getAddress();
  console.log('Validation Registry deployed at:', validationAddr);

  // --- 4. Save addresses for Python agents ---
  const addresses = {
    identity: identityAddr,
    reputation: reputationAddr,
    validation: validationAddr,
    network: 'baseSepolia',
    deployedAt: new Date().toISOString(),
    deployer: deployer.address
  };

  fs.writeFileSync('./contract_addresses.json', JSON.stringify(addresses, null, 2));
  console.log('\n[DONE] All contracts deployed!');
  console.log('Addresses saved to contract_addresses.json');
  console.log('\nNext steps:');
  console.log('  1. Copy addresses into your .env file');
  console.log('  2. Verify on https://sepolia.basescan.org');
  console.log('  3. Register agents: npx hardhat run scripts/register_agents.js --network baseSepolia');
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
