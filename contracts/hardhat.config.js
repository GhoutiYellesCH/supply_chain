require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

const { SEPOLIA_RPC_URL, PRIVATE_KEY } = process.env;

// A valid Ethereum private key is exactly 32 bytes = 64 hex chars
// (optionally prefixed with 0x). Anything else (empty, placeholder, wrong
// length) → we skip wiring up the sepolia network so `compile` / `test`
// still work locally without a real key.
function isValidPrivateKey(pk) {
  if (!pk) return false;
  const cleaned = pk.startsWith("0x") ? pk.slice(2) : pk;
  return /^[0-9a-fA-F]{64}$/.test(cleaned);
}

const networks = { hardhat: {} };

if (SEPOLIA_RPC_URL && isValidPrivateKey(PRIVATE_KEY)) {
  networks.sepolia = {
    url: SEPOLIA_RPC_URL,
    accounts: [PRIVATE_KEY.startsWith("0x") ? PRIVATE_KEY : "0x" + PRIVATE_KEY],
  };
} else if (SEPOLIA_RPC_URL || PRIVATE_KEY) {
  console.warn(
    "[hardhat] sepolia network NOT configured — set SEPOLIA_RPC_URL and a valid 64-hex PRIVATE_KEY in .env to enable it."
  );
}

module.exports = {
  solidity: {
    version: "0.8.20",
    settings: { optimizer: { enabled: true, runs: 200 } },
  },
  networks,
};
