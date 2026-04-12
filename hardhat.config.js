require('@nomicfoundation/hardhat-toolbox');
require('dotenv').config();

// Ensure private key has 0x prefix (MetaMask exports without it)
function getPrivateKey() {
  const key = process.env.PRIVATE_KEY || '';
  if (key.length === 64) return '0x' + key;       // 64 hex chars without prefix
  if (key.length === 66 && key.startsWith('0x')) return key;  // Already prefixed
  console.warn('[WARN] PRIVATE_KEY not set or invalid. Using Hardhat default (local only).');
  return '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80';
}

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: '0.8.20',
  networks: {
    baseSepolia: {
      url: `https://base-sepolia.g.alchemy.com/v2/${process.env.ALCHEMY_API_KEY || ''}`,
      accounts: [getPrivateKey()]
    }
  }
};
