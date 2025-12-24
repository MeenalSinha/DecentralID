# 🔐 DecentralID - Decentralized Identity & Reputation System

A blockchain-powered identity and reputation system where users control their credentials with verifiable cryptographic proofs on Ethereum. Profile data is stored on IPFS, while verification and reputation scores are immutably recorded on-chain.

![Ethereum](https://img.shields.io/badge/Ethereum-3C3C3D?style=flat&logo=ethereum&logoColor=white)
![Solidity](https://img.shields.io/badge/Solidity-363636?style=flat&logo=solidity&logoColor=white)
![IPFS](https://img.shields.io/badge/IPFS-65C2CB?style=flat&logo=ipfs&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB)

## 🎯 Problem Statement

Traditional identity and reputation systems suffer from:
- **Vendor Lock-In**: Users don't own their professional credentials
- **Lack of Trust**: No verifiable proof of skills and work history
- **Centralized Control**: Single points of failure and censorship
- **Data Privacy**: Sensitive information stored with third parties

## 💡 Our Solution

DecentralID combines **Ethereum smart contracts** with **IPFS storage** to create a trustless, decentralized identity system:

- ✅ **User-Controlled Data**: You own your credentials, stored on IPFS
- ✅ **Blockchain Verification**: Cryptographic proofs on Ethereum
- ✅ **Reputation System**: Build trust through on-chain endorsements
- ✅ **Privacy-First**: Sensitive data off-chain, only hashes on-chain
- ✅ **Interoperable**: Use your identity across multiple platforms

## 🏗️ Architecture

```
┌─────────────────┐
│   React dApp    │ ← User Interface (Web3 Integration)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Ethereum L1/L2  │ ← Smart Contract (Verification + Reputation)
│  Smart Contract │    - Stores IPFS hashes
└────────┬────────┘    - Records reputation scores
         │              - Emits events
         │
         ↓
┌─────────────────┐
│      IPFS       │ ← Decentralized Storage (Profile Data)
│   (Pinata/Web3  │    - Name, bio, skills, education
│    Storage)     │    - Portfolio links
└─────────────────┘    - Encrypted documents (future)
```

**Key Design Principle**: Sensitive data lives on IPFS, verification lives on-chain.

## 🚀 Features

### Core Features
- 🔗 **MetaMask Integration**: Connect with industry-standard Web3 wallet
- 📝 **Create Decentralized Identity**: Blockchain-verified profiles
- ⭐ **Reputation System**: 5-star endorsements recorded on-chain
- 🔍 **View Profiles**: Browse and verify other users' credentials
- 📊 **Reputation Badges**: Elite, Trusted, Verified, New

### Technical Features
- 📦 **IPFS Storage**: Off-chain data storage via Pinata
- ⛓️ **Smart Contract Events**: Real-time updates via event logs
- 🔐 **Cryptographic Verification**: Immutable identity proofs
- 🌐 **Multi-Network Support**: Sepolia, Mumbai, Mainnet
- 💾 **ABI Auto-Export**: Contract interface for frontend

## 🛠️ Tech Stack

### Blockchain Layer
- **Solidity ^0.8.19**: Smart contract language
- **Hardhat**: Development environment
- **Ethers.js v6**: Blockchain interaction library
- **OpenZeppelin**: Security-audited contract templates

### Frontend Layer
- **React 18**: UI framework
- **Tailwind CSS**: Styling
- **Lucide Icons**: Icon library
- **Web3 Modal**: Wallet connection

### Storage Layer
- **IPFS**: Decentralized file storage
- **Pinata**: IPFS pinning service
- **Web3.Storage**: Alternative IPFS gateway

## 📦 Installation

### Prerequisites
```bash
node >= 16.0.0
npm >= 7.0.0
MetaMask browser extension
```

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/decentralized-identity-reputation.git
cd decentralized-identity-reputation
```

### 2. Install Dependencies
```bash
# Install root dependencies
npm install

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 3. Configure Environment
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your keys
nano .env
```

Required variables:
```bash
PRIVATE_KEY=your_wallet_private_key
SEPOLIA_RPC_URL=your_rpc_url
PINATA_API_KEY=your_pinata_key
PINATA_SECRET_API_KEY=your_pinata_secret
ETHERSCAN_API_KEY=your_etherscan_key
```

### 4. Compile Contracts
```bash
npx hardhat compile
```

### 5. Deploy to Sepolia
```bash
# Get testnet ETH from https://sepoliafaucet.com
npx hardhat run scripts/deploy.js --network sepolia
```

### 6. Update Frontend Config
```javascript
// frontend/src/App.jsx
const CONTRACT_ADDRESS = '0xYourDeployedContractAddress';
```

### 7. Run Frontend
```bash
cd frontend
npm run dev
```

## 📁 Project Structure

```
decentralized-identity-reputation/
│
├── contracts/
│   └── IdentityReputation.sol      # Main smart contract
│
├── scripts/
│   └── deploy.js                   # Deployment script
│
├── deployments/
│   └── sepolia-deployment.json     # Deployment records
│
├── frontend/
│   ├── src/
│   │   ├── abi/
│   │   │   └── IdentityReputation.json
│   │   ├── components/
│   │   │   ├── ConnectWallet.jsx
│   │   │   ├── CreateIdentity.jsx
│   │   │   └── ViewProfile.jsx
│   │   ├── hooks/
│   │   │   └── useEthereum.js
│   │   ├── utils/
│   │   │   ├── contract.js
│   │   │   └── ipfs.js
│   │   └── App.jsx
│   │
│   └── package.json
│
├── hardhat.config.js               # Hardhat configuration
├── .env.example                    # Environment template
├── .gitignore
├── package.json
└── README.md
```

## 🔧 Smart Contract API

### Create Identity
```solidity
function createIdentity(string memory ipfsHash) public
```
Creates a new decentralized identity with IPFS hash.

### Get Identity
```solidity
function getIdentity(address user) public view returns (
    string memory ipfsHash,
    uint256 reputation,
    uint256 createdAt,
    bool exists
)
```
Retrieves identity details for a given address.

### Update Reputation
```solidity
function updateReputation(address user, uint256 points) public
```
Adds reputation points to a user (1-10 points, max 100 total).

### Check Identity Exists
```solidity
function hasIdentity(address user) public view returns (bool)
```
Checks if an address has created an identity.

## 🧪 Testing

### Run Unit Tests
```bash
npx hardhat test
```

### Run Coverage
```bash
npx hardhat coverage
```

### Gas Reporter
```bash
REPORT_GAS=true npx hardhat test
```

## 🌐 Deployment

### Sepolia Testnet (Recommended)
```bash
npx hardhat run scripts/deploy.js --network sepolia
```

### Mumbai Testnet (Polygon)
```bash
npx hardhat run scripts/deploy.js --network mumbai
```

### Mainnet (Production)
```bash
npx hardhat run scripts/deploy.js --network mainnet
```

### Verify on Etherscan
```bash
npx hardhat verify --network sepolia YOUR_CONTRACT_ADDRESS
```

## 🎨 Frontend Usage

### 1. Connect Wallet
Click "Connect MetaMask" to connect your wallet.

### 2. Create Identity
Fill in your profile details:
- Name
- Bio
- Skills (comma-separated)
- Education
- Portfolio URL

Click "Create Identity on Blockchain" to submit.

### 3. View Profile
After creation, view your profile with:
- Reputation score (0-100)
- Badge level (New → Verified → Trusted → Elite)
- IPFS hash reference
- All profile details

### 4. Endorse Others
Rate other users with 1-5 stars to update their on-chain reputation.

## 🔒 Security Considerations

### For Hackathons
- ✅ Use Sepolia testnet only
- ✅ Never use real funds
- ✅ Test wallets with no mainnet value
- ✅ Pinata free tier is sufficient

### For Production
- 🔐 Multi-sig wallet for contract ownership
- 🔐 Formal security audit required
- 🔐 Rate limiting on endorsements
- 🔐 Encrypted IPFS data for sensitive info
- 🔐 Backend proxy for API keys

## 🚦 Roadmap

### Phase 1 (Current)
- [x] Basic identity creation
- [x] IPFS integration
- [x] Reputation system
- [x] MetaMask connection

### Phase 2 (Next)
- [ ] Verifiable credentials (W3C standard)
- [ ] Multi-signature endorsements
- [ ] Encrypted document storage
- [ ] ENS integration

### Phase 3 (Future)
- [ ] Cross-chain identity
- [ ] OAuth-style identity provider
- [ ] Mobile app (React Native)
- [ ] DAO governance

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ethereum Foundation**: For blockchain infrastructure
- **IPFS/Protocol Labs**: For decentralized storage
- **OpenZeppelin**: For secure smart contract templates
- **Hardhat**: For excellent development tools

## 📞 Contact

**Project Maintainer**: Your Name
- GitHub: [@yourusername](https://github.com/yourusername)
- Twitter: [@yourhandle](https://twitter.com/yourhandle)
- Email: your.email@example.com

**Project Link**: [https://github.com/yourusername/decentralized-identity-reputation](https://github.com/yourusername/decentralized-identity-reputation)

---

<div align="center">
  <strong>Built with ❤️ for a decentralized future</strong>
  <br />
  <sub>Powered by Ethereum, IPFS, and Web3</sub>
</div>