const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("AdhahiSupplyChain", function () {
  let contract, owner, other;

  beforeEach(async () => {
    [owner, other] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("AdhahiSupplyChain");
    contract = await Factory.deploy();
  });

  it("anchors a registration hash and verifies it", async () => {
    const h = ethers.keccak256(ethers.toUtf8Bytes("sheep-1"));
    await expect(contract.registerSheep(h))
      .to.emit(contract, "SheepRegistered");
    expect(await contract.verifyEvent(h)).to.equal(true);
  });

  it("rejects duplicate hashes", async () => {
    const h = ethers.keccak256(ethers.toUtf8Bytes("dup"));
    await contract.addEvent(h);
    await expect(contract.addEvent(h)).to.be.revertedWith("Hash already anchored");
  });

  it("returns false for unknown hash", async () => {
    const h = ethers.keccak256(ethers.toUtf8Bytes("nope"));
    expect(await contract.verifyEvent(h)).to.equal(false);
  });
});
