const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("CredentialStatusRegistry Unit Tests (Phase 4)", function () {
  let issuerRegistry;
  let credentialRegistry;
  let statusRegistry;
  let admin;
  let institution;
  let operatorKey;
  let unauthorizedUser;

  const sampleCredentialId = ethers.id("credential-diploma-2026-status-test");
  const sampleCommitment = ethers.id("salted-commitment-12345");

  beforeEach(async function () {
    [admin, institution, operatorKey, unauthorizedUser] = await ethers.getSigners();

    // 1. Deploy IssuerRegistry
    const IssuerRegistryFactory = await ethers.getContractFactory("IssuerRegistry");
    issuerRegistry = await IssuerRegistryFactory.deploy(admin.address);

    // 2. Deploy CredentialRegistry
    const CredentialRegistryFactory = await ethers.getContractFactory("CredentialRegistry");
    credentialRegistry = await CredentialRegistryFactory.deploy(
      admin.address,
      await issuerRegistry.getAddress()
    );

    // 3. Deploy CredentialStatusRegistry
    const StatusRegistryFactory = await ethers.getContractFactory("CredentialStatusRegistry");
    statusRegistry = await StatusRegistryFactory.deploy(
      admin.address,
      await issuerRegistry.getAddress(),
      await credentialRegistry.getAddress()
    );

    // Setup: Authorize institution and operational signing key
    await issuerRegistry.connect(admin).registerIssuer(institution.address, 3, "uri");
    await issuerRegistry.connect(institution).registerSigningKey(operatorKey.address, 0);

    // Register credential
    await credentialRegistry.connect(institution).registerCredential(
      sampleCredentialId,
      sampleCommitment,
      institution.address
    );
  });

  describe("Lifecycle Status Transitions", function () {
    it("should default to Active (0) for registered credentials", async function () {
      const [status, updatedAt] = await statusRegistry.getCredentialStatus(sampleCredentialId);
      expect(status).to.equal(0); // Active
      expect(updatedAt).to.equal(0);
    });

    it("should allow an authorized issuer operational key to suspend and reinstate a credential", async function () {
      // Suspend
      await expect(
        statusRegistry.connect(operatorKey).suspendCredential(sampleCredentialId, "Temporary academic review")
      )
        .to.emit(statusRegistry, "CredentialStatusChanged")
        .withArgs(sampleCredentialId, 0, 1, operatorKey.address, "Temporary academic review");

      const [statusSuspended] = await statusRegistry.getCredentialStatus(sampleCredentialId);
      expect(statusSuspended).to.equal(1); // Suspended

      // Reinstate
      await expect(
        statusRegistry.connect(operatorKey).reinstateCredential(sampleCredentialId, "Review concluded in good standing")
      )
        .to.emit(statusRegistry, "CredentialStatusChanged")
        .withArgs(sampleCredentialId, 1, 0, operatorKey.address, "Review concluded in good standing");

      const [statusReinstated] = await statusRegistry.getCredentialStatus(sampleCredentialId);
      expect(statusReinstated).to.equal(0); // Active
    });

    it("should allow permanent revocation and reject reactivation (Irreversible State Machine)", async function () {
      await expect(
        statusRegistry.connect(institution).revokeCredential(sampleCredentialId, "Diploma rescinded for academic misconduct")
      )
        .to.emit(statusRegistry, "CredentialStatusChanged")
        .withArgs(sampleCredentialId, 0, 2, institution.address, "Diploma rescinded for academic misconduct");

      const [statusRevoked] = await statusRegistry.getCredentialStatus(sampleCredentialId);
      expect(statusRevoked).to.equal(2); // Revoked

      // Attempting to reinstate MUST revert
      await expect(
        statusRegistry.connect(institution).reinstateCredential(sampleCredentialId, "Attempt reinstatement")
      ).to.be.revertedWithCustomError(statusRegistry, "CredentialAlreadyRevoked");

      // Attempting to suspend MUST revert
      await expect(
        statusRegistry.connect(institution).suspendCredential(sampleCredentialId, "Attempt suspension")
      ).to.be.revertedWithCustomError(statusRegistry, "CredentialAlreadyRevoked");
    });

    it("should reject status updates from unauthorized callers", async function () {
      await expect(
        statusRegistry.connect(unauthorizedUser).suspendCredential(sampleCredentialId, "Malicious suspend")
      ).to.be.revertedWithCustomError(statusRegistry, "UnauthorizedCaller");
    });

    it("should reject status updates for non-existent credentials", async function () {
      const nonExistentId = ethers.id("non-existent-credential");
      await expect(
        statusRegistry.connect(institution).suspendCredential(nonExistentId, "test")
      ).to.be.revertedWithCustomError(statusRegistry, "CredentialNotFound");
    });

    it("should revert getCredentialStatus with CredentialNotFound for non-existent credentials", async function () {
      const nonExistentId = ethers.id("random-unregistered-credential-id");
      await expect(
        statusRegistry.getCredentialStatus(nonExistentId)
      ).to.be.revertedWithCustomError(statusRegistry, "CredentialNotFound");
    });

    it("should reject status reason strings exceeding 128 bytes to prevent PII and gas griefing", async function () {
      const longReason = "A".repeat(129);
      await expect(
        statusRegistry.connect(institution).suspendCredential(sampleCredentialId, longReason)
      ).to.be.revertedWithCustomError(statusRegistry, "ReasonTooLong");

      await expect(
        statusRegistry.connect(institution).revokeCredential(sampleCredentialId, longReason)
      ).to.be.revertedWithCustomError(statusRegistry, "ReasonTooLong");
    });

    it("should permit emergency revocation during pause while blocking non-critical transitions", async function () {
      // Pause registry
      await statusRegistry.connect(admin).pause();

      // Suspend must be blocked
      await expect(
        statusRegistry.connect(institution).suspendCredential(sampleCredentialId, "suspension attempt")
      ).to.be.revertedWithCustomError(statusRegistry, "EnforcedPause");

      // Emergency revocation must SUCCEED even when paused
      await expect(
        statusRegistry.connect(institution).revokeCredential(sampleCredentialId, "Emergency pause revocation")
      )
        .to.emit(statusRegistry, "CredentialStatusChanged")
        .withArgs(sampleCredentialId, 0, 2, institution.address, "Emergency pause revocation");

      const [statusRevoked] = await statusRegistry.getCredentialStatus(sampleCredentialId);
      expect(statusRevoked).to.equal(2);
    });
  });
});
