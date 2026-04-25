const hre = require("hardhat");

async function main() {
  const Factory = await hre.ethers.getContractFactory("AdhahiSupplyChain");
  const contract = await Factory.deploy();
  await contract.waitForDeployment();
  const address = await contract.getAddress();
  console.log("AdhahiSupplyChain deployed to:", address);
  console.log("Network:", hre.network.name);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
