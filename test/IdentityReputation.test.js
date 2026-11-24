const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("IdentityReputation Baseline Tests (Phase 0)", function () {
  let identityReputation;
  let owner;
  let user1;
  let user2;
  let user3;

  beforeEach(async function () {
    [owner, user1, user2, user3] = await ethers.getSigners();
    const IdentityReputationFactory = await ethers.getContractFactory("IdentityReputation");
    identityReputation = await IdentityReputationFactory.deploy();
    await identityReputation.waitForDeployment();
  });

  describe("Deployment & Initial State", function () {
    it("should set deployer as owner", async function () {
      expect(await identityReputation.owner()).to.equal(owner.address);
    });

    it("should verify owner as institution by default", async function () {
      const [isVerified, role] = await identityReputation.isVerifiedIssuer(owner.address);
      expect(isVerified).to.be.true;
      expect(role).to.equal(3); // IssuerRole.VerifiedInstitution
    });

    it("should initialize totalIdentities to 0", async function () {
      expect(await identityReputation.totalIdentities()).to.equal(0);
    });
  });

  describe("Identity Management", function () {
    it("should allow a user to create an identity", async function () {
      const ipfsHash = "QmTestHash1234567890abcdef";
      await expect(identityReputation.connect(user1).createIdentity(ipfsHash))
        .to.emit(identityReputation, "IdentityCreated");

      const [storedHash, rep, createdAt, lastActivity, endorsements, exists] =
        await identityReputation.getIdentity(user1.address);

      expect(exists).to.be.true;
      expect(storedHash).to.equal(ipfsHash);
      expect(rep).to.equal(0);
      expect(endorsements).to.equal(0);
      expect(await identityReputation.totalIdentities()).to.equal(1);
    });

    it("should reject empty IPFS hash", async function () {
      await expect(
        identityReputation.connect(user1).createIdentity("")
      ).to.be.revertedWith("IPFS hash cannot be empty");
    });

    it("should prevent duplicate identity creation for the same address", async function () {
      await identityReputation.connect(user1).createIdentity("QmFirstHash");
      await expect(
        identityReputation.connect(user1).createIdentity("QmSecondHash")
      ).to.be.revertedWith("Identity already exists");
    });

    it("should allow identity update by owner", async function () {
      await identityReputation.connect(user1).createIdentity("QmInitial");
      await expect(identityReputation.connect(user1).updateIdentity("QmUpdated"))
        .to.emit(identityReputation, "IdentityUpdated")
        .withArgs(user1.address, "QmUpdated");

      const [storedHash] = await identityReputation.getIdentity(user1.address);
      expect(storedHash).to.equal("QmUpdated");
    });
  });

  describe("Endorsements & Reputation (and Vulnerability Proofs)", function () {
    beforeEach(async function () {
      await identityReputation.connect(user1).createIdentity("QmUser1");
      await identityReputation.connect(user2).createIdentity("QmUser2");
    });

    it("should allow one identity to endorse another", async function () {
      await expect(
        identityReputation.connect(user1).mintEndorsement(user2.address, 5, 5, "QmMessage")
      )
        .to.emit(identityReputation, "EndorsementMinted")
        .and.to.emit(identityReputation, "ReputationUpdated");

      const [, rep, , , endorsements] = await identityReputation.getIdentity(user2.address);
      expect(rep).to.equal(5);
      expect(endorsements).to.equal(1);
    });

    it("should prevent self-endorsement", async function () {
      await expect(
        identityReputation.connect(user1).mintEndorsement(user1.address, 5, 5, "QmSelf")
      ).to.be.revertedWith("Cannot endorse yourself");
    });

    it("VULNERABILITY PROOF: allows repeated endorsements to inflate reputation (Reputation Spam)", async function () {
      // User1 endorses user2 10 times in a row without restriction
      for (let i = 0; i < 10; i++) {
        await identityReputation.connect(user1).mintEndorsement(user2.address, 10, 5, "QmSpam");
      }
      const [, rep, , , endorsements] = await identityReputation.getIdentity(user2.address);
      expect(rep).to.equal(100);
      expect(endorsements).to.equal(10);
    });
  });

  describe("Issuer Role Management", function () {
    beforeEach(async function () {
      await identityReputation.connect(user1).createIdentity("QmUser1");
    });

    it("should allow contract owner to verify issuer", async function () {
      await expect(identityReputation.connect(owner).verifyIssuer(user1.address, 1))
        .to.emit(identityReputation, "IssuerVerified")
        .withArgs(user1.address, 1);

      const [isVerified, role] = await identityReputation.isVerifiedIssuer(user1.address);
      expect(isVerified).to.be.true;
      expect(role).to.equal(1); // Organization
    });

    it("should reject non-owner verifying an issuer", async function () {
      await expect(
        identityReputation.connect(user2).verifyIssuer(user1.address, 1)
      ).to.be.revertedWith("Not authorized");
    });

    it("DEFECT PROOF: revokeIssuer resets verified flag but fails to reset issuerRoles in storage", async function () {
      await identityReputation.connect(owner).verifyIssuer(user1.address, 1);
      await identityReputation.connect(owner).revokeIssuer(user1.address);

      const [isVerified, role] = await identityReputation.isVerifiedIssuer(user1.address);
      expect(isVerified).to.be.false;
      // In IdentityReputation.sol line 241, revokeIssuer only updates verifiedIssuers[issuer] = false
      // and emits IssuerVerified(issuer, Individual), but fails to update issuerRoles[issuer] in storage!
      expect(role).to.equal(1); // Still 1 (Organization) in storage due to defect
    });
  });

  describe("Sybil Resistance Metric (and Vulnerability Proof)", function () {
    it("VULNERABILITY PROOF: calculates wallet age from contract creation instead of actual on-chain wallet history", async function () {
      await identityReputation.connect(user1).createIdentity("QmUser1");
      const [hasId, meetsWalletAge, hasEndorsements, score] =
        await identityReputation.getSybilResistanceScore(user1.address);

      expect(hasId).to.be.true;
      // Even if user1 wallet has existed for 5 years on Ethereum, contract returns false because it was just created in contract!
      expect(meetsWalletAge).to.be.false;
      expect(hasEndorsements).to.equal(false);
      expect(score).to.equal(33);
    });
  });
});
