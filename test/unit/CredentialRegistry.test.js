const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("CredentialRegistry Unit Tests (Phase 4)", function () {
  let issuerRegistry;
  let credentialRegistry;
  let admin;
  let institution;
  let operatorKey;
  let unauthorizedUser;

  const sampleCredentialId = ethers.id("credential-diploma-2026-001");
  const sampleCommitment = ethers.id("salted-subject-hash-abcdef1234567890");

  beforeEach(async function () {
    [admin, institution, operatorKey, unauthorizedUser] = await ethers.getSigners();

    // Deploy IssuerRegistry
    const IssuerRegistryFactory = await ethers.getContractFactory("IssuerRegistry");
    issuerRegistry = await IssuerRegistryFactory.deploy(admin.address);
    await issuerRegistry.waitForDeployment();

    // Deploy CredentialRegistry
    const CredentialRegistryFactory = await ethers.getContractFactory("CredentialRegistry");
    credentialRegistry = await CredentialRegistryFactory.deploy(
      admin.address,
      await issuerRegistry.getAddress()
    );
    await credentialRegistry.waitForDeployment();

    // Register institution and delegated operator key
    await issuerRegistry.connect(admin).registerIssuer(institution.address, 3, "uri");
    await issuerRegistry.connect(institution).registerSigningKey(operatorKey.address, 0);
  });

  describe("Credential Registration", function () {
    it("should allow an authorized issuer to register a credential commitment", async function () {
      await expect(
        credentialRegistry.connect(institution).registerCredential(
          sampleCredentialId,
          sampleCommitment,
          institution.address
        )
      )
        .to.emit(credentialRegistry, "CredentialRegistered");

      expect(await credentialRegistry.credentialExists(sampleCredentialId)).to.be.true;

      const [storedCommitment, storedIssuer, issuedAt] =
        await credentialRegistry.getCredential(sampleCredentialId);
      expect(storedCommitment).to.equal(sampleCommitment);
      expect(storedIssuer).to.equal(institution.address);
      expect(issuedAt).to.be.gt(0);
    });

    it("should allow an authorized delegated operational signing key to register a credential", async function () {
      await expect(
        credentialRegistry.connect(operatorKey).registerCredential(
          sampleCredentialId,
          sampleCommitment,
          institution.address
        )
      ).to.emit(credentialRegistry, "CredentialRegistered");

      expect(await credentialRegistry.credentialExists(sampleCredentialId)).to.be.true;
    });

    it("should reject registration by an unauthorized caller", async function () {
      await expect(
        credentialRegistry.connect(unauthorizedUser).registerCredential(
          sampleCredentialId,
          sampleCommitment,
          institution.address
        )
      ).to.be.revertedWithCustomError(credentialRegistry, "UnauthorizedCaller");
    });

    it("should reject duplicate credential registration", async function () {
      await credentialRegistry.connect(institution).registerCredential(
        sampleCredentialId,
        sampleCommitment,
        institution.address
      );

      await expect(
        credentialRegistry.connect(institution).registerCredential(
          sampleCredentialId,
          sampleCommitment,
          institution.address
        )
      ).to.be.revertedWithCustomError(credentialRegistry, "CredentialAlreadyRegistered");
    });

    it("should reject empty commitment or empty credential ID", async function () {
      await expect(
        credentialRegistry.connect(institution).registerCredential(
          ethers.ZeroHash,
          sampleCommitment,
          institution.address
        )
      ).to.be.revertedWithCustomError(credentialRegistry, "EmptyCredentialId");

      await expect(
        credentialRegistry.connect(institution).registerCredential(
          sampleCredentialId,
          ethers.ZeroHash,
          institution.address
        )
      ).to.be.revertedWithCustomError(credentialRegistry, "EmptyCommitment");
    });

    it("should reject registration if the issuing institution is suspended or revoked", async function () {
      await issuerRegistry.connect(admin).suspendIssuer(institution.address);

      await expect(
        credentialRegistry.connect(institution).registerCredential(
          sampleCredentialId,
          sampleCommitment,
          institution.address
        )
      ).to.be.revertedWithCustomError(credentialRegistry, "IssuerNotActive");
    });
  });
});
