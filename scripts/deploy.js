const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("🚀 Starting deployment...\n");

  // Get deployer account
  const [deployer] = await hre.ethers.getSigners();
  const balance = await hre.ethers.provider.getBalance(deployer.address);

  console.log("📋 Deployment Details:");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log("Network:", hre.network.name);
  console.log("Deployer:", deployer.address);
  console.log("Balance:", hre.ethers.formatEther(balance), "ETH");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

  // Deploy IdentityReputation contract
  console.log("📦 Deploying IdentityReputation contract...");
  const IdentityReputation = await hre.ethers.getContractFactory("IdentityReputation");
  const contract = await IdentityReputation.deploy();

  await contract.waitForDeployment();
  const contractAddress = await contract.getAddress();

  console.log("✅ IdentityReputation deployed to:", contractAddress);

  // Wait for block confirmations
  if (hre.network.name !== "hardhat" && hre.network.name !== "localhost") {
    console.log("\n⏳ Waiting for block confirmations...");
    await contract.deploymentTransaction().wait(6);
    console.log("✅ Confirmed!");
  }

  // Save deployment info
  const deploymentInfo = {
    network: hre.network.name,
    contractAddress: contractAddress,
    deployer: deployer.address,
    deployedAt: new Date().toISOString(),
    blockNumber: await hre.ethers.provider.getBlockNumber(),
    chainId: (await hre.ethers.provider.getNetwork()).chainId.toString()
  };

  // Create deployments directory if it doesn't exist
  const deploymentsDir = path.join(__dirname, "../deployments");
  if (!fs.existsSync(deploymentsDir)) {
    fs.mkdirSync(deploymentsDir);
  }

  // Save deployment info to file
  const deploymentFile = path.join(
    deploymentsDir,
    `${hre.network.name}-deployment.json`
  );
  fs.writeFileSync(
    deploymentFile,
    JSON.stringify(deploymentInfo, null, 2)
  );

  console.log("\n💾 Deployment info saved to:", deploymentFile);

  // Copy ABI to frontend
  const artifactPath = path.join(
    __dirname,
    "../artifacts/contracts/IdentityReputation.sol/IdentityReputation.json"
  );
  const frontendAbiDir = path.join(__dirname, "../frontend/src/abi");
  
  if (!fs.existsSync(frontendAbiDir)) {
    fs.mkdirSync(frontendAbiDir, { recursive: true });
  }

  const frontendAbiPath = path.join(frontendAbiDir, "IdentityReputation.json");
  
  if (fs.existsSync(artifactPath)) {
    const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
    fs.writeFileSync(
      frontendAbiPath,
      JSON.stringify(artifact, null, 2)
    );
    console.log("📋 ABI copied to frontend/src/abi/");
  }

  // Verify on Etherscan (if not local network)
  if (hre.network.name !== "hardhat" && hre.network.name !== "localhost") {
    console.log("\n🔍 Verifying contract on Etherscan...");
    try {
      await hre.run("verify:verify", {
        address: contractAddress,
        constructorArguments: [],
      });
      console.log("✅ Contract verified on Etherscan!");
    } catch (error) {
      console.log("⚠️  Verification failed:", error.message);
      console.log("You can verify manually later with:");
      console.log(`npx hardhat verify --network ${hre.network.name} ${contractAddress}`);
    }
  }

  // Print summary
  console.log("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log("🎉 Deployment Complete!");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log("\n📝 Next Steps:");
  console.log("1. Update frontend CONTRACT_ADDRESS to:", contractAddress);
  console.log("2. Update .env with contract address");
  console.log("3. Test the dApp with MetaMask\n");

  // Print usage example
  console.log("🔧 Contract Interaction Examples:");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log("// Create identity");
  console.log(`await contract.createIdentity("QmYourIPFSHash");`);
  console.log("\n// Get identity");
  console.log(`await contract.getIdentity("0xAddress");`);
  console.log("\n// Update reputation");
  console.log(`await contract.updateReputation("0xAddress", 5);`);
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:");
    console.error(error);
    process.exit(1);
  });