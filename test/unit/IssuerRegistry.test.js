const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("IssuerRegistry Unit Tests (Phase 4)", function () {
  let issuerRegistry;
  let admin;
  let institution;
  let operatorKey;
  let unauthorizedUser;

  beforeEach(async function () {
    [admin, institution, operatorKey, unauthorizedUser] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("IssuerRegistry");
    issuerRegistry = await Factory.deploy(admin.address);
    await issuerRegistry.waitForDeployment();
  });

  describe("Initialization & Roles", function () {
    it("should grant DEFAULT_ADMIN_ROLE and GOVERNANCE_ROLE to initial admin", async function () {
      const defaultAdmin = await issuerRegistry.DEFAULT_ADMIN_ROLE();
      const governanceRole = await issuerRegistry.GOVERNANCE_ROLE();
      expect(await issuerRegistry.hasRole(defaultAdmin, admin.address)).to.be.true;
      expect(await issuerRegistry.hasRole(governanceRole, admin.address)).to.be.true;
    });

    it("should revert if initialized with zero address", async function () {
      const Factory = await ethers.getContractFactory("IssuerRegistry");
      await expect(Factory.deploy(ethers.ZeroAddress)).to.be.revertedWithCustomError(
        issuerRegistry,
        "ZeroAddress"
      );
    });
  });

  describe("Issuer Registration & Authorization", function () {
    it("should allow governance to register an institutional issuer", async function () {
      await expect(
        issuerRegistry.connect(admin).registerIssuer(
          institution.address,
          3, // VerifiedInstitution
          "ipfs://bafkreihavardmeta"
        )
      )
        .to.emit(issuerRegistry, "IssuerRegistered")
        .withArgs(institution.address, 3, "ipfs://bafkreihavardmeta")
        .and.to.emit(issuerRegistry, "IssuerAuthorized")
        .and.to.emit(issuerRegistry, "SigningKeyRegistered");

      expect(await issuerRegistry.isIssuerAuthorized(institution.address)).to.be.true;
      const issuerInfo = await issuerRegistry.getIssuer(institution.address);
      expect(issuerInfo.role).to.equal(3);
      expect(issuerInfo.status).to.equal(1); // Active
      expect(issuerInfo.metadataURI).to.equal("ipfs://bafkreihavardmeta");
    });

    it("should reject duplicate issuer registration", async function () {
      await issuerRegistry.connect(admin).registerIssuer(institution.address, 3, "uri1");
      await expect(
        issuerRegistry.connect(admin).registerIssuer(institution.address, 3, "uri2")
      ).to.be.revertedWithCustomError(issuerRegistry, "IssuerAlreadyRegistered");
    });

    it("should reject unauthorized caller registering an issuer", async function () {
      await expect(
        issuerRegistry.connect(unauthorizedUser).registerIssuer(institution.address, 3, "uri")
      ).to.be.reverted;
    });
  });

  describe("Issuer Lifecycle Transitions (Suspension, Reinstatement, Revocation)", function () {
    beforeEach(async function () {
      await issuerRegistry.connect(admin).registerIssuer(institution.address, 3, "uri");
    });

    it("should suspend and reinstate an issuer", async function () {
      await expect(issuerRegistry.connect(admin).suspendIssuer(institution.address))
        .to.emit(issuerRegistry, "IssuerSuspended")
        .withArgs(institution.address);

      expect(await issuerRegistry.isIssuerAuthorized(institution.address)).to.be.false;

      await expect(issuerRegistry.connect(admin).reinstateIssuer(institution.address))
        .to.emit(issuerRegistry, "IssuerReinstated")
        .withArgs(institution.address);

      expect(await issuerRegistry.isIssuerAuthorized(institution.address)).to.be.true;
    });

    it("should permanently revoke an issuer and prevent reactivation", async function () {
      await expect(issuerRegistry.connect(admin).revokeIssuer(institution.address))
        .to.emit(issuerRegistry, "IssuerRevoked")
        .withArgs(institution.address);

      expect(await issuerRegistry.isIssuerAuthorized(institution.address)).to.be.false;

      // Reinstatement must fail
      await expect(
        issuerRegistry.connect(admin).reinstateIssuer(institution.address)
      ).to.be.revertedWithCustomError(issuerRegistry, "IssuerIsRevoked");

      // Authorization update must fail
      await expect(
        issuerRegistry.connect(admin).authorizeIssuer(institution.address, 3)
      ).to.be.revertedWithCustomError(issuerRegistry, "IssuerIsRevoked");
    });
  });

  describe("Signing Key Management & Validation", function () {
    beforeEach(async function () {
      await issuerRegistry.connect(admin).registerIssuer(institution.address, 3, "uri");
    });

    it("should allow an issuer to register an operational signing key", async function () {
      await expect(
        issuerRegistry.connect(institution).registerSigningKey(operatorKey.address, 0)
      )
        .to.emit(issuerRegistry, "SigningKeyRegistered")
        .withArgs(institution.address, operatorKey.address, 0);

      expect(
        await issuerRegistry.isSigningKeyValid(institution.address, operatorKey.address)
      ).to.be.true;
    });

    it("should reject registering zero address as key", async function () {
      await expect(
        issuerRegistry.connect(institution).registerSigningKey(ethers.ZeroAddress, 0)
      ).to.be.revertedWithCustomError(issuerRegistry, "ZeroAddress");
    });

    it("should enforce time-bound signing key expiration", async function () {
      const block = await ethers.provider.getBlock("latest");
      const validUntil = block.timestamp + 100; // valid for 100 seconds

      await issuerRegistry.connect(institution).registerSigningKey(operatorKey.address, validUntil);
      expect(
        await issuerRegistry.isSigningKeyValid(institution.address, operatorKey.address)
      ).to.be.true;

      // Fast-forward time past expiration
      await ethers.provider.send("evm_increaseTime", [150]);
      await ethers.provider.send("evm_mine");

      expect(
        await issuerRegistry.isSigningKeyValid(institution.address, operatorKey.address)
      ).to.be.false;
    });

    it("should allow key revocation by issuer", async function () {
      await issuerRegistry.connect(institution).registerSigningKey(operatorKey.address, 0);
      await expect(issuerRegistry.connect(institution).revokeSigningKey(operatorKey.address))
        .to.emit(issuerRegistry, "SigningKeyRevoked")
        .withArgs(institution.address, operatorKey.address);

      expect(
        await issuerRegistry.isSigningKeyValid(institution.address, operatorKey.address)
      ).to.be.false;
    });

    it("should allow emergency key revocation by governance", async function () {
      await issuerRegistry.connect(institution).registerSigningKey(operatorKey.address, 0);
      await expect(
        issuerRegistry.connect(admin).emergencyRevokeSigningKey(institution.address, operatorKey.address)
      )
        .to.emit(issuerRegistry, "SigningKeyRevoked")
        .withArgs(institution.address, operatorKey.address);

      expect(
        await issuerRegistry.isSigningKeyValid(institution.address, operatorKey.address)
      ).to.be.false;
    });
  });
});
