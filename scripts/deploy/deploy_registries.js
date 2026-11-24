const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("==================================================");
  console.log("🚀 Deploying DecentralID Trust Registries (Phase 4)");
  console.log("==================================================");

  const [deployer] = await hre.ethers.getSigners();
  const network = hre.network.name;
  const chainId = (await hre.ethers.provider.getNetwork()).chainId.toString();

  console.log(`Network:   ${network} (Chain ID: ${chainId})`);
  console.log(`Deployer:  ${deployer.address}\n`);

  // 1. Deploy IssuerRegistry
  console.log("📦 Deploying IssuerRegistry...");
  const IssuerRegistry = await hre.ethers.getContractFactory("IssuerRegistry");
  const issuerRegistry = await IssuerRegistry.deploy(deployer.address);
  await issuerRegistry.waitForDeployment();
  const issuerRegistryAddress = await issuerRegistry.getAddress();
  console.log(`✅ IssuerRegistry deployed at: ${issuerRegistryAddress}`);

  // 2. Deploy CredentialRegistry
  console.log("📦 Deploying CredentialRegistry...");
  const CredentialRegistry = await hre.ethers.getContractFactory("CredentialRegistry");
  const credentialRegistry = await CredentialRegistry.deploy(deployer.address, issuerRegistryAddress);
  await credentialRegistry.waitForDeployment();
  const credentialRegistryAddress = await credentialRegistry.getAddress();
  console.log(`✅ CredentialRegistry deployed at: ${credentialRegistryAddress}`);

  // 3. Deploy CredentialStatusRegistry
  console.log("📦 Deploying CredentialStatusRegistry...");
  const CredentialStatusRegistry = await hre.ethers.getContractFactory("CredentialStatusRegistry");
  const credentialStatusRegistry = await CredentialStatusRegistry.deploy(
    deployer.address,
    issuerRegistryAddress,
    credentialRegistryAddress
  );
  await credentialStatusRegistry.waitForDeployment();
  const credentialStatusRegistryAddress = await credentialStatusRegistry.getAddress();
  console.log(`✅ CredentialStatusRegistry deployed at: ${credentialStatusRegistryAddress}`);

  // 4. Save Deployment Manifest
  const manifest = {
    network: network,
    chainId: Number(chainId),
    contracts: {
      IssuerRegistry: issuerRegistryAddress,
      CredentialRegistry: credentialRegistryAddress,
      CredentialStatusRegistry: credentialStatusRegistryAddress,
    },
    deployer: deployer.address,
    deployedAt: new Date().toISOString(),
    blockNumber: await hre.ethers.provider.getBlockNumber(),
  };

  const outputDir = path.join(__dirname, "../../deployments/local");
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const manifestPath = path.join(outputDir, "manifest.json");
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
  console.log(`\n💾 Saved deployment manifest to: ${manifestPath}`);

  // 5. Post-Deployment Verification Smoke Test
  console.log("\n🔍 Running Post-Deployment Smoke Verification...");
  const isGov = await issuerRegistry.hasRole(await issuerRegistry.GOVERNANCE_ROLE(), deployer.address);
  if (!isGov) throw new Error("Smoke check failed: Deployer lacks GOVERNANCE_ROLE on IssuerRegistry");

  const linkedIssuer = await credentialRegistry.issuerRegistry();
  if (linkedIssuer.toLowerCase() !== issuerRegistryAddress.toLowerCase()) {
    throw new Error("Smoke check failed: CredentialRegistry linked to wrong IssuerRegistry");
  }

  const linkedStatusIssuer = await credentialStatusRegistry.issuerRegistry();
  const linkedStatusCred = await credentialStatusRegistry.credentialRegistry();
  if (
    linkedStatusIssuer.toLowerCase() !== issuerRegistryAddress.toLowerCase() ||
    linkedStatusCred.toLowerCase() !== credentialRegistryAddress.toLowerCase()
  ) {
    throw new Error("Smoke check failed: CredentialStatusRegistry link mismatch");
  }

  console.log("✨ All smoke verification checks passed successfully!");
  console.log("==================================================");
}

main()
  .then(() => process.exit(0))
  .catch((err) => {
    console.error("❌ Deployment failed:", err);
    process.exit(1);
  });
