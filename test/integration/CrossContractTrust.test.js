const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Cross-Contract Trust Integration Tests (Phase 4)", function () {
  let issuerRegistry;
  let credentialRegistry;
  let statusRegistry;
  let platformAdmin;
  let university;
  let departmentKey;
  let verifier;

  const diplomaId = ethers.id("mit-cs-degree-2026-maya-lin");
  const diplomaCommitment = ethers.id("salted-hash-of-degree-claims-and-salt");

  beforeEach(async function () {
    [platformAdmin, university, departmentKey, verifier] = await ethers.getSigners();

    // 1. Deploy all 3 registries
    const IssuerRegistryFactory = await ethers.getContractFactory("IssuerRegistry");
    issuerRegistry = await IssuerRegistryFactory.deploy(platformAdmin.address);

    const CredentialRegistryFactory = await ethers.getContractFactory("CredentialRegistry");
    credentialRegistry = await CredentialRegistryFactory.deploy(
      platformAdmin.address,
      await issuerRegistry.getAddress()
    );

    const StatusRegistryFactory = await ethers.getContractFactory("CredentialStatusRegistry");
    statusRegistry = await StatusRegistryFactory.deploy(
      platformAdmin.address,
      await issuerRegistry.getAddress(),
      await credentialRegistry.getAddress()
    );
  });

  it("Complete End-to-End Workflow: Onboarding -> Key Auth -> Issuance -> Verification -> Revocation", async function () {
    // 1. Platform Admin onboards University
    await issuerRegistry.connect(platformAdmin).registerIssuer(
      university.address,
      3, // VerifiedInstitution
      "ipfs://bafkrei-university-accreditation"
    );
    expect(await issuerRegistry.isIssuerAuthorized(university.address)).to.be.true;

    // 2. University registers Departmental signing key
    await issuerRegistry.connect(university).registerSigningKey(departmentKey.address, 0);
    expect(
      await issuerRegistry.isSigningKeyValid(university.address, departmentKey.address)
    ).to.be.true;

    // 3. Departmental Key issues & registers credential commitment on CredentialRegistry
    await credentialRegistry.connect(departmentKey).registerCredential(
      diplomaId,
      diplomaCommitment,
      university.address
    );
    expect(await credentialRegistry.credentialExists(diplomaId)).to.be.true;

    // 4. Verifier performs complete independent verification
    // - Check 1: Issuer is accredited institution
    expect(await issuerRegistry.isIssuerAuthorized(university.address)).to.be.true;
    // - Check 2: On-chain commitment matches claimed hash
    const [onChainCommitment, onChainIssuer] = await credentialRegistry.getCredential(diplomaId);
    expect(onChainCommitment).to.equal(diplomaCommitment);
    expect(onChainIssuer).to.equal(university.address);
    // - Check 3: Credential status is active
    const [status] = await statusRegistry.getCredentialStatus(diplomaId);
    expect(status).to.equal(0); // Active

    // 5. University revokes the Departmental key (e.g., operator left department)
    await issuerRegistry.connect(university).revokeSigningKey(departmentKey.address);
    expect(
      await issuerRegistry.isSigningKeyValid(university.address, departmentKey.address)
    ).to.be.false;

    // 6. That key can NO LONGER register new credentials
    const newDiplomaId = ethers.id("mit-cs-degree-2026-rogue-entry");
    await expect(
      credentialRegistry.connect(departmentKey).registerCredential(
        newDiplomaId,
        diplomaCommitment,
        university.address
      )
    ).to.be.revertedWithCustomError(credentialRegistry, "UnauthorizedCaller");

    // 7. That key can NO LONGER update status on existing credentials
    await expect(
      statusRegistry.connect(departmentKey).suspendCredential(diplomaId, "attempt")
    ).to.be.revertedWithCustomError(statusRegistry, "UnauthorizedCaller");

    // 8. Platform Admin revokes the entire University
    await issuerRegistry.connect(platformAdmin).revokeIssuer(university.address);
    expect(await issuerRegistry.isIssuerAuthorized(university.address)).to.be.false;

    // 9. University can NO LONGER register any credentials even with university primary key
    await expect(
      credentialRegistry.connect(university).registerCredential(
        newDiplomaId,
        diplomaCommitment,
        university.address
      )
    ).to.be.revertedWithCustomError(credentialRegistry, "IssuerNotActive");
  });
});
