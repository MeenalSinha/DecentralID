const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Status Transitions Invariant Tests (Phase 4)", function () {
  let issuerRegistry;
  let credentialRegistry;
  let statusRegistry;
  let admin;
  let institution;

  beforeEach(async function () {
    [admin, institution] = await ethers.getSigners();

    const IssuerRegistryFactory = await ethers.getContractFactory("IssuerRegistry");
    issuerRegistry = await IssuerRegistryFactory.deploy(admin.address);

    const CredentialRegistryFactory = await ethers.getContractFactory("CredentialRegistry");
    credentialRegistry = await CredentialRegistryFactory.deploy(
      admin.address,
      await issuerRegistry.getAddress()
    );

    const StatusRegistryFactory = await ethers.getContractFactory("CredentialStatusRegistry");
    statusRegistry = await StatusRegistryFactory.deploy(
      admin.address,
      await issuerRegistry.getAddress(),
      await credentialRegistry.getAddress()
    );

    await issuerRegistry.connect(admin).registerIssuer(institution.address, 3, "uri");
  });

  it("INVARIANT: Revoked credentials can NEVER be reinstated or suspended across multiple attempts", async function () {
    // Generate 5 credentials
    for (let i = 0; i < 5; i++) {
      const credId = ethers.id(`invariant-cred-${i}`);
      const commitment = ethers.id(`commitment-${i}`);

      await credentialRegistry.connect(institution).registerCredential(credId, commitment, institution.address);

      // Randomly either suspend first or directly revoke
      if (i % 2 === 0) {
        await statusRegistry.connect(institution).suspendCredential(credId, "temp suspend");
      }
      // Revoke credential
      await statusRegistry.connect(institution).revokeCredential(credId, "terminal revoke");

      // Verify status is 2 (Revoked)
      const [status] = await statusRegistry.getCredentialStatus(credId);
      expect(status).to.equal(2);

      // Assert invariant holds: No state transition allowed once in terminal Revoked state
      await expect(
        statusRegistry.connect(institution).reinstateCredential(credId, "exploit")
      ).to.be.revertedWithCustomError(statusRegistry, "CredentialAlreadyRevoked");

      await expect(
        statusRegistry.connect(institution).suspendCredential(credId, "exploit")
      ).to.be.revertedWithCustomError(statusRegistry, "CredentialAlreadyRevoked");

      await expect(
        statusRegistry.connect(institution).revokeCredential(credId, "duplicate revoke")
      ).to.be.revertedWithCustomError(statusRegistry, "CredentialAlreadyRevoked");
    }
  });
});
